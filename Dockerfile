# Imagen base ligera con Python
FROM python:3.11-slim

# Instalar ffmpeg y certificados SSL
RUN apt-get update && apt-get install -y \
    ffmpeg \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Crear carpeta de trabajo
WORKDIR /app

# Copiar todos los archivos del proyecto
COPY . /app

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Ejecutar el bot
CMD ["python", "main.py"]
