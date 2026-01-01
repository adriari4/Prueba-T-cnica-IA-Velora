import streamlit as st
import requests
import os
import pandas as pd
import time

# Frontend para Sistema de Evaluación por IA - Sistema Unificado

st.set_page_config(page_title="Sistema de Evaluación por IA", layout="wide", page_icon="⚡")

# --- BRANDING DE VELORA E INYECCIÓN DE UI MODERNA ---
# Colores aproximados del branding de Velora:
# Cian/Verde azulado: #00C4CC
# Azul Oscuro: #005F9E
# Texto: #1f2937 (Gris Oscuro/Negro)
# Fondo: Blanco/Gris Claro

st.markdown("""
    <style>
        /* Importar Fuente Google */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            color: #000000;
            font-weight: 500;
        }

        /* Ocultar Branding de Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stDecoration"] {visibility: hidden;} /* Oculta la decoración arcoíris */
        
        /* Fondo de la App */
        .stApp {
            background-color: #ffffff;
        }

        /* Tarjetas Personalizadas */
        .metric-card {
            background-color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            margin-bottom: 20px;
            border: 1px solid #e5e7eb;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 800;
            color: #000000;
        }
        .metric-label {
            font-size: 0.875rem;
            color: #374151;
            font-weight: 600;
        }

        /* Insignias de Estado */
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 600;
        }
        .status-viable {
            background-color: #d1fae5;
            color: #065f46;
        }
        .status-discarded {
            background-color: #fee2e2;
            color: #991b1b;
        }

        /* Botones con tema Velora */
        .stButton button {
            background: linear-gradient(90deg, #00C4CC 0%, #005F9E 100%);
            color: white;
            border-radius: 8px;
            font-weight: 600;
            border: none;
            padding: 0.6rem 1.2rem;
            transition: all 0.2s;
        }
        .stButton button:hover {
            opacity: 0.9;
            box-shadow: 0 4px 12px rgba(0, 196, 204, 0.3);
        }

        /* Estilo del Chat */
        .stChatMessage {
            background-color: white;
            border-radius: 12px;
            padding: 15px;
            border: 1px solid #f3f4f6;
        }
        
        /* Estilo de Pestañas */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        /* Force Input Fields to be White with Black Text */
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
            background-color: #ffffff !important;
            color: #000000 !important;
            border-color: #d1d5db !important;
        }
        /* Fix for Streamlit's dark mode defaults if active */
        [data-baseweb="base-input"] {
            background-color: #ffffff !important;
            border: 1px solid #d1d5db !important;
        }

        /* Executive Summary Text Enhancement */
        .stMarkdown p, .stMarkdown li {
            font-size: 1.1rem !important;
            color: #000000 !important;
            font-weight: 500 !important;
        }

        /* Tab Visibility */
        .stTabs [aria-selected="true"] {
            background-color: transparent;
            border-bottom: 3px solid #00C4CC;
            color: #005F9E !important;
            font-weight: 800 !important;
        }
    </style>
""", unsafe_allow_html=True)

# Cabecera con Logo (diseño simulado)
col_head1, col_head2 = st.columns([1, 4])
with col_head1:
    # Usar logo si existe, si no texto
    logo_path = "evaluador-tecnico/assets/logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=150)
    else:
        st.markdown("## VELORA")

with col_head2:
    st.markdown("<h2 style='text-align: right; color: #005F9E;'>Sistema de Evaluación por IA</h2>", unsafe_allow_html=True)

st.markdown("---")

# Backend URL configuration
BACKEND_HOST = os.getenv("BACKEND_URL", "http://localhost:8000")
    
ANALYZE_URL = f"{BACKEND_HOST}/analyze"
INTERVIEW_URL = f"{BACKEND_HOST}/interview"
START_INTERVIEW_URL = f"{BACKEND_HOST}/interview/start"
AUDIT_URL = f"{BACKEND_HOST}/audit"
EVALUATIONS_URL = f"{BACKEND_HOST}/evaluations"

# Inicializar Session State
if "current_eval_id" not in st.session_state:
    st.session_state.current_eval_id = None
if "step" not in st.session_state:
    st.session_state.step = "INPUT" # INPUT, RESULTS, INTERVIEW, FINISHED
