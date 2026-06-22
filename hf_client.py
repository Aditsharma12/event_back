import os
import logging
import requests
from fastapi import UploadFile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HF_URL = os.getenv("HF_URL", "https://adit1sharma-acc-api.hf.space/api/v1/incidents/analyze")
HF_TOKEN = os.getenv("HF_TOKEN", "")

def analyze_image(image: UploadFile) -> dict:
    """
    Calls the Hugging Face Space endpoint to analyze an uploaded image.
    """
    if not HF_URL or HF_URL.startswith("YOUR_"):
        logger.error("HF_URL not configured.")
        raise ValueError("HF_URL not configured.")

    headers = {}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"

    # Ensure the file pointer is at the beginning
    image.file.seek(0)
    
    content_type = image.content_type
    if not content_type or not content_type.startswith("image/"):
        filename = (image.filename or "").lower()
        if filename.endswith(".png"):
            content_type = "image/png"
        elif filename.endswith((".jpg", ".jpeg")):
            content_type = "image/jpeg"
        elif filename.endswith(".gif"):
            content_type = "image/gif"
        else:
            content_type = "image/jpeg"  # Safe default fallback

    files = {
        "file": (
            image.filename,
            image.file,
            content_type
        )
    }

    try:
        logger.info(f"Sending image {image.filename} to Hugging Face API: {HF_URL}")
        response = requests.post(
            HF_URL,
            headers=headers,
            files=files,
            timeout=30  # Grounding DINO on CPU can take a few seconds
        )
        if not response.ok:
            logger.error(f"Hugging Face API Error Response: {response.text}")
        response.raise_for_status()
        
        result = response.json()
        logger.info("Successfully received analysis from Hugging Face API")
        return result
        
    except Exception as e:
        logger.error(f"Failed to communicate with Hugging Face Space: {str(e)}")
        raise e
