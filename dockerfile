# Usar una imagen oficial de Python ligera
FROM python:3.12-slim

# Evitar que Python genere archivos .pyc y forzar salida estándar en consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema operativo (CRÍTICO para OpenCV y Tesseract)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de requerimientos e instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código fuente al contenedor
COPY . /app/

# Crear la carpeta de base de datos y uploads si no existen
RUN mkdir -p /app/data/uploads

# Exponer el puerto que usará FastAPI
EXPOSE 8000

# Comando para arrancar el servidor de producción con Uvicorn
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]