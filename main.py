# app.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from PIL import Image, ImageOps
import pytesseract
import requests
import base64
import os
import tempfile
import json
import re

app = FastAPI()

OLLAMA_URL = "http://localhost:11434/api/generate"

# ---------- Helpers ----------
def preprocess_image_for_ocr(path: str, max_width=1600) -> str:
    """Open image, convert to RGB, autocontrast, resize if large, save a temp PNG and return path."""
    img = Image.open(path).convert("RGB")
    # autocontrast to improve OCR
    img = ImageOps.autocontrast(img)
    # resize if too wide
    if img.width > max_width:
        ratio = max_width / float(img.width)
        new_h = int(img.height * ratio)
        img = img.resize((max_width, new_h), Image.LANCZOS)
    out = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    img.save(out.name, format="PNG")
    out.close()
    return out.name

def ocr_text_from_image(path: str) -> str:
    """Return OCR text using pytesseract (English). Adjust config to get multi-line text."""
    ocr_config = "--psm 6"  # assume a single uniform block of text; tweak if needed
    try:
        text = pytesseract.image_to_string(Image.open(path), config=ocr_config, lang="eng")
    except Exception:
        text = ""
    return text.strip()

def call_ollama_text_model(text: str, model: str = "mistral:instruct") -> str:
    """Call Ollama with text prompt (for mistral/text-based extraction)."""
    prompt = f"""
You are an expert document parser. Extract EXACTLY the following JSON object and nothing else.
Keys (use these exact keys): "Full Name", "Certificate Title", "Issuing Authority", "Date of Issue", "Certificate ID"
If a field is not present in the text, set its value to null.
Do NOT invent or guess values not present in the text.

Certificate text:
\"\"\"{text}\"\"\"

Return valid JSON only.
"""
    payload = {
        "model": model,
        "prompt": prompt,
        "temperature": 0.0,
        "max_tokens": 512
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
    return _collect_response_text(resp)

def call_ollama_vision_model(image_path: str, model: str = "llava") -> str:
    """Call Ollama with an image; strict JSON instructions to avoid hallucination."""
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    prompt = """
You are an expert document analyzer. Given the image, extract EXACTLY the following JSON object and nothing else.
Keys (use these exact keys): "Full Name", "Certificate Title", "Issuing Authority", "Date of Issue", "Certificate ID"
If a field is not present in the image, set its value to null.
Do NOT invent or guess; if unsure, set the field to null.
Return valid JSON only.
"""
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [img_b64],
        "temperature": 0.0,
        "max_tokens": 512
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
    return _collect_response_text(resp)

def _collect_response_text(response):
    """Collect streaming or normal response body text. Ollama may return lines of JSON containing 'response'."""
    try:
        # If response is chunked or streaming, handle lines like earlier code
        output = ""
        for line in response.iter_lines():
            if not line:
                continue
            try:
                parsed = json.loads(line.decode("utf-8"))
                # older responses used key "response"
                if isinstance(parsed, dict) and "response" in parsed:
                    output += parsed.get("response", "")
                else:
                    output += line.decode("utf-8")
            except Exception:
                # fallback to raw string
                output += line.decode("utf-8")
        if output:
            return output.strip()
    except Exception:
        pass

    # Fallback: try response.text
    try:
        return response.text.strip()
    except Exception:
        return ""

def extract_first_json(text: str):
    """Extract the first {...} JSON object from a string."""
    if not text:
        return None
    text = text.strip()
    start = text.find('{')
    if start == -1:
        return None
    brace_count = 0
    for i, c in enumerate(text[start:], start):
        if c == '{':
            brace_count += 1
        elif c == '}':
            brace_count -= 1
            if brace_count == 0:
                candidate = text[start:i+1]
                try:
                    return json.loads(candidate)
                except Exception:
                    try:
                        fixed = candidate.replace("'", '"')
                        return json.loads(fixed)
                    except Exception:
                        return None
    return None

# ---------- Main classifier (hybrid) ----------
def classify_certificate(image_path: str) -> dict:
    """Hybrid: OCR -> if OCR is good use text model; otherwise use vision model.
       Returns a dict (parsed JSON) or fallback dict with 'raw' output."""
    # Preprocess for OCR
    preproc_path = preprocess_image_for_ocr(image_path)

    ocr_text = ocr_text_from_image(preproc_path)
    # cleanup preproc file
    try:
        os.remove(preproc_path)
    except Exception:
        pass

    # Decide path: if OCR produced decent text, use text model (more deterministic).
    if ocr_text and len(ocr_text) > 60:
        model_output = call_ollama_text_model(ocr_text, model="mistral:instruct")
        parsed = extract_first_json(model_output)
        if parsed:
            return {"method": "ocr+mistral", "parsed": parsed, "raw": model_output}
        # fallback to vision model if parsing fails
    # Use vision model (llava)
    model_output = call_ollama_vision_model(image_path, model="llava")
    parsed = extract_first_json(model_output)
    if parsed:
        return {"method": "llava", "parsed": parsed, "raw": model_output}
    # Last-resort: return raw model text so you can debug
    return {"method": "raw", "parsed": None, "raw": model_output}

# ---------- FastAPI endpoints ----------
@app.post("/upload/")
async def upload_certificate(file: UploadFile = File(...)):
    try:
        # Save uploaded file temporarily
        suffix = os.path.splitext(file.filename)[1] or ".png"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        result = classify_certificate(tmp_path)

        # cleanup
        try:
            os.remove(tmp_path)
        except Exception:
            pass

        # If parsed is None, return raw output and a helpful message
        if result.get("parsed") is None:
            return JSONResponse({
                "warning": "Could not parse strict JSON from model. See raw output to debug or improve prompt/OCR.",
                "result": result
            }, status_code=200)

        return JSONResponse({"result": result}, status_code=200)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Certificate Upload</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 50px; background: #f4f4f4; }
        .container { max-width: 600px; margin: auto; padding: 20px; background: white; border-radius: 10px; box-shadow: 0px 2px 6px rgba(0,0,0,0.2); }
        input[type=file] { display:block; margin: 20px auto; }
        button { display:block; margin:auto; padding:10px 20px; background:#4CAF50; color:white; border:none; border-radius:5px; cursor:pointer; }
        pre { background:#eee; padding:15px; border-radius:5px; margin-top:20px; white-space:pre-wrap; word-wrap:break-word; }
      </style>
    </head>
    <body>
      <div class="container">
        <h2>Upload Certificate</h2>
        <form id="uploadForm">
          <input type="file" name="file" id="fileInput" required>
          <button type="submit">Upload</button>
        </form>
        <pre id="result"></pre>
      </div>
      <script>
    const form = document.getElementById("uploadForm");
    form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById("fileInput");
    if (!fileInput.files.length) return;

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const resp = await fetch("/upload/", { method: "POST", body: formData });
    const data = await resp.json();

    let displayText = "";
    if (data.result && data.result.parsed) {
        displayText = JSON.stringify(data.result.parsed, null, 2);
    } else if (data.warning) {
        displayText = data.warning + "\n\n" + JSON.stringify(data.result, null, 2);
    } else {
        displayText = JSON.stringify(data, null, 2);
    }

    document.getElementById("result").innerText = displayText;
    });
    </script>
    </body>
    </html>
    """

