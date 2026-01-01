import os
import json
import uuid
from typing import List, Optional
from glob import glob
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Evaluador de Talento IA - Core Engine")

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data") if os.path.exists(os.path.join(BASE_DIR, "data")) else "app/data"

if os.getenv("DOCKER_ENV"):
     DATA_DIR = "/app/data"

# Ensure Data Directory Exists
os.makedirs(DATA_DIR, exist_ok=True)

# Helper to get file paths based on ID
def get_file_paths(eval_id: str):
    return {
        "eval": os.path.join(DATA_DIR, f"eval_{eval_id}.json"),
        "transcript": os.path.join(DATA_DIR, f"transcript_{eval_id}.txt")
    }

# LLM Factory
def get_llm_model():
    """
    Factory function to initialize the LLM based on environment variables.
    Supports easy swapping of providers (e.g., OpenAI, Azure, Anthropic).
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model_name = os.getenv("LLM_MODEL", "gpt-4o")
    
    if provider == "openai":
        return ChatOpenAI(model=model_name, temperature=0)
    # Future providers can be added here:
    # elif provider == "anthropic":
    #     return ChatAnthropic(model=model_name, temperature=0)
    else:
        # Default to OpenAI if unknown
        return ChatOpenAI(model="gpt-4o", temperature=0)

llm = get_llm_model()

# --- MODULE 1: CV ANALYSIS ENGINE ---

class AnalysisResult(BaseModel):
    candidate_name: str = Field(description="Nombre completo del candidato (Explicitamente proporcionado).")
    dni: str = Field(description="DNI del candidato.")
    matching_requirements: List[str] = Field(description="Lista de requisitos cumplidos.")
    unmatching_requirements: List[str] = Field(description="Lista de requisitos NO cumplidos.")
    not_found_requirements: List[str] = Field(description="Lista de requisitos NO mencionados en el CV.")
    score: float = Field(description="Puntuación de 0 a 100.")
    discarded: bool = Field(description="True si se incumple un requisito obligatorio que NO es 'not_found'.")
    total_requirements: int = Field(description="Número total de requisitos identificados.")

class AnalyzeRequest(BaseModel):
    cv_text: str
    offer_text: str
    first_name: str
    last_name: str
    dni: str

@app.post("/analyze")
async def analyze_cv(request: AnalyzeRequest):
    parser = JsonOutputParser(pydantic_object=AnalysisResult)
    
    # Explicit Name Construction
    full_name = f"{request.first_name} {request.last_name}"
    
    # System Prompt for Phase 1
    system_prompt = """
Eres un Experto en Reclutamiento Técnico (Motor de Análisis Core). Tu objetivo es comparar una Oferta de Empleo con un CV y extraer un análisis estructurado.

REGLAS CRÍTICAS:
1. Identificación de Requisitos: Separa la oferta en unidades individuales.
2. Clasificación:
    - `matching`: Cumple explícitamente.
    - `unmatching`: No cumple explícitamente (ej. pide 5 años y tiene 1).
    - `not_found`: No se menciona en el CV.
3. Lógica de Descarte (Fase 1):
    - Si un requisito OBLIGATORIO es `unmatching` (no cumple), `discarded` = true.
    - Si un requisito OBLIGATORIO es `not_found` (no mencionado), `discarded` = false (se preguntará en la entrevista).
4. Cálculo de Score: (Requisitos cumplidos / Total requisitos) * 100.
    - Los `not_found` cuentan como 0 para el score por ahora.
