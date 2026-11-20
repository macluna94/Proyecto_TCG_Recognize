import os
import re
import shutil
from collections import Counter
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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
    version="1.1.0",
)

# Habilitar CORS para permitir peticiones desde cualquier origen local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorios
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
FRONTEND_DIR = os.path.join(BASE_DIR, "src", "frontend_web")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Servir imágenes subidas para el modal del historial
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Montar todo el frontend estático en /app (sirve index.html, styles.css y app.js)
app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")



def _card_num_sort_key(number_str: str) -> int:
    match = re.search(r"(\d+)", str(number_str or ""))
    return int(match.group(1)) if match else 99999


@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Bienvenido a TCG Recognize API",
        "app_url": "/app",
        "docs_url": "/docs",
    }






@app.post("/api/v1/scan")
async def scan_card(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Endpoint principal: Recibe imagen, procesa OCR, busca coincidencia y guarda historial."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo enviado no es una imagen válida.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        warped_path, _ = detect_and_warp_card(file_path, output_dir=UPLOAD_DIR)
        ocr_results = extract_card_text(warped_path)
        match_result = match_card(ocr_results["raw_name"], ocr_results["raw_number"], METADATA_DB)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo crítico en el motor de visión: {str(e)}")

    card_info = match_result.get("card")

    new_scan = ScanHistory(
        image_path=file_path,
        card_name=card_info["name"] if card_info else None,
        card_number=card_info["number"] if card_info else None,
        match_type=match_result["match_type"],
        match_score=match_result["score"],
    )

    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)

    return {
        "scan_id": new_scan.id,
        "success": match_result["match_type"] != "none",
        "ocr_raw": ocr_results,
        "match": match_result,
    }


@app.get("/api/v1/collection")
def get_collection(db: Session = Depends(get_db)):
    """Cruza el catálogo del set (metadata_set.json) con los escaneos exitosos en SQLite."""
    scans = db.query(ScanHistory).filter(ScanHistory.match_type != "none").all()
    counts = Counter(str(s.card_number) for s in scans if s.card_number)

    cards = []
    for card in METADATA_DB:
        num = str(card.get("number", ""))
        qty = counts.get(num, 0)
        cards.append(
            {
                "id": card.get("id"),
                "name": card.get("name"),
                "number": num,
                "rarity": card.get("rarity", "Special"),
                "image_url": card.get("image_url"),
                "owned": qty > 0,
                "count": qty,
            }
        )

    cards.sort(key=lambda c: _card_num_sort_key(c["number"]))

    total_set = len(cards)
    unique_owned = sum(1 for c in cards if c["owned"])
    total_physical = sum(counts.values())
    progress_pct = round((unique_owned / total_set) * 100, 1) if total_set else 0.0

    return {
        "set_name": "30th Celebration",
        "set_id": "me55",
        "total_cards": total_set,
        "unique_owned": unique_owned,
        "total_physical": total_physical,
        "progress_pct": progress_pct,
        "cards": cards,
    }


@app.get("/api/v1/stats")
def get_stats(db: Session = Depends(get_db)):
    """Devuelve métricas del coleccionista, progreso del set y top duplicados."""
    all_scans = db.query(ScanHistory).order_by(ScanHistory.scanned_at.desc()).all()
    success_scans = [s for s in all_scans if s.match_type and s.match_type != "none"]

    total_scans = len(all_scans)
    success_count = len(success_scans)
    success_rate = round((success_count / total_scans) * 100, 1) if total_scans else 0.0
    avg_score = (
        round(sum(s.match_score or 0 for s in success_scans) / success_count, 1)
        if success_count
        else 0.0
    )

    meta_by_num = {str(c.get("number")): c for c in METADATA_DB}
    unique_nums = {str(s.card_number) for s in success_scans if s.card_number}
    total_set = len(METADATA_DB) or 50
    progress_pct = round((len(unique_nums) / total_set) * 100, 1) if total_set else 0.0

    # Top cartas repetidas
    counts = Counter((str(s.card_number), s.card_name) for s in success_scans if s.card_number)
    duplicates = []
    for (num, name), qty in counts.most_common(5):
        card_meta = meta_by_num.get(num, {})
        duplicates.append(
            {
                "number": num,
                "name": name or card_meta.get("name", "Desconocida"),
                "count": qty,
                "image_url": card_meta.get("image_url"),
            }
        )

    return {
        "total_scans": total_scans,
        "successful_scans": success_count,
        "failed_scans": total_scans - success_count,
        "success_rate": success_rate,
        "avg_score": avg_score,
        "unique_cards": len(unique_nums),
        "total_set_cards": total_set,
        "progress_pct": progress_pct,
        "duplicates": duplicates,
    }


@app.get("/api/v1/history")
def get_history(db: Session = Depends(get_db)):
    """Devuelve el historial completo de escaneos ordenado del más reciente al más antiguo."""
    scans = db.query(ScanHistory).order_by(ScanHistory.scanned_at.desc()).all()
    meta_by_num = {str(c.get("number")): c for c in METADATA_DB}

    total = len(scans)
    success = sum(1 for s in scans if s.match_type and s.match_type != "none")
    success_rate = round((success / total) * 100, 1) if total else 0.0

    items = []
    for s in scans:
        num = str(s.card_number) if s.card_number else ""
        meta = meta_by_num.get(num, {})
        filename = os.path.basename(s.image_path) if s.image_path else None
        items.append(
            {
                "id": s.id,
                "scanned_at": s.scanned_at.strftime("%d %b %Y, %H:%M") if s.scanned_at else "--",
                "card_name": s.card_name or "No identificada",
                "card_number": num or "--",
                "rarity": meta.get("rarity", "Sin clasificar"),
                "match_type": s.match_type or "none",
                "match_score": round(s.match_score or 0.0, 1),
                "image_url": meta.get("image_url"),
                "uploaded_image": f"/uploads/{filename}" if filename else None,
            }
        )

    return {"total": total, "success_rate": success_rate, "items": items}