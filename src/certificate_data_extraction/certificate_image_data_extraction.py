import asyncio
import json
import time
import ollama
import os
import sys

from doctr.io import DocumentFile
from doctr.models import ocr_predictor

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..', '..')))
from src.core.logging import get_logger

logger = get_logger("Certificate Data Extractor")

class CertificateDataExtractor:
    def __init__(self):
        # Load OCR model once (saves time)
        # self.model = ocr_predictor(det_arch="linknet_resnet18", reco_arch="crnn_mobilenet_v3_small", pretrained=True)
        self.model = ocr_predictor(pretrained=True)

    async def run_doctr(self, image_path):
        loop = asyncio.get_event_loop()
        # Run OCR in a thread pool to avoid blocking
        return await loop.run_in_executor(None, self._ocr_sync, image_path)

    def _ocr_sync(self, image_path):
        doc = DocumentFile.from_images(image_path)
        result = self.model(doc)
        exported = result.export()

        lines = []
        for page in exported["pages"]:
            for block in page["blocks"]:
                for line in block["lines"]:
                    line_text = " ".join([word["value"] for word in line["words"]])
                    lines.append(line_text)
        logger.info("OCR processing completed.")
        return "\n".join(lines)

    async def train_llm(self, ocr_text: str):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._llm_sync, ocr_text)

    def _llm_sync(self, ocr_text: str):
        prompt = f"""
        From the following extracted certificate text, return a JSON object with:
        "student_name", "father_name", "mother_name", "roll_no", 
        "date_of_birth", "examination_year", "school_name", 
        "ts_gg_no", "certificate_no", "cgpa".

        Text:
        {ocr_text}

        If a field is not found, return "Not Found". 
        Return ONLY the JSON.
        """
        logger.info("LLM processing started.")
        response = ollama.chat(
            model="llama3.2-vision:latest",
            messages=[{"role": "user", "content": prompt}],
            format="json"
        )
        logger.info("LLM processing completed.")
        return json.loads(response["message"]["content"])


async def main():
    extractor = CertificateDataExtractor()
    start = time.time()

    image_path = "./data/sample.jpg"
    # Step 1: Run OCR
    ocr_text = await extractor.run_doctr(image_path)
    print("--- OCR TEXT ---")
    print(ocr_text)
    print(f"Processing time: {time.time() - start:.2f} seconds")

    # Step 2: Run LLM
    structured_data = await extractor.train_llm(ocr_text)
    print("--- LLM RESPONSE ---")
    print(json.dumps(structured_data, indent=4))

    end = time.time()
    print(f"Processing time: {end - start:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
