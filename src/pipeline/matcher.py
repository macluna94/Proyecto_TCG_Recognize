import json
import os
import re
from rapidfuzz import process, fuzz

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
METADATA_FILE = os.path.join(DATA_DIR, "metadata_set.json")


def load_metadata():
    if not os.path.exists(METADATA_FILE):
        raise FileNotFoundError(f"No se encontró la metadata en: {METADATA_FILE}")
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# Filtra el ruido del OCR dejando solo caracteres útiles
def clean_ocr_text(raw_name, raw_number):
    # Nombre: Mantener solo letras (mayúsculas/minúsculas), espacios y guiones.
    # Esto elimina tildes falsas (~~) y comas (,)
    clean_name = re.sub(r"[^a-zA-Z\s\-]", "", raw_name).strip()

    # Número: Extraer específicamente el patrón de números separados por barra (ej. 022/128)
    # Esto ignora números sueltos como el '5' detectado por error.
    num_match = re.search(r"(\d{1,3}/\d{1,3})", raw_number)
    clean_number = num_match.group(1) if num_match else ""

    return clean_name, clean_number


# Encuentra la mejor coincidencia en la metadata usando RapidFuzz
def match_card(raw_name, raw_number, metadata):
    clean_name, clean_number = clean_ocr_text(raw_name, raw_number)
    
    print(f"Texto limpio tras Regex -> Nombre: '{clean_name}' | Número: '{clean_number}'")

    # Estrategia 1: Coincidencia dura por número de carta (es el dato más seguro si se leyó bien)
    if clean_number:
        # Algunos sets en el JSON solo guardan "022" en lugar de "022/128"
        base_num = clean_number.split("/")[0].lstrip("0")  # Convierte "022" a "22"
        for card in metadata:
            card_num = str(card.get("number", "")).lstrip("0")
            if card_num == base_num:
                return {"match_type": "exact_number", "score": 100.0, "card": card}

    # Estrategia 2: Fuzzy matching por nombre (Si el número falló o no se leyó)
    if clean_name:
        # Extraer lista de nombres válidos del set
        valid_names = [card["name"] for card in metadata]
        
        # Obtener la mejor coincidencia usando el ratio de RapidFuzz
        # process.extractOne devuelve: (nombre_coincidente, puntuacion, indice)
        best_match_tuple = process.extractOne(
            clean_name, valid_names, scorer=fuzz.WRatio
        )
        
        if best_match_tuple:
            best_name, score, index = best_match_tuple
            # Umbral de confianza: Si la similitud es mayor al 65%
            if score >= 65.0:
                return {
                    "match_type": "fuzzy_name",
                    "score": round(score, 2),
                    "card": metadata[index],
                }

    return {"match_type": "none", "score": 0.0, "card": None}


if __name__ == "__main__":
    # Prueba manual con tu lectura fallida del OCR
    ocr_simulado_name = "~~ Wisniwasht ss,"
    ocr_simulado_num = "5 \n\n 022/128"

    print("Cargando base de datos del set...")
    try:
        cards_db = load_metadata()
        resultado = match_card(ocr_simulado_name, ocr_simulado_num, cards_db)

        if resultado["card"]:
            print("\n¡Carta identificada con éxito!")
            print(f"Tipo de coincidencia: {resultado['match_type']} (Score: {resultado['score']})")
            print(f"ID: {resultado['card']['id']}")
            print(f"Nombre Oficial: {resultado['card']['name']}")
            print(f"Rareza: {resultado['card']['rarity']}")
        else:
            print("\nNo se logró emparejar la carta con confianza suficiente.")
            
    except FileNotFoundError as e:
        print(e)