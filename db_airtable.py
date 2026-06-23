"""Airtable backend for Message Pool — survives Zeabur redeploys."""
import os
import json
import uuid
import hashlib
import secrets
import requests
from datetime import datetime, timezone

# ── Config ──────────────────────────────────────────────────────────────────
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN", "")
BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "appmMvxwqWtH4PMer")
TABLE_ANALYSES = "Message Pool Analyses"
TABLE_ITEMS = "Message Pool Items"
TABLE_USERS = "Message Pool Users"

def _ah():
    return {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    }

# ── Low-level Airtable helpers ──────────────────────────────────────────────

def _at_get(table, **params):
    """Fetch records from Airtable (handles pagination)."""
    all_records = []
    offset = None
    while True:
        p = dict(params)
        if offset:
            p["offset"] = offset
        r = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/{table}", headers=_ah(), params=p, timeout=20)
        if not r.ok:
            print(f"⚠️ Airtable GET {table}: {r.status_code} {r.text[:200]}")
            return []
        data = r.json()
        all_records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return all_records

def _at_create(table, fields):
    """Create one record."""
    r = requests.post(
        f"https://api.airtable.com/v0/{BASE_ID}/{table}",
        headers=_ah(),
        json={"fields": fields},
        timeout=20
    )
    if not r.ok:
        print(f"⚠️ Airtable CREATE {table}: {r.status_code} {r.text[:200]}")
        return None
    return r.json()

def _at_update(table, record_id, fields):
    """Patch one record."""
    r = requests.patch(
        f"https://api.airtable.com/v0/{BASE_ID}/{table}/{record_id}",
        headers=_ah(),
        json={"fields": fields},
        timeout=20
    )
    if not r.ok:
        print(f"⚠️ Airtable UPDATE {table}: {r.status_code} {r.text[:200]}")
        return None
    return r.json()

def _at_delete(table, record_id):
    r = requests.delete(
        f"https://api.airtable.com/v0/{BASE_ID}/{table}/{record_id}",
        headers=_ah(),
        timeout=20
    )
    return r.ok

def _at_clear(table):
    """Delete all records in a table (batch delete, max 10 per call)."""
    records = _at_get(table, maxRecords=500)
    ids = [r["id"] for r in records]
    for i in range(0, len(ids), 10):
        batch = ids[i:i+10]
        params = "&".join([f"records[]={rid}" for rid in batch])
        r = requests.delete(
            f"https://api.airtable.com/v0/{BASE_ID}/{table}?{params}",
            headers=_ah(),
            timeout=20
        )
        if not r.ok:
            print(f"⚠️ Airtable DELETE batch: {r.status_code}")


# ── Ensure tables exist ─────────────────────────────────────────────────────

def _ensure_tables():
    """Create Airtable tables if they don't exist. Uses Metadata API."""
    try:
        r = requests.get(
            f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables",
            headers=_ah(),
            timeout=15
        )
        if not r.ok:
            print(f"⚠️ Cannot check tables: {r.status_code}")
            return
        existing = [t["name"] for t in r.json().get("tables", [])]
        print(f"   Airtable tables found: {existing}")

        if TABLE_ANALYSES not in existing:
            print(f"⚠️ Table '{TABLE_ANALYSES}' NOT FOUND! Run airtable_message_pool_setup.py first.")
        if TABLE_ITEMS not in existing:
            print(f"⚠️ Table '{TABLE_ITEMS}' NOT FOUND! Run airtable_message_pool_setup.py first.")
        if TABLE_USERS not in existing:
            print(f"⚠️ Table '{TABLE_USERS}' NOT FOUND! Run airtable_message_pool_setup.py first.")
    except Exception as e:
        print(f"⚠️ Airtable metadata check failed: {e}")


# ── User Auth (Airtable-backed) ─────────────────────────────────────────────

def init_db(db_path=None):
    """Ensure Airtable tables are reachable. Sync compatibility with sqlite init_db()."""
    _ensure_tables()

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
    """Create user in Airtable. Returns True/False."""
    # Check if exists
    existing = _at_get(TABLE_USERS, filterByFormula=f"LOWER({{Username}})='{username.lower().strip()}'")
    if existing:
        return False
    result = _at_create(TABLE_USERS, {
        "Username": username.lower().strip(),
        "PasswordHash": _hash_pw(password),
        "DisplayName": display_name or username,
        "IsAdmin": is_admin,
        "CreatedAt": datetime.now(timezone.utc).isoformat()
    })
    return result is not None

def verify_user(username, password, db_path=None):
    """Verify login. Returns user dict or None."""
    records = _at_get(TABLE_USERS, filterByFormula=f"LOWER({{Username}})='{username.lower().strip()}'")
    if not records:
        return None
    rec = records[0]
    fields = rec["fields"]
    if _check_pw(password, fields.get("PasswordHash", "")):
        return {
            "id": fields.get("Username"),
            "username": fields.get("Username"),
            "display_name": fields.get("DisplayName", username),
            "is_admin": bool(fields.get("IsAdmin", 0))
        }
    return None

def list_users(db_path=None):
    """List all users."""
    records = _at_get(TABLE_USERS, sort=[{"field": "Username", "direction": "asc"}])
    return [
        {
            "id": r["fields"].get("Username"),
            "username": r["fields"].get("Username"),
            "display_name": r["fields"].get("DisplayName", ""),
            "is_admin": bool(r["fields"].get("IsAdmin", 0)),
            "created_at": r["fields"].get("CreatedAt", "")
        }
        for r in records
    ]


# ── Analysis & Items (Airtable-backed) ──────────────────────────────────────

