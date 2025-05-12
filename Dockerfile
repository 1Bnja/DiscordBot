FROM python:3.11-slim

# Instala ffmpeg y certificados del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    ca-certificates \
    curl \
 && update-ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Establecer certificado raíz explícitamente para Python
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

WORKDIR /app
COPY . /app

# Instala pip + dependencias
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]