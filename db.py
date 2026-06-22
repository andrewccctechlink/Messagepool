"""Database layer — SQLite local storage with multi-user support."""
import sqlite3
import json
import os
import re
import hashlib
import secrets
from datetime import datetime, timezone

DB_PATH = "./data/message_pool.db"


def get_conn(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(db_path=DB_PATH):
    conn = get_conn(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            request_id TEXT UNIQUE NOT NULL,
            source_type TEXT DEFAULT 'document',
            source_name TEXT,
            summary TEXT,
            raw_text TEXT,
            item_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL,
            request_id TEXT NOT NULL,
            product TEXT NOT NULL,
            price REAL,
            currency TEXT,
            vendor TEXT,
            validity TEXT,
            quantity TEXT,
            moq TEXT,
            raw_snippet TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_items_product ON items(product);
        CREATE INDEX IF NOT EXISTS idx_items_vendor ON items(vendor);
        CREATE INDEX IF NOT EXISTS idx_analyses_user ON analyses(user_id);
        CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at);
    """)
    conn.commit()
    conn.close()


def _hash_pw(password):
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"


def _check_pw(password, stored):
    salt, h = stored.split(":", 1)
    return hashlib.sha256((salt + password).encode()).hexdigest() == h


def create_user(username, password, display_name=None, is_admin=0, db_path=DB_PATH):
    conn = get_conn(db_path)
    now = datetime.now(timezone.utc).isoformat()
    try:
        conn.execute(
            "INSERT INTO users (username,password_hash,display_name,is_admin,created_at) VALUES (?,?,?,?,?)",
            (username.lower().strip(), _hash_pw(password), display_name or username, is_admin, now))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_user(username, password, db_path=DB_PATH):
    conn = get_conn(db_path)
    row = conn.execute("SELECT * FROM users WHERE username=?", (username.lower().strip(),)).fetchone()
    conn.close()
    if row and _check_pw(password, row["password_hash"]):
        return dict(row)
    return None


def list_users(db_path=DB_PATH):
    conn = get_conn(db_path)
    rows = conn.execute("SELECT id,username,display_name,is_admin,created_at FROM users ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_analysis(request_id, source_type, summary, items, raw_text, user_id=None, source_name=None, db_path=DB_PATH):
    conn = get_conn(db_path)
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO analyses (user_id,request_id,source_type,source_name,summary,raw_text,item_count,created_at) VALUES (?,?,?,?,?,?,?,?)",
        (user_id, request_id, source_type, source_name, summary, raw_text, len(items), now))
    aid = cur.lastrowid
    for item in items:
        conn.execute(
            "INSERT INTO items (analysis_id,request_id,product,price,currency,vendor,validity,quantity,moq,raw_snippet,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (aid, request_id, item.get("product","Unknown"), item.get("price"), item.get("currency"),
             item.get("vendor"), item.get("validity"), item.get("quantity"), item.get("moq"), item.get("raw_snippet",""), now))
    conn.commit()
    conn.close()
    return aid


def search_items(query, user_id=None, db_path=DB_PATH):
    product_term, price_min, price_max, currency = _parse_price_query(query)
    conn = get_conn(db_path)
    conditions, params = [], []
    if user_id:
        conditions.append("a.user_id = ?"); params.append(user_id)
    if product_term:
        conditions.append("(LOWER(i.product) LIKE ? OR LOWER(i.vendor) LIKE ? OR LOWER(i.raw_snippet) LIKE ?)")
        like = f"%{product_term.lower()}%"
        params.extend([like, like, like])
    if price_min is not None:
        conditions.append("i.price >= ?"); params.append(price_min)
    if price_max is not None:
        conditions.append("i.price <= ?"); params.append(price_max)
    if currency:
        conditions.append("UPPER(i.currency) = ?"); params.append(currency.upper())
    where = " AND ".join(conditions) if conditions else "1=1"
    rows = conn.execute(f"""
        SELECT i.*, a.source_type, a.source_name, a.created_at as date_received
        FROM items i JOIN analyses a ON i.analysis_id=a.id
        WHERE {where} ORDER BY i.created_at DESC LIMIT 200""", params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_history(user_id=None, limit=50, offset=0, db_path=DB_PATH):
    conn = get_conn(db_path)
    if user_id:
        rows = conn.execute("""SELECT a.*, u.display_name as uploaded_by
            FROM analyses a LEFT JOIN users u ON a.user_id = u.id
            WHERE a.user_id=? ORDER BY a.created_at DESC LIMIT ? OFFSET ?""", (user_id, limit, offset)).fetchall()
    else:
        rows = conn.execute("""SELECT a.*, u.display_name as uploaded_by
            FROM analyses a LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at DESC LIMIT ? OFFSET ?""", (limit, offset)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats(user_id=None, db_path=DB_PATH):
    conn = get_conn(db_path)
    if user_id:
        total_a = conn.execute("SELECT COUNT(*) FROM analyses WHERE user_id=?", (user_id,)).fetchone()[0]
        total_i = conn.execute("SELECT COUNT(*) FROM items WHERE analysis_id IN (SELECT id FROM analyses WHERE user_id=?)", (user_id,)).fetchone()[0]
        last = conn.execute("SELECT created_at FROM analyses WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (user_id,)).fetchone()
    else:
        total_a = conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
        total_i = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        last = conn.execute("SELECT created_at FROM analyses ORDER BY created_at DESC LIMIT 1").fetchone()
    conn.close()
    return {"total_analyses": total_a, "total_items": total_i, "last_analysis": last[0] if last else None}


def _parse_price_query(query):
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
