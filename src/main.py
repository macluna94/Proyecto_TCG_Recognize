import os
import glob
import time

# Importaciones de tu pipeline
from pipeline.detector import detect_and_warp_card
from pipeline.ocr import extract_card_text
from pipeline.matcher import load_metadata, match_card

def evaluate_prototype():
    print("=== Iniciando Pipeline de TCG Recognize (Prototipo Ruta A) ===")
    
    # 1- Cargar metadatos
    try:
        metadata = load_metadata()
        print(f"[OK] Metadata cargada: {len(metadata)} cartas disponibles en el set.")
    except Exception as e:
        print(f"[ERROR] No se pudo cargar la metadata: {e}")
        return

    # 2- Obtener imágenes de prueba
    sample_dir = os.path.join("data", "raw_samples")
    image_files = glob.glob(os.path.join(sample_dir, "*.[jJ][pP][gG]")) + \
                  glob.glob(os.path.join(sample_dir, "*.[pP][nN][gG]")) + \
                  glob.glob(os.path.join(sample_dir, "*.[jJ][pP][eE][gG]"))
    
    if not image_files:
        print(f"[ADVERTENCIA] No se encontraron imágenes en {sample_dir}")
        return

    total_images = len(image_files)
    successful_matches = 0
    results_log = []

    print(f"\n[INICIO] Procesando {total_images} imágenes de prueba...\n")
    start_time = time.time()

    # 3- Ejecutar pipeline secuencial para cada imagen
    for idx, img_path in enumerate(image_files, 1):
        filename = os.path.basename(img_path)
        print(f"--- Evaluando ({idx}/{total_images}): {filename} ---")
        
        try:
            # Paso A: Detección y Warp
            warped_path, _ = detect_and_warp_card(img_path, save_debug=False)
            
            # Paso B: Extracción OCR
            ocr_results = extract_card_text(warped_path, save_rois=False)
            
            # Paso C: Búsqueda y Emparejamiento
            match_result = match_card(
                ocr_results["raw_name"], 
                ocr_results["raw_number"], 
                metadata
            )
            
            # Registro de resultados
            if match_result["match_type"] != "none":
                successful_matches += 1
                card_info = match_result["card"]
                print(f" -> [ÉXITO] Carta identificada: {card_info['name']} ({card_info['number']})")
                print(f" -> Método: {match_result['match_type']} | Score: {match_result['score']}")
                results_log.append((filename, True, card_info['name']))
            else:
                print(f" -> [FALLO] No se superó el umbral de confianza.")
                print(f" -> OCR detectó: Nombre '{ocr_results['raw_name']}' | Número '{ocr_results['raw_number']}'")
                results_log.append((filename, False, None))
                
        except Exception as e:
            print(f" -> [ERROR CRÍTICO] Fallo procesando {filename}: {e}")
            results_log.append((filename, False, None))
        
        print("") # Salto de línea visual

    # 4- Cálculo de métricas
    elapsed_time = time.time() - start_time
    success_rate = (successful_matches / total_images) * 100

    print("=== Resumen de Evaluación (S1-T8) ===")
    print(f"Total procesadas:   {total_images}")
    print(f"Identificadas:      {successful_matches}")
    print(f"Tasa de éxito:      {success_rate:.2f}%")
    print(f"Tiempo total:       {elapsed_time:.2f} segundos")
    
    # Evaluar si la Ruta A es viable para la entrega (S1-T9)
    if success_rate >= 60.0:
        print("\n[CONCLUSIÓN] La Ruta A (OpenCV + OCR) es viable para el MVP.")
    else:
        print("\n[CONCLUSIÓN] La Ruta A necesita ajustes en iluminación/OCR, o considerar Ruta B a futuro.")

if __name__ == "__main__":
    evaluate_prototype()