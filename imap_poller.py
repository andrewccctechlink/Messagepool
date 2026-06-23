"""IMAP Auto-Poller — checks email inbox periodically and auto-analyzes."""
import imaplib
import email as email_lib
import os
import tempfile
import threading
import time
import uuid
from email import policy
from datetime import datetime, timezone

from file_parser import parse_file
from gemini_direct import analyze_direct

# Use same DB backend as server
# Use same DB backend as server
AIRTABLE_TOKEN = (lambda: __import__('os').environ.get('AIRTABLE_TOKEN', ''))()
if AIRTABLE_TOKEN:
    from db_airtable import save_analysis
else:
    from db import save_analysis


class IMAPPoller:
    def __init__(self, config, db_path):
        self.config = config
        self.db_path = db_path
        self.running = False
        self.thread = None
        self.last_check = None
        self.last_error = None
        self.processed_count = 0

    def start(self):
        if not self.config.get("enabled"):
            return
        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def status(self):
        return {
            "running": self.running,
            "last_check": self.last_check,
            "last_error": self.last_error,
            "processed_count": self.processed_count,
        }

    def _poll_loop(self):
        interval = self.config.get("poll_interval_minutes", 5) * 60
        while self.running:
            try:
                self._check_inbox()
                self.last_error = None
            except Exception as e:
                self.last_error = str(e)
            time.sleep(interval)

    def _check_inbox(self):
        cfg = self.config
        mail = imaplib.IMAP4_SSL(cfg["server"], cfg.get("port", 993))
        mail.login(cfg["email"], cfg["password"])
        mail.select(cfg.get("folder", "INBOX"))

        _, data = mail.search(None, "UNSEEN")
        msg_ids = data[0].split()

        for msg_id in msg_ids:
            _, msg_data = mail.fetch(msg_id, "(RFC822)")
            raw = msg_data[0][1]
            self._process_email(raw)
            self.processed_count += 1

        mail.logout()
        self.last_check = datetime.now(timezone.utc).isoformat()

    def _process_email(self, raw_bytes):
        msg = email_lib.message_from_bytes(raw_bytes, policy=policy.default)
        subject = msg.get("Subject", "No Subject")
        sender = msg.get("From", "Unknown")

        # Save as temp .eml and parse
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".eml")
        tmp.write(raw_bytes)
        tmp.close()

        try:
            gemini_key = self.config.get("gemini_api_key", "")
            text, ftype = parse_file(tmp.name, api_key=gemini_key)

            if text and len(text.strip()) > 20:
                result = analyze_direct(gemini_key, text, ftype)
                save_analysis(
                    request_id=result["request_id"],
                    source_type=ftype,
                    source_name=f"[Auto] {subject} — from {sender}",
                    summary=result.get("summary", ""),
                    items=result.get("items", []),
                    raw_text=text,
                    db_path=self.db_path,
                )
        finally:
            os.unlink(tmp.name)
