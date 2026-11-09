# Entrega I: Planificación y Viabilidad Técnica

## 1. Definición del Alcance (MVP)
El proyecto "TCG Recognize" se enfoca en reconocer cartas del set de Pokémon TCG *30th Celebration* (ID: `me55`). Para acotar el desarrollo y garantizar estabilidad, el MVP restringe las evaluaciones a una carta por imagen, tomadas bajo condiciones de luz razonables para minimizar reflejos holográficos complejos.

## 2. Estrategia Técnica Seleccionada (Ruta A)
Tras procesar un lote de imágenes reales capturadas con dispositivo móvil, se comprobó la viabilidad de la **Ruta A** (Procesamiento de imagen clásico + OCR + Fuzzy Matching), postergando la necesidad de entrenar modelos de Deep Learning.

El pipeline consta de tres etapas comprobadas:
1. **Alineación de Perspectiva (OpenCV):** Uso de CLAHE, filtro Canny dinámico y detección de contornos para aislar la carta. Se incluye un sistema de transformación de perspectiva que corrige rotaciones horizontales de 90° proyectando la carta a una resolución estándar de 500x700 px.
2. **Extracción de Texto (Tesseract OCR):** Preprocesamiento de Regiones de Interés (ROIs) mediante desenfoque mediano y umbrales adaptativos para empastar el puntillismo de impresión y separar las letras del fondo.
3. **Reconciliación (RapidFuzz):** Limpieza de ruido residual mediante expresiones regulares (Regex) y cálculo de coincidencia aproximada (Distancia de Levenshtein) contra los registros de `metadata_set.json`.

## 3. Resultados del Prototipo
El script integrado arrojó las siguientes métricas de evaluación sobre el entorno local:
* **Tamaño de muestra:** 20 imágenes de prueba (`data/raw_samples/`).
* **Cartas identificadas correctamente:** 15
* **Tasa de acierto global:** 75.00%
* **Velocidad de ejecución:** 8.37 segundos totales (aprox. 0.4s por carta).

**Conclusión:** Al superar el 60% de precisión en su etapa más temprana, el método es robusto frente a rotaciones, inclinaciones e impurezas de impresión. La arquitectura es viable para pasar a la fase de construcción de la API REST.