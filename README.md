
# Proyecto_TCG_Recognize


 **Materia**: Reonocimiento de Patrones
## Estructura del Proyecto

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
