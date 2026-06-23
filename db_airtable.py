"""Airtable backend for Message Pool — survives Zeabur redeploys.
ROBUST v2: all filtering/sorting done in Python (avoids Airtable param validation errors).
"""
import os
import hashlib
import secrets
import requests

# ── Config ──
AIRTABLE_TOKEN = ***"AIRTABLE_TOKEN", "")
BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "appmMvxwqWtH4PMer")
TABLE_ANALYSES = "Message Pool Analyses"
TABLE_ITEMS = "Message Pool Items"
TABLE_USERS = "Message Pool Users"

def _ah():
    return {"Authorization": f"Bearer {AIRTABLE_TOKEN}", "Content-Type": "application/json"}

# ── Low-level helpers (no filterByFormula, no sort — all Python-side) ──────

def _at_fetch(table, **params):
    """Fetch ALL records from a table (handles pagination). No Airtable filters."""
    all_records = []
    offset = None
    while True:
        p = dict(params)
        if offset:
            p["offset"] = offset
        r = requests.get(
            f"https://api.airtable.com/v0/{BASE_ID}/{table}",
            headers=_ah(), params=p, timeout=25
        )
        if not r.ok:
            print(f"⚠️ Airtable GET {table}: {r.status_code}")
            return []
        data = r.json()
        all_records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return all_records

def _at_create(table, fields):
    """Create one record. Returns Airtable response or None."""
    r = requests.post(
        f"https://api.airtable.com/v0/{BASE_ID}/{table}",
        headers=_ah(), json={"fields": fields}, timeout=20
    )
    if not r.ok:
        print(f"⚠️ Airtable CREATE {table}: {r.status_code} {r.text[:200]}")
        return None
    return r.json()

# ── Init ────────────────────────────────────────────────────────────────────

def init_db(db_path=None):
    """No-op: Airtable doesn't need init."""
    pass

def get_conn(db_path=None):
    return None

# ── User Auth ───────────────────────────────────────────────────────────────

def _hash_pw(password):
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"

def _check_pw(password, stored):
    try:
        salt, h = stored.split(":", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == h
    except Exception:
        return False

def create_user(username, password, display_name=None, is_admin=0, db_path=None):
    """Create user. Returns True/False."""
    # Check if exists (fetch all, filter in Python)
    existing = _at_fetch(TABLE_USERS)
    for r in existing:
        f = r.get("fields", {})
        if (f.get("Username") or "").lower().strip() == username.lower().strip():
            return False
    result = _at_create(TABLE_USERS, {
        "Username": username.lower().strip(),
        "PasswordHash": _hash_pw(password),
        "DisplayName": display_name or username,
        "IsAdmin": is_admin
    })
    return result is not None

def verify_user(username, password, db_path=None):
    """Verify login. Returns user dict or None."""
    records = _at_fetch(TABLE_USERS)
    uname = username.lower().strip()
    for r in records:
        f = r.get("fields", {})
        if (f.get("Username") or "").lower().strip() == uname:
            if _check_pw(password, f.get("PasswordHash", "")):
                return {
                    "id": f.get("Username", uname),
                    "username": f.get("Username", uname),
                    "display_name": f.get("DisplayName", username),
                    "is_admin": bool(f.get("IsAdmin", 0))
                }
    return None

def list_users(db_path=None):
    """List all users."""
    records = _at_fetch(TABLE_USERS)
    users = []
    for r in records:
        f = r.get("fields", {})
        users.append({
            "id": f.get("Username", ""),
            "username": f.get("Username", ""),
            "display_name": f.get("DisplayName", ""),
            "is_admin": bool(f.get("IsAdmin", 0)),
            "created_at": r.get("createdTime", "")
        })
    users.sort(key=lambda u: u["username"])
    return users

# ── Analysis & Items ────────────────────────────────────────────────────────

def save_analysis(request_id, source_type, summary, items, raw_text, user_id=None, source_name=None, db_path=None):
    """Save analysis + items to Airtable. Returns request_id."""
    ana = _at_create(TABLE_ANALYSES, {
        "RequestID": request_id,
        "SourceType": source_type,
        "SourceName": source_name or "Unknown",
        "Summary": summary or "",
        "RawText": (raw_text or "")[:4000],
        "ItemCount": len(items)
    })
    if not ana:
        return None
    for item in items:
        _at_create(TABLE_ITEMS, {
            "RequestID": request_id,
            "Product": item.get("product", "Unknown"),
            "Price": item.get("price"),
            "Currency": item.get("currency", ""),
            "Vendor": item.get("vendor", ""),
            "Validity": item.get("validity", ""),
            "Quantity": str(item.get("quantity", "")),
            "MOQ": str(item.get("moq", "")),
            "RawSnippet": (item.get("raw_snippet", "") or "")[:2000],
            "SourceName": source_name or ""
        })
    return request_id

def search_items(query, user_id=None, db_path=None):
    """Search items (Python-side filtering)."""
    items = _at_fetch(TABLE_ITEMS)
    results = []
    for r in items:
        f = r.get("fields", {})
        entry = {
            "id": f.get("RequestID", ""),
            "product": f.get("Product", "Unknown"),
            "price": f.get("Price"),
            "currency": f.get("Currency", ""),
            "vendor": f.get("Vendor", ""),
            "validity": f.get("Validity", ""),
            "quantity": str(f.get("Quantity", "")),
            "moq": str(f.get("MOQ", "")),
            "raw_snippet": f.get("RawSnippet", ""),
            "source_type": "airtable",
            "source_name": f.get("SourceName", ""),
            "date_received": r.get("createdTime", "")
        }
        results.append(entry)
    
    # Filter in Python
    import re
    q = query.strip().lower()
    filtered = []
    for item in results:
        searchable = f"{item.get('product','')} {item.get('vendor','')} {item.get('raw_snippet','')}".lower()
        if q in searchable:
            filtered.append(item)
    filtered.sort(key=lambda x: x.get("date_received", ""), reverse=True)
    return filtered[:200]

def get_history(user_id=None, limit=50, offset=0, db_path=None):
    """Get analysis history (Python-side sorting)."""
    records = _at_fetch(TABLE_ANALYSES)
    results = []
    for r in records:
        f = r.get("fields", {})
        results.append({
            "id": f.get("RequestID", ""),
            "source_type": f.get("SourceType", ""),
            "source_name": f.get("SourceName", ""),
            "summary": f.get("Summary", ""),
            "raw_text": f.get("RawText", ""),
            "item_count": f.get("ItemCount", 0),
            "uploaded_by": "user",
            "created_at": r.get("createdTime", ""),
            "request_id": f.get("RequestID", "")
        })
    results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return results[offset:offset + limit]

def get_stats(user_id=None, db_path=None):
    """Get summary stats."""
    analyses = _at_fetch(TABLE_ANALYSES)
    items = _at_fetch(TABLE_ITEMS)
    last = None
    if analyses:
        # Find newest by Airtable createdTime
        times = [r.get("createdTime", "") for r in analyses]
        last = max(times) if times else None
    return {
        "total_analyses": len(analyses),
        "total_items": len(items),
        "last_analysis": last
    }
