# Entrega III: Interfaz Gráfica (Frontend) y Experiencia de Usuario

## 1. Evolución y Arquitectura del Frontend
Tras validar un primer prototipo funcional en **Streamlit** para probar el ciclo de carga y visualización, se dio el salto a una **aplicación web responsiva independiente** diseñada bajo el sistema visual **Pastel Kanto OS** (tema claro inspirado en la Pokédex de Kanto, tipografía `Inter` + `JetBrains Mono` y paleta pastel de alto contraste).

Para cumplir con el principio de separación de responsabilidades (*Separation of Concerns*) y facilitar el mantenimiento, el frontend se organizó de forma modular dentro de `src/frontend_web/`:
* **`index.html`:** Estructura semántica de las 4 vistas y navegación adaptativa (barra lateral fija en escritorio y barra inferior fija en móvil).
* **`styles.css`:** Variables de color, tipografía, soporte de áreas seguras móviles (`safe-area-inset`) y utilidades visuales.
* **`app.js`:** Control de navegación, manejo de *Drag & Drop* y cámara móvil, consumo asíncrono de la API vía `fetch()` y renderizado dinámico del DOM.

La interfaz se sirve directamente desde **FastAPI** mediante `StaticFiles` en la ruta `/app`, lo que simplifica la arquitectura y permite desplegar backend y frontend en un único contenedor Docker sin servidores adicionales.

## 2. Vistas Implementadas y Aprovechamiento de Datos
Para transformar la herramienta de un escáner puntual a un gestor completo de colección del set *30th Celebration* (`me55`), se diseñaron cuatro secciones principales:

1. **Escáner de Cartas:** Zona interactiva de *Drag & Drop* (y acceso directo a cámara nativa en dispositivos móviles), vista previa inmediata, indicador de carga durante el procesamiento (OpenCV + Tesseract + RapidFuzz), tarjeta de resultado con el arte oficial y un acordeón de depuración (*DEBUG*) con el JSON crudo del OCR.
2. **Álbum de Colección (*Binder*):** Cuadrícula responsiva (2 columnas en móvil hasta 5 en escritorio) ordenada por número de carta. Cruza el catálogo oficial (`data/metadata_set.json`) con los escaneos exitosos en SQLite, mostrando a todo color las cartas obtenidas con contador de copias (`x2`, `x3`) y como ranuras bloqueadas las cartas faltantes del set.
3. **Dashboard Analítico:** Tarjetas KPI en tiempo real (cartas escaneadas, cartas únicas, progreso porcentual del set), gráfica de barras con el top de cartas repetidas y métricas globales de rendimiento del OCR (tasa de éxito y confianza promedio).
4. **Historial de Escaneos:** Vista adaptativa (tabla completa en escritorio y tarjetas compactas en móvil) con buscador en tiempo real, filtros por método de coincidencia (`exact_number`, `fuzzy_name`, `none`) y modal de inspección que muestra la fotografía original almacenada en `data/uploads/`.

## 3. Extensión de la API REST (`src/api/main.py`)
Para desacoplar completamente la interfaz del acceso directo al archivo SQLite, se habilitó `CORSMiddleware`, se expuso el directorio estático `/uploads` y se añadieron tres endpoints de lectura (`GET`) complementarios a `POST /api/v1/scan`:
* **`GET /api/v1/collection`:** Devuelve el catálogo del set `me55` cruzado con el inventario único y conteo de copias físicas en `scan_history`.
* **`GET /api/v1/stats`:** Calcula métricas agregadas del coleccionista, progreso del set, tasa de éxito del OCR y top de duplicados.
* **`GET /api/v1/history`:** Retorna el historial cronológico completo de escaneos con enlaces a la imagen oficial y a la foto capturada.

## 4. Validación Local, Red y Contenedor
* **Flujo end-to-end:** Se verificó la carga de imagen, detección/OCR, guardado en SQLite y actualización inmediata en Álbum, Dashboard e Historial.
* **Prueba en Docker:** Se construyó y validó la imagen `tcg-recognize-api` sirviendo simultáneamente la API (`/docs`) y la interfaz web (`/app`) dentro del entorno Linux.
* **Prueba móvil en red local:** Se validó la vista responsiva y captura desde navegador móvil exponiendo Uvicorn en `0.0.0.0:8000`.