FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Default command (overridden by docker-compose)
CMD ["uvicorn", "evaluador-tecnico.src.backend.engine:app", "--host", "0.0.0.0", "--port", "8000"]
