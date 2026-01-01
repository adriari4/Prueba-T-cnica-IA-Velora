# Sistema de Evaluación por IA

Esta solución es un ecosistema de reclutamiento inteligente diseñado para automatizar la evaluación técnica de candidatos mediante modelos de lenguaje de gran escala (LLM). El sistema, orquestado con LangChain, ejecuta un flujo de dos fases: análisis autónomo de compatibilidad y entrevista interactiva de validación de requisitos.

## 🏗 Arquitectura del Sistema

El sistema sigue una arquitectura de microservicios contenerizada para garantizar escalabilidad, portabilidad y desacoplamiento técnico:

### Componentes Principales

*   **Frontend (`src/frontend/app.py`)**: Interfaz unificada construida con Streamlit. Incluye:
    *   **Portal del Candidato**: Registro de identidad (Nombre, Apellidos y DNI/Pasaporte) y ejecución de pruebas.
    *   **Panel del Evaluador**: Acceso a Informes Ejecutivos detallados con persistencia de datos.
*   **Backend (`src/backend/engine.py`)**: API robusta en FastAPI que gestiona la lógica de negocio, los agentes de LangChain y el procesamiento de lenguaje natural.
*   **Data Layer**: Persistencia local en `/data/reports/` para auditoría y consulta de resultados en formato JSON y TXT.

## 🦜🔗 Lógica de Negocio y Evaluación

El núcleo del sistema utiliza LangChain para garantizar un procesamiento agnóstico del modelo y estructurado de la información.

### 1. Reglas de Puntuación y Descarte

*   **Identificación Unívoca**: Se registra Nombre, Apellidos y DNI o Pasaporte para vincular cada informe ejecutivo a un candidato real.
*   **Fragmentación Atómica**: Los requisitos compuestos se desglosan en unidades individuales para una evaluación precisa (ej. "FastAPI y LangChain" cuentan como dos ítems).
*   **Cálculo de Score**: Cada requisito tiene un peso equitativo sobre el 100% de la oferta.
*   **Filtro de Descarte Crítico**: Si un requisito marcado como Mínimo o Obligatorio no se identifica en el perfil, el score se fija en 0% y el candidato es descartado automáticamente.
*   **Gestión de Información Faltante**: Los requisitos no encontrados en el CV se derivan a un agente de entrevista que interactúa con el candidato para intentar recuperar esos puntos en el score final.

### 2. Recálculo Dinámico (Fase 2)

Tras la entrevista, el sistema procesa la transcripción y actualiza la puntuación final (ej. de un 50% inicial a un 75% si se valida un requisito extra en la charla).

## 🚀 Ejecución con Docker

El proyecto está completamente dockerizado para permitir una ejecución inmediata en cualquier entorno.

### Pasos de Despliegue

1.  **Variables de Entorno**: Configura el archivo `.env` en la raíz del proyecto:
    ```env
    OPENAI_API_KEY=tu_clave_api_aqui
    LLM_PROVIDER=openai
    LLM_MODEL=gpt-4o
    ```
2.  **Construir y Ejecutar**:
    ```bash
    docker-compose up --build
    ```
3.  **Acceso**:
    *   **Aplicación Web (Streamlit)**: [http://localhost:8501](http://localhost:8501)
    *   **Documentación API (FastAPI)**: [http://localhost:8000/docs](http://localhost:8000/docs)

## � Informe Ejecutivo

El evaluador dispone de un panel privado donde, al seleccionar a un candidato por su identidad, puede visualizar:

*   **Estado Final**: Apto o Descartado por requisito obligatorio.
*   **Evolución del Score**: Comparativa entre la fase de análisis de CV y el resultado tras la entrevista.
*   **Evidencia Técnica**: Desglose detallado de requisitos cumplidos y confirmados por voz/chat.

Desarrollado como solución técnica de evaluación de talento.

## 🔧 Desarrollo Local

Si prefieres correrlo sin Docker:

1.  Crear entorno virtual: `python -m venv .venv`
2.  Activar: `.\.venv\Scripts\Activate` (Windows)
3.  Instalar dependencias: `pip install -r requirements.txt`
4.  Correr Backend:
    ```bash
    uvicorn evaluador-tecnico.src.backend.engine:app --reload
    ```
5.  Correr Frontend:
    ```bash
    streamlit run evaluador-tecnico/src/frontend/app.py
    ```

