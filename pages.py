"""HTML pages — all templates with JS inlined. No templates/ or static/ folders needed."""

LOGIN_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Message Pool — Login</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#f5f7fa; display:flex; align-items:center; justify-content:center; height:100vh; }
.login-card { background:#fff; border-radius:16px; padding:40px; width:380px; box-shadow:0 4px 20px rgba(0,0,0,0.08); text-align:center; }
.login-card h1 { color:#5C6BC0; margin-bottom:8px; font-size:24px; }
.login-card p { color:#888; font-size:13px; margin-bottom:24px; }
input { width:100%; padding:12px 16px; border:1px solid #ddd; border-radius:8px; font-size:14px; margin-bottom:14px; }
input:focus { border-color:#5C6BC0; outline:none; }
.btn { width:100%; padding:12px; border:none; border-radius:8px; background:#5C6BC0; color:#fff; font-size:15px; font-weight:600; cursor:pointer; }
.btn:hover { background:#3F51B5; }
.error { color:#e53935; font-size:13px; margin-bottom:12px; display:none; }
</style>
</head>
<body>
<div class="login-card">
  <h1>📦 Message Pool</h1>
  <p>Quattro Dynamics — Procurement Intelligence</p>
  <div class="error" id="loginError"></div>
  <input type="text" id="username" placeholder="Username" autofocus>
  <input type="password" id="password" placeholder="Password" onkeydown="if(event.key==='Enter')doLogin()">
  <button class="btn" onclick="doLogin()">Login</button>
  <div style="margin-top:20px;font-size:11px;color:#aaa">v<span id="appVersion">—</span></div>
</div>
<script>
async function doLogin() {
  const u = document.getElementById('username').value.trim();
  const p = document.getElementById('password').value;
  const err = document.getElementById('loginError');
  if (!u || !p) { err.textContent = 'Please enter username and password'; err.style.display = 'block'; return; }
  try {
    const r = await fetch('/api/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:u, password:p})});
    const d = await r.json();
    if (d.ok) { window.location.href = '/'; }
    else { err.textContent = d.error || 'Login failed'; err.style.display = 'block'; }
  } catch(e) { err.textContent = 'Connection error'; err.style.display = 'block'; }
}
fetch('/api/version').then(r=>r.json()).then(d=>{document.getElementById('appVersion').textContent=d.version||'—'}).catch(()=>{});
</script>
</body>
</html>'''

INDEX_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Quattro Message Pool</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:#f5f7fa; display:flex; height:100vh; }
.sidebar { width:220px; background:#5C6BC0; color:#fff; padding:20px 0; display:flex; flex-direction:column; }
.sidebar h2 { padding:0 20px 20px; font-size:16px; border-bottom:1px solid rgba(255,255,255,0.2); margin-bottom:15px; }
.nav-item { padding:12px 20px; cursor:pointer; display:flex; align-items:center; gap:10px; transition:background .2s; }
.nav-item:hover { background:rgba(255,255,255,0.1); }
.nav-item.active { background:rgba(255,255,255,0.2); font-weight:600; }
.main { flex:1; overflow-y:auto; padding:30px; }
.card { background:#fff; border-radius:12px; padding:24px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.06); }
.stats-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; margin-bottom:24px; }
.stat-card { background:#fff; border-radius:10px; padding:20px; text-align:center; box-shadow:0 2px 6px rgba(0,0,0,0.05); }
.stat-card .num { font-size:32px; font-weight:700; color:#5C6BC0; }
.stat-card .label { font-size:13px; color:#666; margin-top:4px; }
.drop-zone { border:3px dashed #ccc; border-radius:16px; padding:50px 20px; text-align:center; cursor:pointer; transition:all .3s; background:#fafbfc; }
.drop-zone.dragover { border-color:#5C6BC0; background:#eef0ff; }
.drop-zone h3 { color:#444; margin-bottom:8px; }
.drop-zone p { color:#888; font-size:13px; margin:4px 0; }
.drop-zone .hint { color:#5C6BC0; font-size:12px; font-style:italic; }
.btn { padding:10px 24px; border:none; border-radius:8px; cursor:pointer; font-size:14px; font-weight:500; transition:background .2s; }
.btn-primary { background:#5C6BC0; color:#fff; }
.btn-primary:hover { background:#3F51B5; }
.btn-primary:disabled { background:#aaa; cursor:not-allowed; }
input[type=text],input[type=password],textarea,select { width:100%; padding:10px 14px; border:1px solid #ddd; border-radius:8px; font-size:14px; margin-bottom:12px; }
textarea { min-height:120px; resize:vertical; }
table { width:100%; border-collapse:collapse; font-size:13px; }
th { background:#f0f2f5; padding:10px 12px; text-align:left; font-weight:600; color:#333; }
td { padding:10px 12px; border-bottom:1px solid #eee; }
tr:hover td { background:#f8f9fb; }
.tab { display:none; }
.tab.active { display:block; }
.progress { display:none; height:4px; background:#e0e0e0; border-radius:2px; overflow:hidden; margin:16px 0; }
.progress.show { display:block; }
.progress-bar { height:100%; background:#5C6BC0; animation:loading 1.5s infinite; }
@keyframes loading { 0%{width:0} 50%{width:70%} 100%{width:100%} }
.badge { display:inline-block; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:500; }
.badge-email { background:#e3f2fd; color:#1565c0; }
.badge-doc { background:#e8f5e9; color:#2e7d32; }
.results-area { margin-top:20px; }
.empty-state { text-align:center; padding:40px; color:#999; }
.file-list { margin:12px 0; }
.file-item { display:inline-block; background:#e8eaf6; padding:4px 10px; border-radius:12px; font-size:12px; margin:3px; }
.settings-group { margin-bottom:24px; }
.settings-group label { font-weight:600; display:block; margin-bottom:6px; font-size:13px; }
.toast { position:fixed; bottom:20px; right:20px; background:#333; color:#fff; padding:12px 20px; border-radius:8px; display:none; z-index:9999; }
.toast.show { display:block; animation:fadeIn .3s; }
@keyframes fadeIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
.scan-btn { background:#ff9800; color:#fff; border:none; padding:8px 16px; border-radius:8px; cursor:pointer; font-size:13px; font-weight:500; }
.scan-btn:hover { background:#f57c00; }
.scan-btn:disabled { background:#ccc; cursor:not-allowed; }
</style>
</head>
<body>
<div class="sidebar">
  <h2>📦 Message Pool</h2>
  <div style="padding:8px 20px 15px;font-size:12px;color:rgba(255,255,255,0.7);border-bottom:1px solid rgba(255,255,255,0.2);margin-bottom:10px">👤 <span id="currentUser">User</span></div>
  <div class="nav-item active" onclick="showTab('dashboard')">📊 Dashboard</div>
  <div class="nav-item" onclick="showTab('analyze')">🤖 Analyze</div>
  <div class="nav-item" onclick="showTab('search')">🔍 Search</div>
  <div class="nav-item" onclick="showTab('history')">📋 History</div>
  <div class="nav-item" onclick="showTab('settings')" id="navSettings" style="display:none">⚙️ Settings</div>
  <div class="nav-item" onclick="showTab('admin')" id="navAdmin" style="display:none">👥 Users</div>
  <div style="flex:1"></div>
  <div style="padding:8px 20px;font-size:10px;color:rgba(255,255,255,0.45);border-top:1px solid rgba(255,255,255,0.1);margin-top:8px">v<span id="appVersion">—</span></div>
  <div class="nav-item" onclick="doLogout()" style="margin-top:0;color:rgba(255,255,255,0.6)">🚪 Logout</div>
</div>
<div class="main">
  <div id="tab-dashboard" class="tab active">
    <h1 style="margin-bottom:20px">Dashboard</h1>
    <div class="stats-grid">
      <div class="stat-card"><div class="num" id="stat-analyses">0</div><div class="label">Total Analyses</div></div>
      <div class="stat-card"><div class="num" id="stat-items">0</div><div class="label">Quotation Items</div></div>
      <div class="stat-card"><div class="num" id="stat-last">—</div><div class="label">Last Analysis</div></div>
      <div class="stat-card"><div class="num" id="stat-imap">—</div><div class="label">Email Auto-Poll</div></div>
    </div>
    <div class="card" style="border-left:4px solid #5C6BC0">
      <h3>📧 Auto Email Import (IMAP)</h3>
      <p style="margin-top:8px;color:#666">Forward any quotation email to the pool address — system auto-processes every 5 minutes.</p>
      <p style="margin-top:8px;font-size:12px;color:#888">💡 Works from any device: Outlook, Gmail, iPhone, WhatsApp (screenshot → email)</p>
      <div style="margin-top:12px;display:flex;align-items:center;gap:12px">
        <button class="scan-btn" id="scanBtnDash" onclick="doImapScan()">📨 Scan Inbox Now</button>
        <span id="scanStatusDash" style="font-size:12px;color:#666"></span>
      </div>
    </div>
    <div class="card"><h3>Quick Start</h3><p style="margin-top:10px;color:#666">① Forward emails to pool address <b>or</b> drag files into Analyze tab. ② Search all quotations in <b>Search</b>.</p></div>
  </div>
  <div id="tab-analyze" class="tab">
    <h1 style="margin-bottom:20px">Analyze Procurement Data</h1>
    <div class="card" style="border-left:4px solid #ff9800;margin-bottom:20px">
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div>
          <h3>📨 Email Inbox Scan</h3>
          <p style="font-size:13px;color:#666;margin-top:4px">Check for new forwarded emails and analyze them instantly</p>
        </div>
        <div style="text-align:right">
          <button class="scan-btn" id="scanBtnAnalyze" onclick="doImapScan()">📨 Scan Inbox Now</button>
          <div id="scanStatusAnalyze" style="font-size:11px;color:#666;margin-top:4px"></div>
        </div>
      </div>
    </div>
    <div class="drop-zone" id="dropZone">
      <h3>📂 Drop files here or click to browse</h3>
      <p>PDF, Excel (.xlsx/.xls), PPTX, DOCX, CSV, Images (JPG/PNG), Email (.eml/.msg)</p>
      <p class="hint">📧 Outlook: drag email to Desktop first → then drag .msg here</p>
      <p class="hint">📱 iPhone/WhatsApp screenshots recognized via AI Vision</p>
      <p class="hint">📎 Email attachments auto-extracted & analyzed together</p>
      <input type="file" id="fileInput" multiple hidden accept=".pdf,.xlsx,.xls,.csv,.pptx,.docx,.txt,.eml,.msg,.jpg,.jpeg,.png">
    </div>
    <div class="file-list" id="fileList"></div>
    <div style="display:flex;gap:12px;align-items:center;margin-top:12px">
      <select id="sourceType" style="width:160px;margin:0">
        <option value="document">Document</option>
        <option value="email">Email</option>
        <option value="whatsapp">WhatsApp</option>
        <option value="wechat">WeChat</option>
      </select>
      <button class="btn btn-primary" id="analyzeBtn" onclick="doAnalyze()">🤖 Analyze with AI</button>
      <span id="analyzeStatus" style="font-size:13px;color:#666"></span>
    </div>
    <div class="progress" id="analyzeProgress"><div class="progress-bar"></div></div>
    <div class="results-area" id="resultsArea"></div>
  </div>
  <div id="tab-search" class="tab">
    <h1 style="margin-bottom:20px">Smart Search</h1>
    <div style="display:flex;gap:10px;margin-bottom:12px">
      <input type="text" id="searchInput" placeholder="e.g. air fryer under USD20 or vendor Kitchen Master" style="margin:0" onkeydown="if(event.key==='Enter')doSearch()">
      <button class="btn btn-primary" onclick="doSearch()">Search</button>
    </div>
    <p style="font-size:12px;color:#888;margin-bottom:16px">Supports: product names, price ranges (under/above/between), vendors, currencies</p>
    <div id="searchResults"><div class="empty-state">Enter a query to search all quotations</div></div>
  </div>
  <div id="tab-history" class="tab">
    <h1 style="margin-bottom:20px">Analysis History <span style="font-size:13px;color:#888;font-weight:normal">(shared across all users)</span></h1>
    <div id="historyList"><div class="empty-state">Loading...</div></div>
  </div>
  <div id="tab-settings" class="tab">
    <h1 style="margin-bottom:20px">Settings</h1>
    <div class="card">
      <div class="settings-group">
        <label>🔑 Gemini API Key</label>
        <div id="geminiStatus" style="padding:10px;background:#e8f5e9;border-radius:8px;font-size:13px;color:#2e7d32;margin-bottom:8px">Loading...</div>
      </div>
      <div class="settings-group">
        <label>📧 Auto Email Poll (IMAP)</label>
        <div id="imapStatusBox" style="padding:12px;background:#e8f5e9;border-radius:8px;font-size:13px;margin-bottom:8px">
          <div id="imapStatusText">Checking...</div>
        </div>
      </div>
    </div>
    <div class="card" style="margin-top:16px">
      <h3>🗑️ Data Management</h3>
      <p style="font-size:13px;color:#666;margin:10px 0">Clear all analysis history & extracted items. Users are preserved.</p>
      <button class="btn" style="background:#e53935;color:#fff" onclick="resetData()">⚠️ Reset All Data</button>
      <span id="resetStatus" style="margin-left:12px;font-size:13px"></span>
    </div>
  </div>
  <div id="tab-admin" class="tab">
    <h1 style="margin-bottom:20px">User Management</h1>
    <div class="card">
      <h3>Add New User</h3>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:10px;margin-top:12px;align-items:end">
        <div><label style="font-size:12px">Username</label><input type="text" id="newUsername" placeholder="username" style="margin:0"></div>
        <div><label style="font-size:12px">Password</label><input type="password" id="newPassword" placeholder="password" style="margin:0"></div>
        <div><label style="font-size:12px">Display Name</label><input type="text" id="newDisplayName" placeholder="John" style="margin:0"></div>
        <button class="btn btn-primary" onclick="addUser()" style="height:42px">+ Add</button>
      </div>
      <span id="addUserStatus" style="font-size:13px;color:#4caf50"></span>
    </div>
    <div class="card" style="margin-top:16px">
      <h3>Existing Users</h3>
      <div id="userList" style="margin-top:12px">Loading...</div>
    </div>
  </div>
</div>
<div class="toast" id="toast"></div>
<script>
// ── Date Helper (UTC → local time) ──
function fmtDate(utc) {
  if (!utc) return '-';
  // Ensure the string is treated as UTC
  const s = utc.includes('Z') || utc.includes('+') ? utc : utc + 'Z';
  const d = new Date(s);
  if (isNaN(d.getTime())) return utc;
  return d.toLocaleString('en-GB', {year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false});
}
function fmtDateShort(utc) {
  if (!utc) return '-';
  const s = utc.includes('Z') || utc.includes('+') ? utc : utc + 'Z';
  const d = new Date(s);
  if (isNaN(d.getTime())) return utc;
  return d.toLocaleDateString('en-GB');
}

// ── Tab Navigation ──
let selectedFiles = [];
function showTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  document.querySelectorAll('.nav-item').forEach(n => {
    if (n.textContent.toLowerCase().includes(name)) n.classList.add('active');
  });
  if (name === 'dashboard') loadStats();
  if (name === 'history') loadHistory();
  if (name === 'admin') loadUsers();
}

// ── Dashboard Stats ──
async function loadStats() {
  try {
    const r = await fetch('/api/stats');
    const d = await r.json();
    document.getElementById('stat-analyses').textContent = d.total_analyses || 0;
    document.getElementById('stat-items').textContent = d.total_items || 0;
    document.getElementById('stat-last').textContent = fmtDateShort(d.last_analysis);
    const imap = d.imap_status || {};
    document.getElementById('stat-imap').textContent = imap.running ? '✅ Active' : '⏸ Off';
  } catch(e) { console.error(e); }
}

// ── IMAP Manual Scan ──
async function doImapScan() {
  const btns = [document.getElementById('scanBtnDash'), document.getElementById('scanBtnAnalyze')];
  const statuses = [document.getElementById('scanStatusDash'), document.getElementById('scanStatusAnalyze')];
  btns.forEach(b => { if(b) { b.disabled = true; b.textContent = '⏳ Scanning...'; } });
  statuses.forEach(s => { if(s) s.textContent = 'Connecting to inbox...'; });
  try {
    const r = await fetch('/api/imap-scan', { method: 'POST' });
    const d = await r.json();
    if (d.ok) {
      statuses.forEach(s => { if(s) { s.textContent = '✅ Scan complete! Total processed: ' + d.processed; s.style.color = '#4caf50'; } });
      toast('Inbox scanned successfully');
      loadStats();
      loadHistory();
    } else {
      statuses.forEach(s => { if(s) { s.textContent = '❌ ' + (d.error || 'Scan failed'); s.style.color = '#e53935'; } });
      toast(d.error || 'Scan failed');
    }
  } catch(e) {
    statuses.forEach(s => { if(s) { s.textContent = '❌ Connection error'; s.style.color = '#e53935'; } });
    toast('Error: ' + e.message);
  } finally {
    btns.forEach(b => { if(b) { b.disabled = false; b.textContent = '📨 Scan Inbox Now'; } });
  }
}

// ── Drag & Drop ──
document.addEventListener('DOMContentLoaded', () => {
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  dropZone.addEventListener('click', () => fileInput.click());
  dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
  dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.classList.remove('dragover'); handleFiles(e.dataTransfer.files); });
  fileInput.addEventListener('change', e => handleFiles(e.target.files));
});
function handleFiles(files) {
  selectedFiles = Array.from(files);
  const list = document.getElementById('fileList');
  list.innerHTML = selectedFiles.map(f => '<span class="file-item">📄 '+f.name+' ('+(f.size/1024).toFixed(1)+'KB)</span>').join('');
}

// ── Analyze ──
async function doAnalyze() {
  const btn = document.getElementById('analyzeBtn');
  const status = document.getElementById('analyzeStatus');
  const progress = document.getElementById('analyzeProgress');
  const results = document.getElementById('resultsArea');
  if (!selectedFiles.length) { toast('Please drop files to analyze.'); return; }
  btn.disabled = true; status.textContent = '🔒 Processing...'; progress.classList.add('show'); results.innerHTML = '';
  try {
    const form = new FormData();
    selectedFiles.forEach(f => form.append('files', f));
    const r = await fetch('/api/upload', { method: 'POST', body: form });
    data = await r.json();
    if (!r.ok) { toast(data.error || 'Upload failed'); return; }
    let html = '';
    if (data.errors && data.errors.length) { html += '<div class="card" style="border-left:4px solid #ff9800"><b>⚠️ Errors:</b><br>'+data.errors.join('<br>')+'</div>'; }
    for (const res of (data.results || [])) {
      html += '<div class="card">';
      html += '<h3>📄 '+res.filename+' — '+(res.item_count||res.items.length)+' item(s) found</h3>';
      if (res.summary) html += '<p style="color:#666;margin:8px 0;font-style:italic">'+res.summary+'</p>';
      if (res.pii_removed) html += '<p style="font-size:12px;color:#ff9800">🛡️ '+res.pii_removed+'</p>';
      if (res.items && res.items.length) {
        html += '<table><thead><tr><th>Product</th><th>Price</th><th>Currency</th><th>Vendor</th><th>MOQ</th><th>Validity</th></tr></thead><tbody>';
        for (const item of res.items) { html += '<tr><td>'+(item.product||'-')+'</td><td>'+(item.price||'-')+'</td><td>'+(item.currency||'-')+'</td><td>'+(item.vendor||'-')+'</td><td>'+(item.moq||'-')+'</td><td>'+(item.validity||'-')+'</td></tr>'; }
        html += '</tbody></table>';
      }
      html += '</div>';
    }
    results.innerHTML = html || '<div class="empty-state">No items extracted</div>';
    status.textContent = '✅ Done';
    selectedFiles = []; document.getElementById('fileList').innerHTML = '';
    loadStats();
  } catch(e) { status.textContent = '❌ Error: ' + e.message;
  } finally { btn.disabled = false; progress.classList.remove('show'); }
}

// ── Search ──
async function doSearch() {
  const q = document.getElementById('searchInput').value.trim();
  if (!q) return;
  const div = document.getElementById('searchResults');
  div.innerHTML = '<div class="empty-state">Searching...</div>';
  try {
    const r = await fetch('/api/search?q=' + encodeURIComponent(q));
    const d = await r.json();
    if (!d.items || !d.items.length) { div.innerHTML = '<div class="empty-state">No results found</div>'; return; }
    window._mpLastSearch = d.items;
    let html = '<p style="margin-bottom:12px;color:#666">Found '+d.items.length+' result(s) &nbsp; <button class="btn btn-primary" onclick="createQuotation()" style="padding:6px 16px;font-size:13px">🧾 Create Quotation</button></p>';
    html += '<table><thead><tr><th>☐</th><th>Product</th><th>Price</th><th>Currency</th><th>Vendor</th><th>MOQ</th><th>Source</th><th>Date</th></tr></thead><tbody>';
    for (let i=0; i<d.items.length; i++) { const item=d.items[i]; html += '<tr><td><input type="checkbox" class="quote-check" data-idx="'+i+'"></td><td>'+(item.product||'-')+'</td><td>'+(item.price||'-')+'</td><td>'+(item.currency||'-')+'</td><td>'+(item.vendor||'-')+'</td><td>'+(item.moq||'-')+'</td><td>'+(item.source_name||item.source_type||'-')+'</td><td>'+fmtDate(item.date_received)+'</td></tr>'; }
    html += '</tbody></table>';
    div.innerHTML = html;
  } catch(e) { div.innerHTML = '<div class="empty-state">Error: '+e.message+'</div>'; }
}

function createQuotation(){
  const items=window._mpLastSearch||[];
  const checks=document.querySelectorAll('.quote-check:checked');
  if(!checks.length){alert('Please select at least one item to include in the quotation.');return;}
  const sel=[];
  checks.forEach(cb=>{const idx=parseInt(cb.dataset.idx);if(items[idx])sel.push(items[idx]);});
  if(!sel.length){alert('No valid items selected.');return;}
  let rows=''; let total=0;
  for(const it of sel){
    const p=parseFloat(it.price)||0; const qty=parseInt(it.moq)||1; const ext=p*qty; total+=ext;
    rows+='<tr><td>'+(it.product||'-')+'</td><td style="text-align:right">'+(it.price||'-')+'</td><td>'+(it.currency||'USD')+'</td><td>'+(it.vendor||'-')+'</td><td style="text-align:right">'+(it.moq||'-')+'</td><td style="text-align:right">'+ext.toFixed(2)+'</td></tr>';
  }
  const today=(new Date()).toISOString().slice(0,10);
  const ref='Q-'+Date.now().toString(36).toUpperCase();
  const html='<html xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel"><head><meta charset="UTF-8"><style>td,th{border:1px solid #999;padding:6px 10px;font-size:12px}th{background:#003366;color:#fff}.lh td{text-align:center;border:none}.tt{font-size:16px;font-weight:bold;text-align:center;border:none;padding:8px}.dt{text-align:right;font-size:11px;color:#666;border:none}.to{font-size:11px;border:none}table{width:100%;border-collapse:collapse}.tot{font-weight:bold;background:#e8f0fe}.ft{text-align:center;font-size:10px;color:#999;border:none}</style></head><body><table><tr class="lh"><td colspan="6" style="font-size:18px;font-weight:bold;color:#003366;padding:12px 0;border-bottom:2px solid #003366">STAR GLORY TRADING COMPANY</td></tr><tr class="lh"><td colspan="6" style="font-size:10px;color:#666">Unit 1208, Tower B, Trade Centre, Kowloon Bay, Hong Kong | Tel: +852 3568 1200 | shipping@starglory.com.hk</td></tr><tr class="tt"><td colspan="6">OFFICIAL QUOTATION</td></tr><tr class="dt"><td colspan="6">Date: '+today+'&nbsp;&nbsp;&nbsp;Ref: '+ref+'</td></tr><tr class="to"><td colspan="6"></td></tr></table><br><table><thead><tr><th>Product</th><th>Unit Price</th><th>Currency</th><th>Vendor</th><th>MOQ</th><th>Extended</th></tr></thead><tbody>'+rows+'</tbody><tfoot><tr class="tot"><td colspan="5" style="text-align:right">Total (at MOQ)</td><td style="text-align:right">USD '+total.toFixed(2)+'</td></tr></tfoot></table><br><table><tr class="ft"><td colspan="6">Quotation generated by Message Pool &mdash; Star Glory ERP | '+today+'</td></tr><tr class="ft"><td colspan="6">Prices valid for 15 days. Terms: FOB China. Payment: T/T. Subject to final confirmation.</td></tr></table></body></html>';
  const blob=new Blob([html],{type:'application/vnd.ms-excel'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='Quotation_StarGlory_'+today+'.xls';a.click();
  toast('🧾 Quotation generated with '+sel.length+' item(s) (opens in Excel).');
}

// ── History ──
async function loadHistory() {
  const div = document.getElementById('historyList');
  const isAdmin = document.getElementById('navAdmin').style.display !== 'none';
  try {
    const r = await fetch('/api/history');
    const d = await r.json();
    if (!d.analyses || !d.analyses.length) { div.innerHTML = '<div class="empty-state">No analyses yet</div>'; return; }
    let html = '<table><thead><tr><th>Date</th><th>User</th><th>Source</th><th>Type</th><th>Items</th><th>Summary</th>'+(isAdmin?'<th>Action</th>':'')+'</tr></thead><tbody>';
    for (const a of d.analyses) { html += '<tr><td>'+fmtDate(a.created_at)+'</td><td>'+(a.uploaded_by||'System')+'</td><td>'+(a.source_name||'-')+'</td><td><span class="badge badge-'+(a.source_type==='email'?'email':'doc')+'">'+a.source_type+'</span></td><td>'+a.item_count+'</td><td>'+((a.summary||'').slice(0,80))+'</td>'+(isAdmin?'<td><button class="btn btn-sm btn-danger" onclick="deleteHistory(\''+a.id+'\',this)">🗑️</button></td>':'')+'</tr>'; }
    html += '</tbody></table>';
    div.innerHTML = html;
  } catch(e) { div.innerHTML = '<div class="empty-state">Error: '+e.message+'</div>'; }
}

async function deleteHistory(id, btn) {
  if (!confirm('Delete this analysis record?')) return;
  btn.disabled = true;
  try {
    const r = await fetch('/api/history/delete', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id}) });
    if (r.ok) { btn.closest('tr').remove(); toast('🗑️ Deleted'); }
    else { const d = await r.json(); toast('Error: '+(d.error||'Failed')); }
  } catch(e) { toast('Error: '+e.message); }
  btn.disabled = false;
}

// ── Settings ──
async function loadSettings() {
  try {
    const geminiEl = document.getElementById('geminiStatus');
    geminiEl.innerHTML = '✅ Configured via server environment';
    geminiEl.style.background = '#e8f5e9'; geminiEl.style.color = '#2e7d32';
    const r = await fetch('/api/imap-status');
    const d = await r.json();
    const box = document.getElementById('imapStatusText');
    if (d.configured_via_env) {
      box.innerHTML = '✅ <b>Configured via server environment</b><br>📧 Email: <code>'+d.email+'</code><br>🖥️ Server: <code>'+d.server+'</code><br>⏰ Polling: every '+d.interval+' minutes<br>📡 Status: '+(typeof d.poller_running === 'object' ? (d.poller_running.running ? 'Active' : 'Stopped') : d.poller_running);
      document.getElementById('imapStatusBox').style.background = '#e8f5e9';
    } else {
      box.innerHTML = '⚠️ IMAP not configured. Set <code>IMAP_EMAIL</code> and <code>IMAP_PASSWORD</code> environment variables on Zeabur.';
      document.getElementById('imapStatusBox').style.background = '#fff3e0';
    }
  } catch(e) { console.error('loadSettings:', e); }
}

// ── Reset Data ──
async function resetData() {
  if (!confirm('⚠️ This will permanently delete ALL analyses and items. Users will be preserved.\\n\\nAre you sure?')) return;
  try {
    const r = await fetch('/api/admin/reset-data', { method:'POST' });
    const d = await r.json();
    if (d.ok) { document.getElementById('resetStatus').textContent = '✅ All data cleared'; document.getElementById('resetStatus').style.color = '#4caf50'; toast('All data has been cleared'); loadStats(); }
    else { document.getElementById('resetStatus').textContent = '❌ '+(d.error||'Failed'); document.getElementById('resetStatus').style.color = '#e53935'; }
  } catch(e) { toast('Error: '+e.message); }
}

// ── Toast ──
function toast(msg) { const t = document.getElementById('toast'); t.textContent = msg; t.classList.add('show'); setTimeout(() => t.classList.remove('show'), 3000); }

// ── Auth ──
async function checkAuth() {
  try {
    const r = await fetch('/api/me');
    const d = await r.json();
    if (!d.logged_in) { window.location.href = '/login'; return; }
    document.getElementById('currentUser').textContent = d.user;
    if (d.is_admin) { document.getElementById('navSettings').style.display = ''; document.getElementById('navAdmin').style.display = ''; }
  } catch(e) { window.location.href = '/login'; }
}
async function doLogout() { await fetch('/api/logout', {method:'POST'}); window.location.href = '/login'; }

// ── Admin: Users ──
async function loadUsers() {
  try {
    const r = await fetch('/api/admin/users');
    const d = await r.json();
    if (!d.users || !d.users.length) { document.getElementById('userList').innerHTML = 'No users'; return; }
    let html = '<table><thead><tr><th>ID</th><th>Username</th><th>Display Name</th><th>Role</th><th>Created</th></tr></thead><tbody>';
    for (const u of d.users) { html += '<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+(u.is_admin?'Admin':'User')+'</td><td>'+fmtDateShort(u.created_at)+'</td></tr>'; }
    html += '</tbody></table>';
    document.getElementById('userList').innerHTML = html;
  } catch(e) { document.getElementById('userList').innerHTML = 'Access denied'; }
}
async function addUser() {
  const u = document.getElementById('newUsername').value.trim();
  const p = document.getElementById('newPassword').value;
  const n = document.getElementById('newDisplayName').value.trim();
  if (!u || !p) { toast('Username and password required'); return; }
  try {
    const r = await fetch('/api/admin/users', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:u, password:p, display_name:n||u})});
    const d = await r.json();
    if (d.ok) { document.getElementById('addUserStatus').textContent = '✅ User created!'; document.getElementById('newUsername').value=''; document.getElementById('newPassword').value=''; document.getElementById('newDisplayName').value=''; loadUsers(); setTimeout(()=>document.getElementById('addUserStatus').textContent='',3000); }
    else { toast(d.error || 'Failed'); }
  } catch(e) { toast('Error: '+e.message); }
}

// ── Init ──
checkAuth(); loadStats(); loadSettings(); setInterval(loadStats, 30000);
fetch('/api/version').then(r=>r.json()).then(d=>{document.getElementById('appVersion').textContent=d.version||'—'}).catch(()=>{});
</script>
</body>
</html>'''
