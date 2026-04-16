"""
OCR service — extract text from photos using Tesseract or Google Vision.
"""

import pytesseract
from PIL import Image
import io
import base64
from config import settings

# Google Vision imports (optional)
try:
    from google.cloud import vision as google_vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False


async def extract_text_from_photo(photo_b64: str) -> str:
    """
    Extract text from a base64-encoded image using Tesseract (or Google Vision if configured).

    Args:
        photo_b64: Base64-encoded image data.

    Returns:
        Extracted text string.
    """
    # Decode base64 to image
    photo_data = base64.b64decode(photo_b64)
    image = Image.open(io.BytesIO(photo_data))

    # Use Google Vision if API key is provided, otherwise use Tesseract
    if settings.google_vision_api_key and GOOGLE_VISION_AVAILABLE:
        return await _extract_with_google_vision(photo_b64)
    else:
        return await _extract_with_tesseract(image)


async def _extract_with_tesseract(image: Image.Image) -> str:
    """Extract text using Tesseract OCR."""
    try:
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        print(f"[ERROR] Tesseract OCR failed: {e}")
        return ""


async def _extract_with_google_vision(photo_b64: str) -> str:
    """Extract text using Google Cloud Vision API."""
    if not GOOGLE_VISION_AVAILABLE:
        print("[WARN] Google Vision not available; install: pip install google-cloud-vision")
        return ""

    try:
        client = google_vision.ImageAnnotatorClient()
        image = google_vision.Image(content=base64.b64decode(photo_b64))
        response = client.document_text_detection(image=image)
        
        if response.text_annotations:
            return response.text_annotations[0].description
        return ""
    except Exception as e:
        print(f"[ERROR] Google Vision OCR failed: {e}")
        return ""