if "messages" not in st.session_state:
    st.session_state.messages = []
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

# PESTAÑAS
tab1, tab2 = st.tabs(["Portal del Candidato", "Panel del Evaluador"])

with tab1:
    # --- FLUJO DEL CANDIDATO ---
    
    if st.session_state.step == "INPUT":
        st.markdown("### 👋 Hola, bienvenido")
        st.write("Por favor, introduce tu nombre, DNI y los datos requeridos para comenzar la evaluación técnica.")
        
        # Entradas de Identidad
        c_name, c_last, c_dni = st.columns(3)
        with c_name:
            first_name = st.text_input("Nombre", key="input_name", placeholder="Ej: Pedro")
        with c_last:
            last_name = st.text_input("Apellidos", key="input_lastname", placeholder="Ej: Pascal")
        with c_dni:
            dni = st.text_input("DNI", key="input_dni", placeholder="Ej: 12345678Z")

        # Entradas Técnicas
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📄 Oferta de Empleo")
            offer_text = st.text_area("Oferta", height=200, label_visibility="collapsed", placeholder="Pegue la descripción del puesto aquí...")
        with col2:
            st.markdown("#### 👤 CV del Candidato")
            cv_text = st.text_area("CV", height=200, label_visibility="collapsed", placeholder="Pegue su Curriculum Vitae aquí...")
            
        if st.button("Ejecutar Análisis", type="primary", use_container_width=True):
            if not first_name or not last_name or not dni or not offer_text or not cv_text:
                st.warning("⚠️ Por favor completa TODOS los campos obligatorios (Identificación + Oferta + CV).")
            else:
                with st.spinner(f"Analizando perfil de {first_name}..."):
                    try:
                        resp = requests.post(ANALYZE_URL, json={
                            "first_name": first_name,
                            "last_name": last_name,
                            "dni": dni,
                            "cv_text": cv_text, 
                            "offer_text": offer_text
                        })
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.analysis_result = data
                            st.session_state.current_eval_id = data["evaluation_id"]
                            
                            if data["discarded"]:
                                st.session_state.step = "FINISHED" # O mostrar resultados y luego terminar
                            else:
                                st.session_state.step = "INTERVIEW"
                            st.rerun()
                        else:
                            st.error(f"Error: {resp.text}")
                    except Exception as e:
                        st.error(f"Conexión fallida: {e}")

    elif st.session_state.step == "INTERVIEW":
        st.markdown("### 💬 Entrevista Técnica")
        st.info("El sistema ha detectado algunos puntos por aclarar. Por favor responde al asistente.")
        
        # Inicializar Chat si está vacío
        if not st.session_state.messages:
            with st.spinner("Iniciando entrevista..."):
                try:
                    resp = requests.post(START_INTERVIEW_URL, json={"evaluation_id": st.session_state.current_eval_id})
                    if resp.status_code == 200:
                        st.session_state.messages = resp.json()["history"]
                        st.rerun()
                except:
                    st.error("Error al iniciar entrevista")

        # Interfaz de Chat
        for msg in st.session_state.messages:
            role = msg["role"]
            avatar = "🤖" if role == "assistant" else "👤"
            with st.chat_message(role, avatar=avatar):
                st.write(msg["content"])

        if prompt := st.chat_input("Tu respuesta..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"):
                st.write(prompt)
            
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Pensando..."):
                    payload = {
                        "evaluation_id": st.session_state.current_eval_id,
                        "message": prompt,
                        "history": st.session_state.messages[:-1]
                    }
                    resp = requests.post(INTERVIEW_URL, json=payload)
                    if resp.status_code == 200:
                        reply = resp.json()["response"]
                        st.write(reply)
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                    else:
                        st.error("Error de comunicación")

        st.markdown("---")
        if st.button("Finalizar Entrevista"):
            with st.spinner("Calculando resultados finales..."):
                requests.post(AUDIT_URL, json={"evaluation_id": st.session_state.current_eval_id})
                st.session_state.step = "FINISHED"
                st.rerun()

    elif st.session_state.step == "FINISHED":
        st.markdown("### 🏁 Resultados de la Evaluación")
        
        # Obtener datos más recientes
        try:
             # ¿Simplemente usar la respuesta del endpoint de auditoría o hacer fetch? el backend aún no tiene un get single específico, 
             # pero audit devuelve el resultado completo actualizado.
             # Idealmente llamaríamos a audit de nuevo o tendríamos un get, pero por ahora asumimos que audit actualizó el archivo.
             pass
        except:
            pass

        st.success("El proceso ha finalizado. Sus datos han sido registrados.")
        
        if st.button("Iniciar Nueva Evaluación"):
            st.session_state.step = "INPUT"
            st.session_state.messages = []
            st.session_state.current_eval_id = None
            st.rerun()

