import os
import shutil
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session

# Importes de base de datos
from src.database.connection import engine, Base, get_db
from src.database.models import ScanHistory

# Importes del pipeline de visión
from src.pipeline.detector import detect_and_warp_card
from src.pipeline.ocr import extract_card_text
from src.pipeline.matcher import load_metadata, match_card

# 1. Inicialización de Base de Datos y Memoria
Base.metadata.create_all(bind=engine)

try:
    METADATA_DB = load_metadata()
    print(f"Metadata cargada correctamente: {len(METADATA_DB)} cartas.")
except Exception as e:
    print(f"Error cargando metadata: {e}")
    METADATA_DB = []

app = FastAPI(
    title="TCG Recognize API",
    description="API para escaneo y reconocimiento de cartas coleccionables",
    version="1.0.0"
)

# Definir y asegurar directorio de subidas (S2-T3)
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "online", "message": "Bienvenido a TCG Recognize API"}

# Endpoint principal: 
# --> Recibe imagen, procesa OCR, busca coincidencia y guarda historial
@app.post("/api/v1/scan")
async def scan_card(file: UploadFile = File(...), db: Session = Depends(get_db)):
    
    # Validar formato de archivo (S2-T6)
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo enviado no es una imagen válida.")

    # Guardar imagen con nombre único para evitar sobreescrituras
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Ejecutar Pipeline secuencial (S2-T4)
    try:
        warped_path, _ = detect_and_warp_card(file_path, output_dir=UPLOAD_DIR)
        ocr_results = extract_card_text(warped_path)
        match_result = match_card(ocr_results["raw_name"], ocr_results["raw_number"], METADATA_DB)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo crítico en el motor de visión: {str(e)}")

    # Guardar registro en SQLite persistiendo solo la ruta (RT-03)
    card_info = match_result.get("card")
    
    new_scan = ScanHistory(
        image_path=file_path,
        card_name=card_info["name"] if card_info else None,
        card_number=card_info["number"] if card_info else None,
        match_type=match_result["match_type"],
        match_score=match_result["score"]
    )
    
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)

    # Retornar payload estandarizado al frontend
    return {
        "scan_id": new_scan.id,
        "success": match_result["match_type"] != "none",
        "ocr_raw": ocr_results,
        "match": match_result
    }