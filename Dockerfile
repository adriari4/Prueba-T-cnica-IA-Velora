FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema si es necesario (ej. para herramientas de compilación)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar Código del Proyecto
COPY . /app

# Exponer puertos
EXPOSE 8501
EXPOSE 8000

# Hacer ejecutable el entrypoint
RUN chmod +x entrypoint.sh

# Variables de entorno
ENV PYTHONUNBUFFERED=1

# Comando para ejecutar ambos servicios
CMD ["./entrypoint.sh"]
