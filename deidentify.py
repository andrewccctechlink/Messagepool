"""
Quattro Message Pool — PII De-identification Layer
Strips personally identifiable information before sending text to the cloud AI.
Keeps product names, prices, quantities, and company names intact.
"""

import re
from typing import Optional


def deidentify(text: str) -> tuple[str, list[dict]]:
    """
    Remove PII from procurement text.

    Returns:
        (cleaned_text, removals) where removals is a list of
        {"type": str, "original": str, "replacement": str, "position": int}
    """
    removals: list[dict] = []
    result = text

    # Order matters: process from most specific to least specific

    # 1. Email addresses
    result, r = _strip_pattern(
        result,
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "[EMAIL]",
        "email",
    )
    removals.extend(r)

    # 2. URLs
    result, r = _strip_pattern(
        result,
        r'https?://[^\s<>\"\')\]]+',
        "[URL]",
        "url",
    )
    removals.extend(r)

    # 3. Credit card numbers (13-19 digits with optional separators)
    result, r = _strip_pattern(
        result,
        r'\b(?:\d{4}[\s-]?){3,4}\d{1,4}\b',
        "[CARD]",
        "credit_card",
    )
    removals.extend(r)

    # 4. Phone numbers — international formats
    # +852 XXXX XXXX, +86 1XX XXXX XXXX, +1 (XXX) XXX-XXXX, etc.
    phone_patterns = [
        r'\+?\d{1,3}[\s-]?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}',  # General international
        r'\+852[\s-]?\d{4}[\s-]?\d{4}',  # Hong Kong
        r'\+86[\s-]?1\d{2}[\s-]?\d{4}[\s-]?\d{4}',  # China mobile
        r'\+1[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}',  # US/Canada
        r'\b0\d{2,3}[\s-]?\d{3,4}[\s-]?\d{3,4}\b',  # Local with area code
    ]
    for pattern in phone_patterns:
        result, r = _strip_pattern(result, pattern, "[PHONE]", "phone")
        removals.extend(r)

    # 5. Addresses — street numbers and zip/postal codes
    # Partial: won't catch everything but handles common patterns
    result, r = _strip_pattern(
        result,
        r'\b\d{1,5}\s+(?:(?:N|S|E|W|North|South|East|West|St|Ave|Rd|Blvd|Dr|Ln|Ct|Pl|Way|Street|Avenue|Road|Boulevard|Drive|Lane|Court|Place)\b[^,\n]{0,60})',
        "[ADDRESS]",
        "address",
    )
    removals.extend(r)

    # Zip/postal codes (US, UK, HK, etc.)
    result, r = _strip_pattern(
        result,
        r'\b[A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2}\b',  # UK
        "[POSTAL]",
        "postal_code",
    )
    removals.extend(r)

    # 6. Common personal name patterns (conservative — only obvious ones)
    # Names after greeting words
    result, r = _strip_pattern(
        result,
        r'(?:(?:Dear|Hi|Hello|Hey|Mr\.?|Mrs\.?|Ms\.?|Miss|Dr\.?)\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})',
        lambda m: m.group(0).split()[0] + " [PERSON]",
        "person_name",
    )
    removals.extend(r)

    # "My name is ..."  /  "I'm ... from"
    result, r = _strip_pattern(
        result,
        r"(?:(?:my name is|I'm|I am)\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        lambda m: m.group(0).replace(m.group(1), "[PERSON]"),
        "person_name",
    )
    removals.extend(r)

    # "Contact: Name" patterns
    result, r = _strip_pattern(
        result,
        r'(?:contact|attn|attention|from|sender|buyer|purchasing)\s*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})',
        lambda m: m.group(0).replace(m.group(1), "[PERSON]"),
        "person_name",
    )
    removals.extend(r)

    return result, removals


def _strip_pattern(
    text: str,
    pattern: str,
    replacement,
    pii_type: str,
) -> tuple[str, list[dict]]:
    """Apply a regex pattern and collect removals."""
    removals = []
    compiled = re.compile(pattern, re.IGNORECASE)

    def replacer(match):
        original = match.group(0)
        # Skip if it looks like a price (contains $ € £ ¥ followed by digits)
        if pii_type == "credit_card":
            stripped = re.sub(r'[\s-]', '', original)
            if len(stripped) < 13:
                return original  # Too short, probably a date or order number

        if callable(replacement):
            rep = replacement(match)
        else:
            rep = replacement

        removals.append({
            "type": pii_type,
            "original": original,
            "replacement": rep,
            "position": match.start(),
        })
        return rep

    result = compiled.sub(replacer, text)
    return result, removals


def get_removal_summary(removals: list[dict]) -> str:
    """Generate a human-readable summary of what was removed."""
    if not removals:
        return "No PII detected."

    counts: dict[str, int] = {}
    for r in removals:
        counts[r["type"]] = counts.get(r["type"], 0) + 1

    labels = {
        "email": "email address",
        "phone": "phone number",
        "url": "URL",
        "credit_card": "credit card number",
        "address": "street address",
        "postal_code": "postal code",
        "person_name": "personal name",
    }

    parts = []
    for pii_type, count in counts.items():
        label = labels.get(pii_type, pii_type)
        if count > 1:
            label += "s" if not label.endswith("s") else "es"
        parts.append(f"{count} {label}")

    return f"Removed: {', '.join(parts)}"
