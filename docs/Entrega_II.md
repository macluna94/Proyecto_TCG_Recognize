# Entrega II: Arquitectura Backend y Persistencia

## 1. Diseño de la API REST
El backend del proyecto "TCG Recognize" fue construido utilizando **FastAPI**. Esta decisión técnica se basó en su alto rendimiento, procesamiento asíncrono y la generación automática de documentación interactiva (Swagger UI/OpenAPI).

### Endpoint Principal
* **`POST /api/v1/scan`**: Recibe una imagen (`multipart/form-data`), orquesta el pipeline de visión por computadora (OpenCV + Tesseract) acoplado al módulo de *fuzzy matching*, y retorna un payload JSON estructurado con los metadatos de la carta identificada, porcentaje de coincidencia y confirmación de estado.

## 2. Estrategia de Persistencia (SQLite y RT-03)
Para el almacenamiento, se integró **SQLite** gestionado a través del ORM **SQLAlchemy**. 
Cumpliendo estrictamente con la directiva técnica RT-03, la base de datos se diseñó para ser ligera y escalable:
* **Tabla `ScanHistory`**: Registra la metadata de cada carta procesada (nombre, número, método de coincidencia, score y timestamp).
* **Almacenamiento de Archivos**: Las imágenes subidas *no* se guardan como objetos BLOB en la base de datos. En su lugar, se almacenan físicamente en el sistema de archivos (`data/uploads/`) generando un nombre único con marca de tiempo, y en SQLite únicamente se persiste la ruta (`image_path`).

## 3. Contenerización y Preparación para Despliegue
Se configuró un `Dockerfile` basado en `python:3.12-slim` que resuelve dependencias críticas a nivel de sistema operativo que no pueden resolverse vía PIP. Esto incluye la instalación de los binarios de `tesseract-ocr` y las librerías gráficas `libgl1` y `libglib2.0-0` requeridas por OpenCV, garantizando un entorno hermético y listo para su futuro despliegue en plataformas PaaS.