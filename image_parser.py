"""
Quattro Message Pool — Image Parser via Gemini Vision API
Sends image as base64 to Gemini for text/pricing extraction.
Works with screenshots, photos of documents, WhatsApp captures, etc.
"""
import base64
import os
import httpx

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

IMAGE_PROMPT = """\
Extract ALL text from this image. This is a procurement/business document or chat screenshot.
Focus on:
- Product names, model numbers
- Prices, currencies, payment terms
- Vendor/supplier names
- Quantities, MOQ
- Contact info
- Any dates or validity periods

Return the extracted text in a structured, readable format.
If it's a chat screenshot, preserve the conversation flow with sender names.
"""


def parse_image(filepath: str, api_key: str = None) -> str:
    """
    Send image to Gemini Vision API for text extraction.
    Returns extracted text content.
    """
    if not api_key:
        raise ValueError("Gemini API key required for image parsing. Set it in Settings.")

    # Read and encode image
    ext = os.path.splitext(filepath)[1].lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    mime_type = mime_map.get(ext, "image/jpeg")

    with open(filepath, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    payload = {
        "contents": [{
            "parts": [
                {"text": IMAGE_PROMPT},
                {"inline_data": {"mime_type": mime_type, "data": image_data}}
            ]
        }],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192}
    }

    response = httpx.post(
        GEMINI_API_URL,
        headers={"x-goog-api-key": api_key},
        json=payload,
        timeout=60.0,
    )
    response.raise_for_status()

    result = response.json()
    text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
    return text
