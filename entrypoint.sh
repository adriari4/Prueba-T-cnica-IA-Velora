#!/bin/bash

# Start FastAPI in background
uvicorn evaluador-tecnico.src.backend.engine:app --host 0.0.0.0 --port 8000 &

# Start Streamlit in foreground
streamlit run evaluador-tecnico/src/frontend/app.py --server.port=8501 --server.address=0.0.0.0