"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"OFERTA:\n{request.offer_text}\n\nCV:\n{request.cv_text}\n\n{parser.get_format_instructions()}")
    ]
    
    try:
        response = llm.invoke(messages)
        result = parser.parse(response.content)
        
        # Override/Inject Explicit Identity Data
        result["candidate_name"] = full_name
        result["dni"] = request.dni
        
        # Generate Unique ID
        eval_id = str(uuid.uuid4())
        paths = get_file_paths(eval_id)
        
        # Save Initial Evaluation
        with open(paths['eval'], "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4)
            
        # Return result with ID
        result["evaluation_id"] = eval_id
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- MODULE 2: INTERVIEW AGENT ---

class ChatRequest(BaseModel):
    evaluation_id: str
    message: str
    history: List[dict]

class StartInterviewRequest(BaseModel):
    evaluation_id: str

class ChatResponse(BaseModel):
    response: str
    history: List[dict]

@app.post("/interview", response_model=ChatResponse)
async def conduct_interview(request: ChatRequest):
    # Load context specific to this ID
    paths = get_file_paths(request.evaluation_id)
    if not os.path.exists(paths['eval']):
         raise HTTPException(status_code=404, detail="Evaluation ID not found")

    with open(paths['eval'], "r", encoding="utf-8") as f:
        eval_data = json.load(f)
        
    missing = eval_data.get("not_found_requirements", [])
    candidate_name = eval_data.get("candidate_name", "Candidato")

    system_prompt = f"""
Eres el "Asistente Virtual de Evaluación Técnica". Tu tono es profesional, neutral y eficiente.
Tu objetivo es verificar ÚNICAMENTE los requisitos que aparecen en la lista de 'No Encontrados'.

INSTRUCCIONES CLAVE:
1. Pregunta UNO POR UNO. No agrupes preguntas.
2. Inicia saludando a {candidate_name} y mencionando que necesitas corroborar algunos puntos.
3. Si la lista de 'No Encontrados' está vacía ({missing}), procede al cierre indicando que tienes toda la información.
4. NO preguntes sobre requisitos ya cumplidos.
5. Sé breve y directo.
"""
    
    # Update Transcript
    with open(paths['transcript'], "a", encoding="utf-8") as f:
        f.write(f"Candidato: {request.message}\n")

    # Build LangChain Messages
    messages = [SystemMessage(content=system_prompt)]
    for msg in request.history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=request.message))
    
    response = llm.invoke(messages)
    ai_response = response.content

    # Save Agent Response to Transcript
    with open(paths['transcript'], "a", encoding="utf-8") as f:
        f.write(f"Evaluador: {ai_response}\n")

    new_history = request.history + [
        {"role": "user", "content": request.message},
        {"role": "assistant", "content": ai_response}
    ]

    return ChatResponse(response=ai_response, history=new_history)

@app.post("/interview/start", response_model=ChatResponse)
async def start_interview(request: StartInterviewRequest):
    """Proactively starts the interview."""
    paths = get_file_paths(request.evaluation_id)
    if not os.path.exists(paths['eval']):
         raise HTTPException(status_code=404, detail="Evaluation ID not found")
         
    # Init transcript
    with open(paths['transcript'], "w", encoding="utf-8") as f:
        f.write("--- INICIO ENTREVISTA ---\n")

    with open(paths['eval'], "r", encoding="utf-8") as f:
        eval_data = json.load(f)
        
    missing = eval_data.get("not_found_requirements", [])
    candidate_name = eval_data.get("candidate_name", "Candidato")

    system_prompt = f"""
Eres el "Asistente Virtual de Evaluación Técnica".
Tu tarea: Dar la bienvenida a {candidate_name} y hacer la PRIMERA pregunta sobre la lista de requisitos no encontrados: {missing}.
Si no hay requisitos faltantes, simplemente saluda y di que el perfil es completo.
MANTÉN EL TONO PROFESIONAL.
"""
    messages = [SystemMessage(content=system_prompt)]
    response = llm.invoke(messages)
    ai_response = response.content
    
    with open(paths['transcript'], "a", encoding="utf-8") as f:
        f.write(f"Evaluador: {ai_response}\n")

    initial_history = [{"role": "assistant", "content": ai_response}]
    return ChatResponse(response=ai_response, history=initial_history)



# --- MODULE 3: AUDIT AGENT (STRUCTURED OUTPUT) ---

class AuditResult(BaseModel):
    evaluation: AnalysisResult
    key_points: List[str] = Field(description="Resumen de puntos clave mencionados en la entrevista.")
    red_flags: List[str] = Field(description="Señales de alerta detectadas (ej: contradicciones, respuestas vagas, falta de conocimiento básico). Si no hay, dejar vacío.")

