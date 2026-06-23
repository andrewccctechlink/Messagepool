"""
Quattro Message Pool — Email Parser
Handles .eml and .msg files, extracts body + all attachments.
"""
import email
import os
import re
import tempfile
from email import policy


PARSEABLE_EXTS = (".pdf", ".xlsx", ".xls", ".csv", ".pptx", ".docx", ".txt", ".jpg", ".jpeg", ".png")


def _parse_attachment(data: bytes, filename: str, api_key: str = None) -> str:
    """Save attachment to temp file and parse it."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in PARSEABLE_EXTS:
        return f"[Attachment: {filename} — unsupported format, skipped]"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(data)
    tmp.close()

    try:
        from file_parser import parse_file
        text, _ = parse_file(tmp.name, api_key=api_key)
        return f"=== Attachment: {filename} ===\n{text}"
    except Exception as e:
        return f"[Attachment: {filename} — parse error: {e}]"
    finally:
        os.unlink(tmp.name)


def parse_eml_full(filepath: str, api_key: str = None) -> str:
    """Parse .eml file: extract headers, body, and all attachments."""
    with open(filepath, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    parts = []

    # Headers
    for h in ("From", "To", "Cc", "Subject", "Date"):
        val = msg.get(h)
        if val:
            parts.append(f"{h}: {val}")
    parts.append("---")

    # Body
    body = msg.get_body(preferencelist=("plain", "html"))
    if body:
        content = body.get_content()
        if body.get_content_type() == "text/html":
            content = re.sub(r"<[^>]+>", "", content)
            content = re.sub(r"&nbsp;", " ", content)
            content = re.sub(r"\n\s*\n", "\n", content)
        parts.append(content.strip())

    # Attachments
    for attachment in msg.iter_attachments():
        filename = attachment.get_filename() or "unnamed"
        data = attachment.get_content()
        if isinstance(data, str):
            data = data.encode("utf-8")
        parts.append(_parse_attachment(data, filename, api_key))

    return "\n\n".join(parts)


def parse_msg_full(filepath: str, api_key: str = None) -> str:
    """Parse .msg file: extract headers, body, and all attachments."""
    try:
        import extract_msg
    except ImportError:
        raise RuntimeError("Install extract-msg: pip install extract-msg")

    msg = extract_msg.Message(filepath)
    parts = []

    # Headers
    if msg.sender:
        parts.append(f"From: {msg.sender}")
    if msg.to:
        parts.append(f"To: {msg.to}")
    if msg.subject:
        parts.append(f"Subject: {msg.subject}")
    if msg.date:
        parts.append(f"Date: {msg.date}")
    parts.append("---")

    # Body
    if msg.body:
        parts.append(msg.body.strip())

    # Attachments
    for att in msg.attachments:
        filename = att.longFilename or att.shortFilename or "unnamed"
        data = att.data
        if data:
            parts.append(_parse_attachment(data, filename, api_key))

    msg.close()
    return "\n\n".join(parts)
