import os
import cv2
import numpy as np

def order_points(pts):
    """Ordena 4 puntos: [top-left, top-right, bottom-right, bottom-left]."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def four_point_transform(image, pts, target_width=500, target_height=700):
    """Aplica warp y corrige la orientación si la carta está a 90 grados."""
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Calcular ancho y alto reales detectados para deducir la orientación
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # Si el ancho es mayor al alto, la carta está rotada (landscape)
    is_landscape = maxWidth > maxHeight

    if is_landscape:
        # Proyectar temporalmente en formato horizontal
        dst = np.array([
            [0, 0],
            [target_height - 1, 0],
            [target_height - 1, target_width - 1],
            [0, target_width - 1]], dtype="float32")
        matrix = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, matrix, (target_height, target_width))
        # Rotar 90 grados para devolverla a vertical (portrait)
        warped = cv2.rotate(warped, cv2.ROTATE_90_CLOCKWISE)
    else:
        # Proyección estándar vertical
        dst = np.array([
            [0, 0],
            [target_width - 1, 0],
            [target_width - 1, target_height - 1],
            [0, target_height - 1]], dtype="float32")
        matrix = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, matrix, (target_width, target_height))

    return warped

def detect_and_warp_card(image_path, output_dir="data/uploads", target_width=500, target_height=700, save_debug=False):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Fallo al leer: {image_path}")

    # Redimensionar la imagen original si es demasiado grande (ej. fotos de 4K) para no perder los bordes
    h, w = image.shape[:2]
    if h > 1500 or w > 1500:
        scale = 1000.0 / max(h, w)
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    orig = image.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Mejora de contraste adaptativo (CLAHE) vital para fondos inconsistentes
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8))
    gray_clahe = clahe.apply(gray)
    
    blurred = cv2.GaussianBlur(gray_clahe, (5, 5), 0)
    
    # Umbrales Canny más permisivos para captar bordes difuminados por JPEG
    edged = cv2.Canny(blurred, 30, 100)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    card_contour = None
    min_card_area = image.shape[0] * image.shape[1] * 0.10

    for c in contours:
        if cv2.contourArea(c) < min_card_area:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            card_contour = approx
            break

    if card_contour is None:
        if len(contours) > 0 and cv2.contourArea(contours[0]) >= min_card_area:
            x, y, w_box, h_box = cv2.boundingRect(contours[0])
            pts = np.array([[x, y], [x + w_box, y], [x + w_box, y + h_box], [x, y + h_box]], dtype="float32")
        else:
            h, w = image.shape[:2]
            pts = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype="float32")
    else:
        pts = card_contour.reshape(4, 2)

    warped = four_point_transform(orig, pts, target_width=target_width, target_height=target_height)

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    out_path = os.path.join(output_dir, f"{base_name}_warped.jpg")
    cv2.imwrite(out_path, warped)

    if save_debug:
        cv2.drawContours(orig, [pts.astype(int)], -1, (0, 255, 0), 3)
        cv2.imwrite(os.path.join(output_dir, f"{base_name}_debug.jpg"), orig)

    return out_path, warped