def save_analysis(request_id, source_type, summary, items, raw_text, user_id=None, source_name=None, db_path=None):
    """Save analysis + items to Airtable. Returns analysis record id."""
    now = datetime.now(timezone.utc).isoformat()
    ana = _at_create(TABLE_ANALYSES, {
        "RequestID": request_id,
        "SourceType": source_type,
        "SourceName": source_name or "Unknown",
        "Summary": summary or "",
        "RawText": raw_text[:4000] if raw_text else "",  # Airtable cell limit ~100KB, keep safe
        "ItemCount": len(items),
        "UserID": user_id or "anonymous",
        "CreatedAt": now
    })
    if not ana:
        return None

    # Create items
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
            "SourceName": source_name or "",
            "UserID": user_id or "anonymous",
            "CreatedAt": now
        })
    return request_id

def search_items(query, user_id=None, db_path=None):
    """Search items by product/vendor/price range. Airtable has limited search, so fetch all and filter."""
    items = _get_all_items()
    product_term, price_min, price_max, currency = _parse_price_query(query)

    results = []
    for item in items:
        # Filter by user
        if user_id and item.get("UserID") != user_id:
            continue
        # Filter by product/vendor keyword
        if product_term:
            prod = (item.get("Product", "") + " " + item.get("Vendor", "") + " " + item.get("RawSnippet", "")).lower()
            if product_term.lower() not in prod:
                continue
        # Price filter
        price = item.get("Price")
        if price is not None:
            if price_min is not None and price < price_min:
                continue
            if price_max is not None and price > price_max:
                continue
        # Currency filter
        if currency:
            if (item.get("Currency") or "").upper() != currency.upper():
                continue
        results.append(item)

    # Sort by created_at desc
    results.sort(key=lambda x: x.get("CreatedAt", ""), reverse=True)
    return results[:200]

def get_history(user_id=None, limit=50, offset=0, db_path=None):
    """Get analysis history."""
    sort_param = [{"field": "CreatedAt", "direction": "desc"}]
    records = _at_get(TABLE_ANALYSES, maxRecords=limit + offset, sort=sort_param)
    results = []
    for r in records[offset:offset + limit]:
        f = r["fields"]
        results.append({
            "id": f.get("RequestID", ""),
            "source_type": f.get("SourceType", ""),
            "source_name": f.get("SourceName", ""),
            "summary": f.get("Summary", ""),
            "raw_text": f.get("RawText", ""),
            "item_count": f.get("ItemCount", 0),
            "uploaded_by": f.get("UserID", ""),
            "created_at": f.get("CreatedAt", ""),
            "request_id": f.get("RequestID", "")
        })
    if user_id:
        results = [r for r in results if r.get("uploaded_by") == user_id]
    return results[:limit]

def get_stats(user_id=None, db_path=None):
    """Get summary stats."""
    analyses = _at_get(TABLE_ANALYSES)
    items = _get_all_items()
    if user_id:
        analyses = [a for a in analyses if a["fields"].get("UserID") == user_id]
        items = [i for i in items if i.get("UserID") == user_id]
    last = max([a["fields"].get("CreatedAt", "") for a in analyses]) if analyses else None
    return {
        "total_analyses": len(analyses),
        "total_items": len(items),
        "last_analysis": last
    }

def _get_all_items():
    """Fetch all items from Airtable (with pagination)."""
    all_items = []
    offset = None
    while True:
        params = {}
        if offset:
            params["offset"] = offset
        r = requests.get(
            f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ITEMS}",
            headers=_ah(),
            params=params,
            timeout=20
        )
        if not r.ok:
            break
        data = r.json()
        for rec in data.get("records", []):
            f = rec["fields"]
            all_items.append({
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
                "date_received": f.get("CreatedAt", ""),
                "UserID": f.get("UserID", ""),
                "CreatedAt": f.get("CreatedAt", "")
            })
        offset = data.get("offset")
        if not offset:
            break
    return all_items


# ── Query parser (copied from db.py to avoid circular import) ───────────────

def _parse_price_query(query):
    import re
    q = query.strip().lower()
    price_min = price_max = currency = product_term = None
    cur_map = {"$":"USD","usd":"USD","eur":"EUR","hk$":"HKD","hkd":"HKD","cny":"CNY","rmb":"CNY"}
    for sym, cur in cur_map.items():
        if sym in q:
            currency = cur; break
    m = re.search(r'(?:less\s+than|under|below|<)\s*\S*?(\d+(?:\.\d+)?)', q)
    if m:
        price_max = float(m.group(1))
        product_term = re.sub(r'(?:less\s+than|under|below|<)\s*\S*?\d+(?:\.\d+)?', '', q).strip()
    if not price_max:
        m = re.search(r'(?:more\s+than|above|over|>)\s*\S*?(\d+(?:\.\d+)?)', q)
        if m:
            price_min = float(m.group(1))
            product_term = re.sub(r'(?:more\s+than|above|over|>)\s*\S*?\d+(?:\.\d+)?', '', q).strip()
    if not price_max and not price_min:
        m = re.search(r'between\s*\S*?(\d+(?:\.\d+)?)\s*(?:and|to|-)\s*\S*?(\d+(?:\.\d+)?)', q)
        if m:
            price_min, price_max = float(m.group(1)), float(m.group(2))
            product_term = re.sub(r'between\s*\S*?\d+.*?\d+(?:\.\d+)?', '', q).strip()
    if product_term:
        for w in list(cur_map.keys()) + list(cur_map.values()):
            product_term = product_term.replace(w.lower(), "").strip()
        product_term = re.sub(r'\s+', ' ', product_term).strip() or None
    if not price_min and not price_max and not product_term:
        product_term = query.strip()
    return product_term, price_min, price_max, currency


# ── Compatibility: same interface as db.py ──────────────────────────────────

def get_conn(db_path=None):
    """Dummy — Airtable doesn't use connections."""
    return None
