FROM python:3.9-bullseye

# Instalar FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Crear el directorio del bot
WORKDIR /usr/src/bot

# Copiar requirements.txt primero
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código fuente
COPY . .

# Comando para iniciar el bot
CMD ["python", "main.py"]