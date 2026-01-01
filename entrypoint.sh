#!/bin/bash

# Iniciar FastAPI en segundo plano
uvicorn evaluador-tecnico.src.backend.engine:app --host 0.0.0.0 --port 8000 &

# Iniciar Streamlit en primer plano
streamlit run evaluador-tecnico/src/frontend/app.py --server.port=8501 --server.address=0.0.0.0