with tab2:
    # --- PANEL DEL EVALUADOR ---
    st.markdown("### 📋 Informe Ejecutivo de Candidatos")
    
    col_refresh, col_spacer = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 Actualizar Tabla", use_container_width=True):
            st.rerun()

    try:
        resp = requests.get(EVALUATIONS_URL)
        if resp.status_code == 200:
            evals = resp.json()
            if evals:
                df = pd.DataFrame(evals)
                
                # Mapear descartado booleano a estado user-friendly
                df["discarded"] = df["discarded"].apply(lambda x: "Descartado" if x else "Apto")
                
                # Renombrar columnas para mostrar
                df_display = df.rename(columns={
                    "candidate_name": "Candidato", 
                    "score": "Score Final", 
                    "discarded": "Estado",
                    "total_requirements": "Requisitos",
                    "timestamp": "Fecha"
                })
                
                # Tabla Interactiva
                event = st.dataframe(
                    df_display[["Fecha", "Candidato", "Score Final", "Estado", "Requisitos"]],
                    use_container_width=True,
                    hide_index=True,
                    selection_mode="single-row",
                    on_select="rerun"
                )
                
                # Comprobar selección
                if len(event.selection.rows) > 0:
                    selected_index = event.selection.rows[0]
                    selected_id = evals[selected_index]["id"]
                    
                    st.markdown("---")
                    st.markdown(f"### 📝 Detalle Ejecutivo: {evals[selected_index]['candidate_name']}")
                    
                    # Obtener Detalle
                    try:
                        detail_resp = requests.get(f"{EVALUATIONS_URL}/{selected_id}")
                        if detail_resp.status_code == 200:
                            data = detail_resp.json()
                            eval_data = data["evaluation"]
                            transcript = data["transcript"]
                            
                            # Métricas de Cabecera
                            m1, m2, m3 = st.columns(3)
                            with m1:
                                st.metric("Score Final", f"{eval_data.get('score', 0):.1f}%")
                            with m2:
                                status = "Apto ✅" if not eval_data.get('discarded') else "Descartado ❌"
                                st.metric("Estado", status)
                            with m3:
                                st.metric("Total Requisitos", eval_data.get('total_requirements', 0))
                                
                            # RED FLAGS
                            red_flags = eval_data.get("red_flags", [])
                            if red_flags:
                                st.error("🚩 **RED FLAGS DETECTADAS:**")
                                for rf in red_flags:
                                    st.markdown(f"- {rf}")
                            else:
                                st.success("✅ Sin señales de alerta críticas.")

                            # Puntos Clave
                            key_points = eval_data.get("key_points", [])
                            if key_points:
                                st.info("💡 **Puntos Clave de la Entrevista:**")
                                for kp in key_points:
                                    st.markdown(f"- {kp}")

                            # Análisis de Requisitos
                            st.markdown("#### 🔍 Análisis de Requisitos")
                            
                            # Crear listas de comparación
                            req_data = []
                            for r in eval_data.get("matching_requirements", []):
                                req_data.append({"Requisito": r, "Estado": "Cumplido ✅"})
                            for r in eval_data.get("unmatching_requirements", []):
                                req_data.append({"Requisito": r, "Estado": "No Cumplido ❌"})
                            
                            if req_data:
                                st.table(req_data)
                            
                            # Expansor de Transcripción
                            with st.expander("💬 Ver Transcripción Completa"):
                                st.text(transcript)
                                
                        else:
                            st.error("No se pudieron cargar los detalles.")
                    except Exception as e:
                        st.error(f"Error al cargar detalle: {e}")
                    
            else:
                st.info("No hay evaluaciones registradas aún.")
        else:
            st.error("Error al cargar evaluaciones.")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