class AuditRequest(BaseModel):
    evaluation_id: str

@app.post("/audit")
async def audit_interview(request: AuditRequest):
    paths = get_file_paths(request.evaluation_id)
    if not os.path.exists(paths['eval']) or not os.path.exists(paths['transcript']):
         raise HTTPException(status_code=404, detail="Data not found for this ID")

    with open(paths['eval'], "r", encoding="utf-8") as f:
        initial_eval_data = json.load(f)
    
    with open(paths['transcript'], "r", encoding="utf-8") as f:
        transcript = f.read()

    parser = JsonOutputParser(pydantic_object=AuditResult)
    
    # Prompt
    system_prompt = f"""
Actúa como un Auditor de Datos del Sistema Core. Recibirás el análisis inicial del CV y la transcripción de la entrevista. Tu tarea es generar el objeto JSON final actualizado y un resumen.

PROCEDIMIENTO:
1. Analiza las respuestas del candidato en la entrevista sobre los `not_found_requirements`.
2. Si el candidato confirma tener la experiencia requerida, mueve el requisito a `matching_requirements`.
3. Si el candidato confirma NO tener la experiencia:
    - Muévelo a `unmatching_requirements`.
    - Si ese requisito era OBLIGATORIO, establece `discarded` = true.
4. DETECCIÓN DE RED FLAGS:
    - Identifica contradicciones directas entre CV y respuestas.
    - Respuestas excesivamente cortas o vagas ("sí, sé de eso" sin detalles).
    - Falta de conocimiento en conceptos básicos de los requisitos que dice tener.
5. Recalcula el score final (Cumplidos / Totales * 100).
6. Genera `key_points` y `red_flags`.

JSON INICIAL:
{json.dumps(initial_eval_data)}

TRANSCRIPCIÓN:
{transcript}

{parser.get_format_instructions()}
"""
    
    messages = [SystemMessage(content=system_prompt)]
    try:
        response = llm.invoke(messages)
        result = parser.parse(response.content)
        
        # Save Final Evaluation (Overwrite initial to be main record)
        result["evaluation"]["candidate_name"] = initial_eval_data.get("candidate_name", "Unknown") # preserve name
        
        # Merge audit fields into the main json for persistence too? 
        # Ideally we save the whole structure. Let's start saving the whole AuditResult structure OR merge.
        # To keep it compatible with AnalysisResult reads elsewhere, we'll save fields into the main dict.
        final_data = result["evaluation"]
        final_data["key_points"] = result.get("key_points", [])
        final_data["red_flags"] = result.get("red_flags", [])
        
        with open(paths['eval'], "w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=4)
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- MODULE 4: EVALUATOR PANEL ----

@app.get("/evaluations")
async def get_all_evaluations():
    """List all evaluations for the dashboard."""
    files = glob(os.path.join(DATA_DIR, "eval_*.json"))
    results = []
    
    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            results.append({
                "id": os.path.basename(file).replace("eval_", "").replace(".json", ""),
                "candidate_name": data.get("candidate_name", "Unknown"),
                "score": data.get("score", 0),
                "discarded": data.get("discarded", False),
                "total_requirements": data.get("total_requirements", 0),
                "timestamp": datetime.fromtimestamp(os.path.getmtime(file)).strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception:
            continue
            
    # Sort by date desc
    results.sort(key=lambda x: x["timestamp"], reverse=True)
    return results

@app.get("/evaluations/{evaluation_id}")
async def get_evaluation_detail(evaluation_id: str):
    """Get full details for a specific evaluation."""
    paths = get_file_paths(evaluation_id)
    
    if not os.path.exists(paths['eval']):
        raise HTTPException(status_code=404, detail="Evaluation not found")
        
    with open(paths['eval'], "r", encoding="utf-8") as f:
        eval_data = json.load(f)
        
    transcript = ""
    if os.path.exists(paths['transcript']):
        with open(paths['transcript'], "r", encoding="utf-8") as f:
            transcript = f.read()
            
    return {
        "evaluation": eval_data,
        "transcript": transcript
    }
