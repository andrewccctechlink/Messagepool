#!/usr/bin/env python3
"""Setup Airtable tables for Message Pool persistent storage.
Run once before deploying db_airtable backend.
Usage: python airtable_message_pool_setup.py
"""
import os
import requests
import json

AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN", "")
BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "appmMvxwqWtH4PMer")

if not AIRTABLE_TOKEN:
    print("❌ AIRTABLE_TOKEN environment variable not set!")
    print("   Set it: export AIRTABLE_TOKEN='pat...'")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

def get_existing_tables():
    r = requests.get(f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables", headers=HEADERS, timeout=15)
    if not r.ok:
        print(f"❌ Cannot access base {BASE_ID}: {r.status_code} {r.text[:200]}")
        exit(1)
    return {t["name"]: t["id"] for t in r.json().get("tables", [])}

def create_table(name, fields, description=""):
    """Create a table via Airtable Metadata API."""
    payload = {
        "name": name,
        "description": description,
        "fields": fields
    }
    r = requests.post(
        f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables",
        headers=HEADERS,
        json=payload,
        timeout=15
    )
    if r.ok:
        data = r.json()
        print(f"   ✅ Created '{name}' (id: {data['id']})")
        return True
    else:
        print(f"   ❌ Failed to create '{name}': {r.status_code} {r.text[:300]}")
        return False

def main():
    print(f"🔧 Setting up Message Pool Airtable tables in base {BASE_ID}...\n")

    existing = get_existing_tables()
    print(f"   Existing tables: {list(existing.keys())}\n")

    tables_needed = {
        "Message Pool Analyses": {
            "description": "Quattro Message Pool — analysis records (uploaded documents, emails, pasted text)",
            "fields": [
                {"name": "RequestID", "type": "singleLineText"},
                {"name": "SourceType", "type": "singleLineText"},
                {"name": "SourceName", "type": "singleLineText"},
                {"name": "Summary", "type": "multilineText"},
                {"name": "RawText", "type": "multilineText"},
                {"name": "ItemCount", "type": "number", "options": {"precision": 0}},
                {"name": "UserID", "type": "singleLineText"},
                {"name": "CreatedAt", "type": "singleLineText"}
            ]
        },
        "Message Pool Items": {
            "description": "Quattro Message Pool — extracted line items (products, prices, vendors)",
            "fields": [
                {"name": "RequestID", "type": "singleLineText"},
                {"name": "Product", "type": "singleLineText"},
                {"name": "Price", "type": "number", "options": {"precision": 2}},
                {"name": "Currency", "type": "singleLineText"},
                {"name": "Vendor", "type": "singleLineText"},
                {"name": "Validity", "type": "singleLineText"},
                {"name": "Quantity", "type": "singleLineText"},
                {"name": "MOQ", "type": "singleLineText"},
                {"name": "RawSnippet", "type": "multilineText"},
                {"name": "SourceName", "type": "singleLineText"},
                {"name": "UserID", "type": "singleLineText"},
                {"name": "CreatedAt", "type": "singleLineText"}
            ]
        },
        "Message Pool Users": {
            "description": "Quattro Message Pool — user accounts",
            "fields": [
                {"name": "Username", "type": "singleLineText"},
                {"name": "PasswordHash", "type": "singleLineText"},
                {"name": "DisplayName", "type": "singleLineText"},
                {"name": "IsAdmin", "type": "number", "options": {"precision": 0}},
                {"name": "CreatedAt", "type": "singleLineText"}
            ]
        }
    }

    created = 0
    for name, config in tables_needed.items():
        if name in existing:
            print(f"   ⏭️  '{name}' already exists — skipping")
        else:
            if create_table(name, config["fields"], config.get("description", "")):
                created += 1

    print(f"\n✅ Done! {created} table(s) created.")
    if created > 0:
        print("   You can now set DB_BACKEND=airtable and redeploy Message Pool.")

if __name__ == "__main__":
    main()
