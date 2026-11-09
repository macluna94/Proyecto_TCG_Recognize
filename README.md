# Pokémon TCG Recognizer

> **Aplicación web para reconocimiento automático de cartas coleccionables Pokémon TCG mediante visión por computadora y procesamiento de lenguaje natural.**

## 📖 Descripción del Proyecto
Pokémon TCG Recognizer es un sistema diseñado para identificar cartas coleccionables a partir de una fotografía tomada desde un dispositivo móvil o archivo local. El proyecto implementa un pipeline robusto de análisis de imágenes que opera sobre el set conmemorativo **Celebrations (ID: `me55`)**, permitiendo aislar la carta, corregir perspectivas e inclinaciones, extraer el texto impreso mediante OCR y reconciliarlo contra una base de datos oficial mediante emparejamiento difuso (*fuzzy matching*).

## 🚀 Características Principales
- **Corrección de Perspectiva y Orientación:** Procesamiento clásico con OpenCV (CLAHE, filtros Canny y detección de contornos) capaz de enderezar cartas inclinadas o rotadas 90 grados a formato estándar de 500x700 píxeles.
- **OCR Especializado:** Extracción de Regiones de Interés (ROIs) con umbrales adaptativos y desenfoque mediano para neutralizar el ruido de los patrones de impresión de semitono.
- **Fuzzy Matching Eficiente:** Limpieza de ruido mediante expresiones regulares y cálculo de similitud (Distancia de Levenshtein) con RapidFuzz para conectar lecturas imperfectas con la metadata oficial.
- **Validación del MVP:** Un pipeline validado con un **75.00% de tasa de acierto** sobre lotes de pruebas reales, operando sin necesidad de modelos de Deep Learning complejos.

## 🛠️ Stack Tecnológico
- **Lenguaje:** Python 3.10+
- **Visión por Computadora:** OpenCV (`cv2`), NumPy, Pillow
- **Reconocimiento de Texto:** Tesseract OCR (`pytesseract`)
- **Matching y Datos:** RapidFuzz, Requests, JSON
- **Backend & Web (Fases siguientes):** FastAPI, SQLAlchemy, SQLite, React / HTML+JS
```
tcg-recognize/
├── .gitignore
├── README.md
├── requirements.txt
├── Dockerfile                  # Base para asegurar OpenCV y Tesseract sin fallos de sistema
│
├── data/
│   ├── metadata_set.json       # Metadata del set objetivo (30–50 cartas)
│   ├── raw_samples/            # 10–20 fotos de prueba rápida de Semana 1
│   ├── test_dataset/           # Fotos reservadas estrictamente para métricas formales en S4
│   └── uploads/                # Directorio para subidas/recortes (rutas guardadas en SQLite)
│
├── docs/
│   └── entrega_I.md            # Documentación y justificaciones de la primera entrega
│
├── notebooks/                  # Opcional: notebooks de exploración o visualización rápida
│   └── 01_opencv_warp_test.ipynb
│
└── src/
    ├── __init__.py
    ├── fetch_metadata.py       # Script de descarga y formateo de metadata
    ├── pipeline/
    │   ├── __init__.py
    │   ├── detector.py         # Detección de bordes y corrección de perspectiva (warp)
    │   ├── ocr.py              # Extracción de texto con Tesseract
    │   └── matcher.py          # Fuzzy matching con RapidFuzz
    └── main.py                 # Punto de entrada o prototipo de integración
```