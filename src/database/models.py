from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from .connection import Base

class ScanHistory(Base):
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, index=True)
    # Solo guardamos la ruta en el sistema de archivos (ej. data/uploads/imagen1.jpg)
    image_path = Column(String, nullable=False)
    
    # Datos de la coincidencia
    card_name = Column(String, nullable=True)
    card_number = Column(String, nullable=True)
    match_type = Column(String, nullable=True) # exact_number, fuzzy_name, none
    match_score = Column(Float, nullable=True)
    
    # Fecha de escaneo
    scanned_at = Column(DateTime, default=datetime.utcnow)


    