# from fastapi import FastAPI, Request
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
# from fastapi.staticfiles import StaticFiles
# from fastapi.middleware.cors import CORSMiddleware

# from src.core.config import settings   # import your config

# # -------------------------
# # Initialize FastAPI App
# # -------------------------
# app = FastAPI(
#     title=settings.app_name,
#     version=settings.app_version,
#     debug=settings.debug
# )

# app.mount("/static", StaticFiles(directory="static"), name = "static")

# templates = Jinja2Templates(directory="templates")


# @app.get("/health")
# def health_check():
#     return {
#         "status": "ok",
#         "environment": settings.environment,
#         "debug": settings.debug,
#         "log_level": settings.log_level
#     }


# @app.get("/")
# def root():
#     return {
#         "message": f"Welcome to {settings.app_name} API 🚀",
#         "version": settings.app_version,
#         "docs": "/docs"
#     }


# @app.get("/config")
# def get_config():
#     return {
#         "app": {
#             "name": settings.app_name,
#             "version": settings.app_version,
#             "environment": settings.environment,
#             "debug": settings.debug,
#         },
#         "storage": {
#             "data_dir": str(settings.storage.data_dir),
#             "output_dir": str(settings.storage.output_dir),
#             "cache_dir": str(settings.storage.cache_dir),
#             "temp_dir": str(settings.storage.temp_dir),
#             "log_file": str(settings.storage.log_file),
#             "database_url": settings.storage.database_url,
#         },
#         "security": {
#             "secret_key": settings.security.secret_key[:6] + "*****",  # hide real key
#             "encrypt_credentials": settings.security.encrypt_credentials,
#             "rate_limiting": settings.security.enable_rate_limiting,
#             "audit_logging": settings.security.audit_logging,
#         },
#         "monitoring": {
#             "metrics_enabled": settings.monitoring.enable_metrics,
#             "metrics_port": settings.monitoring.metrics_port,
#             "health_check_enabled": settings.monitoring.enable_health_check,
#         }
#     }


# @app.get("/index", response_class=HTMLResponse)
# async def index(request : Request):
#     return templates.TemplateResponse("index.html", {"request": request, "title": "Home Page"})




# save as ocr_cert_simple.py
import cv2
import pytesseract
import json
import os
import numpy as np
from PIL import Image
import argparse

import pytesseract

# set full path to tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def preprocess(img):
    # convert, denoise, adaptive threshold, optional deskew
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # bilateral filter keeps edges
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    # adaptive threshold
    th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, 31, 10)
    return th

def deskew(img):
    # Estimate skew and rotate to correct (works on binary)
    coords = np.column_stack(np.where(img > 0))
    if coords.size == 0:
        return img
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = img.shape[:2]
    M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h),
                             flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def ocr_image(path, lang='eng'):
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Can't read image {path}")
    pre = preprocess(img)
    pre = deskew(pre)
    # Use pytesseract to get box data
    pil = Image.fromarray(pre)
    custom_oem_psm_config = r'--oem 3 --psm 6'  # 6 = assume a single uniform block of text
    data = pytesseract.image_to_data(pil, lang=lang, config=custom_oem_psm_config, output_type=pytesseract.Output.DICT)

    results = []
    n_boxes = len(data['level'])
    debug_img = img.copy()
    for i in range(n_boxes):
        text = data['text'][i].strip()  
        conf = int(data['conf'][i]) if str(data['conf'][i]).isdigit() else -1
        if text != '':
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            results.append({'text': text, 'conf': conf, 'box': [int(x), int(y), int(w), int(h)]})
            cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0,255,0), 1)

    base = os.path.splitext(os.path.basename(path))[0]
    out_json = base + '_ocr.json'
    out_img  = base + '_debug.png'
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    cv2.imwrite(out_img, debug_img)
    print(f"Saved {out_json} and {out_img}")
    print(f"Extracted {len(results)} text elements")
    print("Sample extracted text lines:")
    # for r in results[:5]:
    #     print(f" - {r['text']} (conf: {r['conf']})")
    return results

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('image', help='path to certificate image')
    ap.add_argument('--lang', default='eng', help='tesseract language (default eng)')
    args = ap.parse_args()
    res = ocr_image(args.image, lang=args.lang)
    print("Sample extracted text lines:")
    for r in res:
        print(r['text'])
