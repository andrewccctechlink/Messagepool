"""Quattro Message Pool — Web Server v1.5 (Airtable persistence, version tracking)."""
import json
import os
import uuid
import secrets
import threading
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, request, jsonify, render_template_string, session, redirect
from werkzeug.utils import secure_filename

# ── Database Backend Selection ──────────────────────────────────────────────
DB_BACKEND = os.environ.get("DB_BACKEND", "auto")
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN", "")

if DB_BACKEND == "airtable" or (DB_BACKEND == "auto" and AIRTABLE_TOKEN):
    print("📦 DB Backend: AIRTABLE (persistent — survives redeploy)")
    import db_airtable as db
    DB_PATH = None
else:
    print("📦 DB Backend: SQLite (local — data lost on redeploy)")
    import db
    DB_PATH = os.environ.get("DB_PATH", "./data/message_pool.db")

# Make functions available at module level
init_db = db.init_db
get_conn = db.get_conn
save_analysis = db.save_analysis
search_items = db.search_items
get_history = db.get_history
get_stats = db.get_stats
create_user = db.create_user
verify_user = db.verify_user
list_users = db.list_users

# ── Version ─────────────────────────────────────────────────────────────────
VERSION_PATH = os.path.join(os.path.dirname(__file__), "VERSION")
try:
    with open(VERSION_PATH, "r") as f:
        APP_VERSION = f.read().strip()
except Exception:
    APP_VERSION = "unknown"

from file_parser import parse_file
from gemini_direct import analyze_direct
from deidentify import deidentify, get_removal_summary
from imap_poller import IMAPPoller
from pages import LOGIN_HTML, INDEX_HTML

# Load config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)

# Env var overrides
CONFIG["gemini_api_key"] = os.environ.get("GEMINI_API_KEY", CONFIG.get("gemini_api_key", ""))
if os.environ.get("IMAP_EMAIL"):
    CONFIG["imap"]["enabled"] = True
    CONFIG["imap"]["server"] = os.environ.get("IMAP_SERVER", "imap.gmail.com")
    CONFIG["imap"]["port"] = int(os.environ.get("IMAP_PORT", "993"))
    CONFIG["imap"]["email"] = os.environ.get("IMAP_EMAIL", "")
    CONFIG["imap"]["password"] = os.environ.get("IMAP_PASSWORD", "")
    CONFIG["imap"]["poll_interval_minutes"] = int(os.environ.get("IMAP_INTERVAL", "5"))

