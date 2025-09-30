FROM python:3.9-slim

# Instalar dependencias del sistema necesarias para moviepy y ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar archivos de requisitos primero para aprovechar la cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p uploads processed

# Exponer el puerto
EXPOSE 5000

# Variable de entorno para Flask
ENV FLASK_APP=app1.py
ENV FLASK_ENV=production

# Comando para ejecutar la aplicación
CMD ["python", "app1.py"]