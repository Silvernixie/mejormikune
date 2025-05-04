# Usar una imagen base extremadamente ligera
FROM python:3.9-slim

WORKDIR /app

# Evitar la creación de archivos __pycache__
ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONUNBUFFERED=1

# Instalar solo las dependencias mínimas necesarias (ffmpeg para música)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copiar solo los archivos de requisitos primero
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt && \
    find /usr/local -type d -name __pycache__ -exec rm -rf {} + || true && \
    apt-get purge -y gcc && \
    apt-get autoremove -y

# Copiar solo los archivos necesarios
COPY main.py extension_handler.py ./
COPY cogs/ ./cogs/
COPY utils/ ./utils/

# Crear carpetas necesarias para datos
RUN mkdir -p data/ticket_archives

# Comando para ejecutar el bot
CMD ["python", "main.py"]