if DB_PATH:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
UPLOAD_FOLDER = CONFIG.get("upload_folder", "./uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

# Init DB + default admin
if DB_PATH:
    init_db(DB_PATH)
    create_user("admin", os.environ.get("ADMIN_PASSWORD", "admin888"), "Admin", is_admin=1, db_path=DB_PATH)
else:
    init_db()
    # Admin already exists in Airtable — skip creation on startup to avoid rate limits
    print("  Admin: using existing Airtable record")

# IMAP Poller
imap_cfg = CONFIG.get("imap", {})
imap_cfg["gemini_api_key"] = CONFIG.get("gemini_api_key", "")
poller = IMAPPoller(imap_cfg, DB_PATH if DB_PATH else "./data/message_pool.db")
poller.start()
print(f"  IMAP: {'ON — checking ' + imap_cfg.get('email','') if imap_cfg.get('enabled') else 'OFF'}")
print(f"  Version: {APP_VERSION} | Backend: {'AIRTABLE' if not DB_PATH else 'SQLITE'}")


# ── Auth Decorators ──────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Login required"}), 401
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


# ── Page Routes ──────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET"])
def login_page():
    session.clear()
    return render_template_string(LOGIN_HTML)


@app.route("/logout")
def logout_page():
    session.clear()
    return redirect("/login")


@app.route("/")
@login_required
def index():
    return render_template_string(INDEX_HTML)


# ── Auth API ─────────────────────────────────────────────────────────────────

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json
    user = verify_user(data.get("username", ""), data.get("password", ""), DB_PATH)
    if not user:
        return jsonify({"error": "Invalid username or password"}), 401
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["display_name"] = user["display_name"]
    session["is_admin"] = bool(user["is_admin"])
    return jsonify({"ok": True, "user": user["display_name"], "is_admin": session["is_admin"]})


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/me")
def api_me():
    if "user_id" not in session:
        return jsonify({"logged_in": False})
    return jsonify({"logged_in": True, "user": session.get("display_name"), "is_admin": session.get("is_admin", False)})


@app.route("/api/version")
def api_version():
    """Return app version and backend info."""
    return jsonify({
        "version": APP_VERSION,
        "backend": "airtable" if not DB_PATH else "sqlite",
        "server": "Quattro Message Pool"
    })


# ── Admin API ────────────────────────────────────────────────────────────────

@app.route("/api/admin/users", methods=["GET", "POST"])
@login_required
@admin_required
def api_admin_users():
    if request.method == "GET":
        return jsonify({"users": list_users(DB_PATH)})
    data = request.json
    ok = create_user(data["username"], data["password"], data.get("display_name"), db_path=DB_PATH)
    if not ok:
        return jsonify({"error": "Username already exists"}), 400
    return jsonify({"ok": True})


@app.route("/api/admin/reset-data", methods=["POST"])
@login_required
@admin_required
def api_reset_data():
    """Clear all analyses and items, keep users."""
    conn = get_conn(DB_PATH)
    if conn:
        conn.execute("DELETE FROM items")
        conn.execute("DELETE FROM analyses")
        conn.commit()
        conn.close()
    return jsonify({"ok": True, "message": "All data cleared"})


@app.route("/api/imap-status")
@login_required
def api_imap_status():
    """Return IMAP configuration status (env vars)."""
    email = os.environ.get("IMAP_EMAIL", "")
    configured = bool(email and os.environ.get("IMAP_PASSWORD"))
    return jsonify({
        "configured_via_env": configured,
        "email": email if configured else "",
        "server": os.environ.get("IMAP_SERVER", "imap.gmail.com") if configured else "",
        "interval": int(os.environ.get("IMAP_INTERVAL", "5")),
        "poller_running": poller.status() if configured else "OFF"
    })


@app.route("/api/imap-scan", methods=["POST"])
@login_required
def api_imap_scan():
    """Manually trigger IMAP inbox scan immediately."""
    if not CONFIG.get("imap", {}).get("enabled"):
        return jsonify({"error": "IMAP is not enabled. Set IMAP_EMAIL and IMAP_PASSWORD environment variables."}), 400
    try:
        poller._check_inbox()
        return jsonify({"ok": True, "message": "Inbox scanned successfully", "processed": poller.processed_count})
    except Exception as e:
        return jsonify({"error": f"Scan failed: {str(e)}"}), 500


# ── Data API (SHARED history — all users see everything) ─────────────────────

@app.route("/api/stats")
@login_required
def api_stats():
    # Shared: no user_id filter — everyone sees total stats
    stats = get_stats(user_id=None, db_path=DB_PATH)
    stats["imap_status"] = poller.status()
    return jsonify(stats)


@app.route("/api/upload", methods=["POST"])
@login_required
def api_upload():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400
    gk = CONFIG.get("gemini_api_key", "")
    if not gk:
        return jsonify({"error": "Gemini API key not configured."}), 400
    uid = session.get("user_id")
    all_results = []
    errors = []
    for f in files:
        filename = secure_filename(f.filename)
        filepath = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}_{filename}")
        f.save(filepath)
        try:
            text, ftype = parse_file(filepath, api_key=gk)
            if not text or len(text.strip()) < 10:
                errors.append(f"{filename}: No content extracted")
                continue
            cleaned, removals = deidentify(text)
            result = analyze_direct(gk, cleaned, ftype)
            save_analysis(
                request_id=result["request_id"], source_type=result["source_type"],
                source_name=filename, summary=result.get("summary", ""),
                items=result.get("items", []), raw_text=text,
                user_id=uid, db_path=DB_PATH)
            all_results.append({
                "filename": filename, "items": result.get("items", []),
                "summary": result.get("summary", ""),
                "pii_removed": get_removal_summary(removals),
                "item_count": len(result.get("items", []))})
        except Exception as e:
            errors.append(f"{filename}: {str(e)}")
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
    return jsonify({"results": all_results, "errors": errors})


@app.route("/api/analyze-text", methods=["POST"])
@login_required
def api_analyze_text():
    data = request.json
    text = data.get("text", "").strip()
    source_type = data.get("source_type", "document")
    if not text:
        return jsonify({"error": "No text provided"}), 400
    gk = CONFIG.get("gemini_api_key", "")
    if not gk:
        return jsonify({"error": "Gemini API key not configured."}), 400
    uid = session.get("user_id")
    cleaned, removals = deidentify(text)
    result = analyze_direct(gk, cleaned, source_type)
    save_analysis(
        request_id=result["request_id"], source_type=result["source_type"],
        source_name="Pasted text", summary=result.get("summary", ""),
        items=result.get("items", []), raw_text=text,
        user_id=uid, db_path=DB_PATH)
    result["pii_removed"] = get_removal_summary(removals)
    return jsonify(result)


@app.route("/api/search")
@login_required
def api_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"items": []})
    # Shared: no user_id filter — everyone searches everything
    items = search_items(q, user_id=None, db_path=DB_PATH)
    return jsonify({"items": items, "query": q})


@app.route("/api/history")
@login_required
def api_history():
    # Shared: no user_id filter — everyone sees all history
    rows = get_history(user_id=None, limit=100, db_path=DB_PATH)
    return jsonify({"analyses": rows})


@app.route("/api/settings", methods=["GET", "POST"])
@login_required
@admin_required
def api_settings():
    global CONFIG, poller
    if request.method == "GET":
        safe = {k: v for k, v in CONFIG.items() if k != "imap"}
        safe["imap_enabled"] = CONFIG.get("imap", {}).get("enabled", False)
        safe["imap_email"] = CONFIG.get("imap", {}).get("email", "")
        return jsonify(safe)
    data = request.json
    if "gemini_api_key" in data:
        CONFIG["gemini_api_key"] = data["gemini_api_key"]
    if "imap" in data:
        CONFIG["imap"].update(data["imap"])
        CONFIG["imap"]["gemini_api_key"] = CONFIG.get("gemini_api_key", "")
        poller.stop()
        poller = IMAPPoller(CONFIG["imap"], DB_PATH if DB_PATH else "./data/message_pool.db")
        poller.start()
    with open(CONFIG_PATH, "w") as f:
        json.dump(CONFIG, f, indent=2)
    return jsonify({"status": "saved"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", CONFIG.get("port", 8080)))
    print(f"🚀 Message Pool running on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
