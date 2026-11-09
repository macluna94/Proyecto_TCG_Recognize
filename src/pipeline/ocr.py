import os
import cv2
import numpy as np
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Ajusta según tu instalación


def preprocess_for_ocr(roi_image):
    """Preprocesamiento con reducción de ruido de semitono (puntillismo) de impresión."""
    if len(roi_image.shape) == 3:
        gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = roi_image

    # 1- Escalar (x3) para darle mayor volumen a los caracteres finos
    resized = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
    
    # 2- Desenfoque mediano: CRÍTICO para empastar los puntos de fondo sin perder los bordes de las letras
    blurred = cv2.medianBlur(resized, 5)
    
    # 3- Umbral adaptativo más tolerante (aumentamos block size a 15 y la constante a 5)
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 5
    )
    
    # 4- Cierre morfológico leve para rellenar huecos dentro de las letras
    kernel = np.ones((2, 2), np.uint8)
    clean_thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    return clean_thresh


def extract_card_text(warped_image_or_path, save_rois=False):
    """Extrae el texto crudo del nombre y del número de una carta alineada (500x700)."""
    if isinstance(warped_image_or_path, str):
        if not os.path.exists(warped_image_or_path):
            raise FileNotFoundError(f"Archivo no encontrado: {warped_image_or_path}")
        image = cv2.imread(warped_image_or_path)
    else:
        image = warped_image_or_path

    h, w = image.shape[:2]

    # 1- Definición de ROIs porcentuales estándar
    # Nombre: (parte superior izquierda)
    y1_name, y2_name = int(h * 0.04), int(h * 0.11)
    x1_name, x2_name = int(w * 0.05), int(w * 0.70)
    roi_name = image[y1_name:y2_name, x1_name:x2_name]

    # Numero de carta: (esquina inferior izquierda)
    y1_num, y2_num = int(h * 0.90), int(h * 0.98)
    x1_num, x2_num = int(w * 0.07), int(w * 0.28)
    roi_num = image[y1_num:y2_num, x1_num:x2_num]

    # 2- Preprocesamiento binarizado
    processed_name = preprocess_for_ocr(roi_name)
    processed_num = preprocess_for_ocr(roi_num)

    # 3- Configuraciones de Tesseract sin comillas problemáticas para Windows
    config_name = "--psm 6"
    config_num = "--psm 11 -c tessedit_char_whitelist=0123456789/"

    # 4- Extracción de texto
    raw_name = pytesseract.image_to_string(processed_name, config=config_name).strip()
    raw_num = pytesseract.image_to_string(processed_num, config=config_num).strip()

    # Guardar recortes para inspección visual en data/uploads/
    if save_rois and isinstance(warped_image_or_path, str):
        base_name = os.path.splitext(os.path.basename(warped_image_or_path))[0]
        out_dir = os.path.dirname(warped_image_or_path)
        # Unificamos el formato a .jpg
        cv2.imwrite(os.path.join(out_dir, f"{base_name}_roi_name.jpg"), processed_name)
        cv2.imwrite(os.path.join(out_dir, f"{base_name}_roi_num.jpg"), processed_num)

    return {"raw_name": raw_name, "raw_number": raw_num}


if __name__ == "__main__":
    import glob

    # Buscar archivos .jpg procesados por el detector
    warped_files = glob.glob("data/uploads/*_warped.jpg")
    
    if not warped_files:
        print("No hay archivos '_warped.jpg' en data/uploads/. Ejecuta primero el detector.")
    else:
        # Probar con el primer archivo encontrado
        test_file = warped_files[0]
        print(f"Probando OCR sobre: {test_file}")
        
        results = extract_card_text(test_file, save_rois=True)
        
        print("Resultado OCR obtenido:")
        print(f" -> Nombre detectado: '{results['raw_name']}'")
        print(f" -> Número detectado: '{results['raw_number']}'")