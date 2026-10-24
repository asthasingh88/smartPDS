import re
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, HTTPException, UploadFile
from paddleocr import PaddleOCR
from PIL import Image, UnidentifiedImageError

router = APIRouter()

# OCR engine ko ek hi baar initialize karenge
ocr_engine = PaddleOCR(use_angle_cls=True, lang="en")


def extract_fields(text: str) -> dict:
    """OCR text se receipt/challan ke common fields extract karta hai."""

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    full_text = "\n".join(lines)

    challan_match = re.search(
        r"(?:challan|receipt|invoice)\s*(?:no\.?|number|#)?\s*[:\-]?\s*([A-Z0-9/-]{3,})",
        full_text,
        re.IGNORECASE,
    )

    date_match = re.search(
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
        full_text,
    )

    quantity_match = re.search(
        r"\b(?:quantity|qty|weight|net weight)\s*[:\-]?\s*"
        r"(\d+(?:\.\d+)?)\s*(kg|kgs|kilograms?)?\b",
        full_text,
        re.IGNORECASE,
    )

    commodity_match = re.search(
        r"\b(wheat|rice| गेहूं |गेहूँ|चावल|धान|sugar|pulses|atta)\b",
        full_text,
        re.IGNORECASE,
    )

    return {
        "challan_number": challan_match.group(1) if challan_match else None,
        "date": date_match.group(1) if date_match else None,
        "commodity": commodity_match.group(1).strip() if commodity_match else None,
        "quantity_kg": float(quantity_match.group(1)) if quantity_match else None,
        "needs_review": True,
    }


@router.post("/receipt-ocr")
async def scan_receipt(file: UploadFile = File(...)):
    """Image upload karke OCR text aur extracted fields return karta hai."""

    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(
            status_code=400,
            detail="Please upload a JPG, PNG, or WEBP image.",
        )

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller.")

    temp_path = None

    try:
        with Image.open(__import__("io").BytesIO(content)) as image:
            image.verify()

        suffix = Path(file.filename or "receipt.jpg").suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            suffix = ".jpg"

        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        result = ocr_engine.ocr(temp_path, cls=True)

        words = []
        if result and result[0]:
            for item in result[0]:
                if len(item) > 1 and item[1]:
                    words.append(item[1][0])

        extracted_text = "\n".join(words)

        return {
            "success": True,
            "extracted_text": extracted_text,
            "fields": extract_fields(extracted_text),
            "message": "Verify extracted fields before updating inventory.",
        }

    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="Invalid or unreadable image.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {exc}")
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)