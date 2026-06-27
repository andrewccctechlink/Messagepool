"""
Quattro Message Pool — Direct Gemini Client (httpx version)
Calls Gemini 2.5 Flash REST API directly — no grpc, no google-generativeai SDK.
Works on Device Guard-locked machines (pure Python, no compiled DLLs).
"""

import json
import uuid
from datetime import datetime, timezone

import httpx

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

EXTRACTION_PROMPT = """\
You are a B2B procurement data extraction specialist. Parse messy procurement communications (WhatsApp chats, WeChat messages, emails, quotation documents) and extract structured product/pricing information.

INSTRUCTIONS:
1. Read the provided text carefully.
2. Extract EVERY distinct product quotation or pricing mention.
3. For each item, extract: product name, unit price, currency, vendor/supplier name, price validity period, quantity mentioned, and minimum order quantity (MOQ).
4. If a field is not mentioned, set it to null.
5. Provide a 1-2 sentence summary of the overall procurement context.

OUTPUT FORMAT — respond with ONLY valid JSON, no markdown fences:
{
  "items": [
    {
      "product": "Product name/model",
      "price": 12.50,
      "currency": "USD",
      "vendor": "Supplier Co Ltd",
      "validity": "Valid until 2026-07-31",
      "quantity": "1000 pcs",
      "moq": "500 pcs",
      "raw_snippet": "The exact sentence(s) from the input that contain this info"
    }
  ],
  "summary": "Brief summary of the procurement context"
}

EXAMPLES:

Input: "Hi, we can offer the 5L air fryer model AF-500 at USD 18.50/pc FOB Shenzhen. MOQ 1000pcs. Price valid till end of August."
Output:
{
  "items": [{"product": "5L Air Fryer AF-500", "price": 18.50, "currency": "USD", "vendor": null, "validity": "Valid until end of August", "quantity": null, "moq": "1000 pcs", "raw_snippet": "we can offer the 5L air fryer model AF-500 at USD 18.50/pc FOB Shenzhen. MOQ 1000pcs. Price valid till end of August."}],
  "summary": "Quotation for a 5L air fryer at USD 18.50/pc FOB Shenzhen."
}

Input: "Morning! Kitchen Master offers the toaster KM-T200 at $12.80 and the kettle KM-K100 at $8.90, both USD, 500pc MOQ. Also GreenHome quoted bamboo cutting board set at EUR 6.20/set, MOQ 2000."
Output:
{
  "items": [
    {"product": "Toaster KM-T200", "price": 12.80, "currency": "USD", "vendor": "Kitchen Master", "validity": null, "quantity": null, "moq": "500 pcs", "raw_snippet": "Kitchen Master offers the toaster KM-T200 at $12.80"},
    {"product": "Kettle KM-K100", "price": 8.90, "currency": "USD", "vendor": "Kitchen Master", "validity": null, "quantity": null, "moq": "500 pcs", "raw_snippet": "the kettle KM-K100 at $8.90, both USD, 500pc MOQ"},
    {"product": "Bamboo Cutting Board Set", "price": 6.20, "currency": "EUR", "vendor": "GreenHome", "validity": null, "quantity": null, "moq": "2000 sets", "raw_snippet": "GreenHome quoted bamboo cutting board set at EUR 6.20/set, MOQ 2000"}
  ],
  "summary": "Comparison of quotes from Kitchen Master (toaster + kettle in USD) and GreenHome (bamboo cutting board set in EUR)."
}

Now extract from the following procurement text:
"""


def analyze_direct(api_key: str, text: str, source_type: str = "document") -> dict:
    """
    Call Gemini 2.5 Flash directly via REST API to analyze procurement text.
    Returns same format as the Zeabur backend /api/v1/analyze response.
    """
    prompt = EXTRACTION_PROMPT + text

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 8192,
        }
    }

    response = httpx.post(
        GEMINI_API_URL,
        headers={"x-goog-api-key": api_key},
        json=payload,
        timeout=60.0,
    )
    response.raise_for_status()

    result = response.json()
    raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Strip markdown fences if present
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw_text = "\n".join(lines)

    parsed = json.loads(raw_text)

    items = []
    for item_data in parsed.get("items", []):
        items.append({
            "product": item_data.get("product", "Unknown"),
            "price": item_data.get("price"),
            "currency": item_data.get("currency"),
            "vendor": item_data.get("vendor"),
            "validity": item_data.get("validity"),
            "quantity": item_data.get("quantity"),
            "moq": item_data.get("moq"),
            "raw_snippet": item_data.get("raw_snippet", ""),
        })

    return {
        "request_id": str(uuid.uuid4()),
        "items": items,
        "summary": parsed.get("summary", f"Extracted {len(items)} item(s) from {source_type} source."),
        "source_type": source_type,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
