from flask import Flask, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, tempfile
from datetime import date
from functools import wraps

app = Flask(__name__)
app.secret_key = "bizhisaab2025secret"
DB = os.path.join(tempfile.gettempdir(), "biz.db")

# ── HTML HELPERS ──────────────────────────────────────────────────────────────
CSS = """
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:'Segoe UI',sans-serif}
body{background:#F1F5F9;display:flex;min-height:100vh}
a{text-decoration:none;color:inherit}
.sb{width:200px;background:#0F172A;display:flex;flex-direction:column;min-height:100vh;flex-shrink:0;position:fixed;top:0;left:0;height:100%}
.sb-brand{padding:16px;color:#fff;font-size:14px;font-weight:700;border-bottom:1px solid #1e293b}
.sb-brand span{color:#3B82F6}
.sb a{display:block;padding:10px 16px;color:#94A3B8;font-size:12px;transition:.15s}
.sb a:hover,.sb a.on{background:#3B82F6;color:#fff}
.sb-foot{margin-top:auto;padding:12px 16px;font-size:11px;color:#475569;border-top:1px solid #1e293b}
.sb-foot a{color:#EF4444;display:block;margin-top:6px}
.main{margin-left:200px;flex:1;display:flex;flex-direction:column}
.topbar{background:#fff;border-bottom:1px solid #E2E8F0;padding:0 20px;height:50px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:10}
.topbar h1{font-size:14px;font-weight:600}
.con{padding:16px 20px}
.card{background:#fff;border:1px solid #E2E8F0;border-radius:10px;padding:16px;margin-bottom:14px}
.ct{font-size:13px;font-weight:600;margin-bottom:12px;color:#111827}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:14px}
.met{background:#fff;border:1px solid #E2E8F0;border-radius:10px;padding:12px}
.ml{font-size:11px;color:#6B7280;margin-bottom:3px}
.mv{font-size:17px;font-weight:700}
.g{color:#16A34A}.r{color:#DC2626}.b{color:#3B82F6}.w{color:#D97706}
.fg{margin-bottom:8px}
.fg label{display:block;font-size:11px;color:#6B7280;font-weight:600;margin-bottom:3px}
.fg input,.fg select{width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px;font-family:inherit;background:#fff}
.fgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:8px;margin-bottom:10px}
.btn{display:inline-block;padding:7px 16px;border-radius:7px;font-size:12px;font-weight:600;cursor:pointer;border:none;transition:.15s}
.bp{background:#3B82F6;color:#fff}.bp:hover{background:#2563EB}
.bs{background:#16A34A;color:#fff}
.bd{background:#DC2626;color:#fff;padding:4px 9px;font-size:11px}
.kul{font-size:14px;font-weight:700;color:#3B82F6;padding:5px 0;margin-bottom:8px}
table{width:100%;border-collapse:collapse;font-size:11px}
th{background:#F8FAFC;padding:7px 9px;text-align:left;font-weight:600;color:#6B7280;border-bottom:1px solid #E2E8F0;white-space:nowrap}
td{padding:7px 9px;border-bottom:1px solid #F1F5F9;color:#111827}
tr:hover td{background:#F8FAFC}
.tw{overflow-x:auto}
.badge{display:inline-block;padding:1px 7px;border-radius:99px;font-size:10px;font-weight:600}
.bg-g{background:#DCFCE7;color:#166534}
.bg-r{background:#FEE2E2;color:#991B1B}
.bg-w{background:#FEF3C7;color:#92400E}
.bg-b{background:#DBEAFE;color:#1E40AF}
.alert{padding:8px 12px;border-radius:7px;margin-bottom:10px;font-size:12px;font-weight:500}
.al-s{background:#DCFCE7;color:#166534;border:1px solid #BBF7D0}
.al-d{background:#FEE2E2;color:#991B1B;border:1px solid #FECACA}
.al-i{background:#DBEAFE;color:#1E40AF;border:1px solid #BFDBFE}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.pnl-s{background:#EFF6FF;border-left:3px solid #3B82F6;padding:5px 10px;margin:8px 0 3px;font-size:11px;font-weight:600;color:#1E40AF}
.pnl-r{display:flex;justify-content:space-between;padding:5px 8px;border-bottom:1px solid #F1F5F9;font-size:12px}
.pnl-t{font-weight:700;background:#F8FAFC}
.pnl-grand{display:flex;justify-content:space-between;font-size:14px;font-weight:700;background:#EFF6FF;border-radius:6px;padding:10px 12px;margin-top:8px}
@media(max-width:700px){.sb{display:none}.main{margin-left:0}.g2{grid-template-columns:1fr}.grid{grid-template-columns:1fr 1fr}}
</style>
"""

def layout(title, page, body, user=""):
    admin_links = ""
    if session.get("role") == "admin":
        admin_links = f"""
        <a href="/investment" class="{'on' if page=='inv' else ''}">💰 Investment</a>
        <a href="/loan" class="{'on' if page=='ln' else ''}">🏦 Loan</a>
        <a href="/pnl" class="{'on' if page=='pnl' else ''}">📊 P&L Report</a>
        <a href="/users" class="{'on' if page=='usr' else ''}">👥 Users</a>
        """
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>BizHisaab — {title}</title>{CSS}</head><body>
    <nav class="sb">
      <div class="sb-brand">📊 <span>Biz</span>Hisaab</div>
      <a href="/dashboard" class="{'on' if page=='dash' else ''}">🏠 Dashboard</a>
      <a href="/kharidari" class="{'on' if page=='kh' else ''}">📦 Kharidari</a>
      <a href="/akhrajaat" class="{'on' if page=='ex' else ''}">💸 Akhrajaat</a>
      <a href="/courier" class="{'on' if page=='co' else ''}">🚚 Courier</a>
      {admin_links}
      <div class="sb-foot">
        <div style="font-weight:600;color:#94A3B8">{session.get('naam','')}</div>
        <div>{session.get('role','')}</div>
        <a href="/logout">Logout</a>
      </div>
    </nav>
    <div class="main">
      <div class="topbar"><h1>{title}</h1><span style="font-size:11px;color:#6B7280">👤 {session.get('naam','')}</span></div>
      <div class="con">{body}</div>
    </div>
    </body></html>"""

def alerts():
    msgs = session.pop('_flashes', [])
    html = ""
    for cat, msg in msgs:
        cl = "al-s" if cat == "success" else "al-d" if cat == "danger" else "al-i"
        html += f'<div class="alert {cl}">{msg}</div>'
    return html

def pk(n):
    try: return f"Rs {int(float(n or 0)):,}"
    except: return "Rs 0"

def today(): return str(date.today())

# ── DATABASE ──────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'employee',
        naam TEXT
    );
    CREATE TABLE IF NOT EXISTS kharidari (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarikh TEXT, vendor TEXT, maal TEXT,
        qty REAL, unit TEXT, daam REAL, kul_rakam REAL,
        status TEXT, notes TEXT, darj_kiya TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS akhrajaat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarikh TEXT, head TEXT, tafseel TEXT,
        kise_diya TEXT, rakam REAL, tariqa TEXT,
        darj_kiya TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS courier (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarikh TEXT, courier_naam TEXT, qism TEXT,
        parcel_tadaad REAL, mila REAL, charges REAL,
        net_rakam REAL, reference TEXT, darj_kiya TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS investment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarikh TEXT, tafseel TEXT, rakam REAL,
        darj_kiya TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS loan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarikh TEXT, shakhs TEXT, qism TEXT, rakam REAL,
        darj_kiya TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS heads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        naam TEXT UNIQUE NOT NULL
    );
    """)
    if not db.execute("SELECT id FROM users WHERE username='admin'").fetchone():
        db.execute("INSERT INTO users (username,password,role,naam) VALUES (?,?,?,?)",
            ("admin", generate_password_hash("admin123"), "admin", "Mudassar"))
    for h in ["Rickshaw/Transport","Kiraya","Tankhwah","Marketing & Ads",
              "Bijli/Utility","Packing","Shipping","Bank Charges","Aur Kharcha"]:
        try: db.execute("INSERT INTO heads (naam) VALUES (?)", (h,))
        except: pass
    db.commit()
    db.close()

def login_req(f):
    @wraps(f)
    def dec(*a, **kw):
        if "uid" not in session: return redirect("/")
        return f(*a, **kw)
    return dec

def admin_req(f):
    @wraps(f)
    def dec(*a, **kw):
        if session.get("role") != "admin":
            session.setdefault('_flashes', []).append(("danger", "Sirf admin access hai"))
            return redirect("/dashboard")
        return f(*a, **kw)
    return dec

# ── AUTH ──────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET","POST"])
def login():
    if "uid" in session: return redirect("/dashboard")
    err = ""
    if request.method == "POST":
        db = get_db()
        u = db.execute("SELECT * FROM users WHERE username=?", (request.form.get("username",""),)).fetchone()
        db.close()
        if u and check_password_hash(u["password"], request.form.get("password","")):
            session["uid"] = u["id"]
            session["naam"] = u["naam"] or u["username"]
            session["role"] = u["role"]
            return redirect("/dashboard")
        err = '<div class="alert al-d">Username ya password galat hai!</div>'
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>BizHisaab Login</title>{CSS}
    <style>body{{display:flex;align-items:center;justify-content:center;background:#0F172A;margin-left:0}}
    .box{{background:#fff;border-radius:14px;padding:36px;width:340px;max-width:95vw}}
    .brand{{text-align:center;font-size:22px;font-weight:800;color:#0F172A;margin-bottom:5px}}
    .brand span{{color:#3B82F6}}.sub{{text-align:center;font-size:12px;color:#6B7280;margin-bottom:24px}}
    .lbl{{display:block;font-size:12px;color:#374151;font-weight:600;margin-bottom:4px}}
    .inp{{width:100%;padding:10px;border:1px solid #E2E8F0;border-radius:8px;font-size:13px;margin-bottom:14px}}
    .lbtn{{width:100%;padding:11px;background:#3B82F6;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer}}
    .hint{{text-align:center;margin-top:12px;font-size:11px;color:#9CA3AF}}</style>
    </head><body><div class="box">
    <div class="brand">📊 <span>Biz</span>Hisaab</div>
    <div class="sub">Business Accounting System</div>
    {err}
    <form method="POST" action="/">
    <label class="lbl">Username</label>
    <input class="inp" name="username" placeholder="username" required autofocus>
    <label class="lbl">Password</label>
    <input class="inp" type="password" name="password" placeholder="password" required>
    <button class="lbtn" type="submit">Login Karein</button>
    </form>
    <div class="hint">Default: admin / admin123</div>
    </div></body></html>"""

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
@app.route("/dashboard")
@login_req
def dashboard():
    db = get_db()
    pu   = db.execute("SELECT COALESCE(SUM(kul_rakam),0) FROM kharidari WHERE status!='Unpaid (Baqi)'").fetchone()[0]
    ex   = db.execute("SELECT COALESCE(SUM(rakam),0) FROM akhrajaat").fetchone()[0]
    co   = db.execute("SELECT COALESCE(SUM(net_rakam),0) FROM courier").fetchone()[0]
    inv  = db.execute("SELECT COALESCE(SUM(rakam),0) FROM investment").fetchone()[0]
    ll   = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Liya'").fetchone()[0]
    lw   = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Wapas'").fetchone()[0]
    net  = co - pu - ex
    nc   = "g" if net >= 0 else "r"
    rpu  = db.execute("SELECT * FROM kharidari ORDER BY created_at DESC LIMIT 5").fetchall()
    rco  = db.execute("SELECT * FROM courier ORDER BY created_at DESC LIMIT 5").fetchall()
    rex  = db.execute("SELECT * FROM akhrajaat ORDER BY created_at DESC LIMIT 5").fetchall()
    db.close()

    pu_rows = "".join([f"<tr><td>{r['tarikh']}</td><td>{r['vendor']}</td><td>{r['maal']}</td><td>{int(r['qty'])}</td><td>{r['unit']}</td><td class='g'><b>{pk(r['kul_rakam'])}</b></td><td><span class='badge {'bg-g' if 'Paid' in str(r['status']) else 'bg-r' if 'Unpaid' in str(r['status']) else 'bg-w'}'>{r['status']}</span></td></tr>" for r in rpu]) or "<tr><td colspan='7' style='text-align:center;color:#9CA3AF;padding:14px'>Koi data nahi</td></tr>"
    co_rows = "".join([f"<tr><td>{r['tarikh']}</td><td><span class='badge bg-b'>{r['courier_naam']}</span></td><td>{r['qism']}</td><td class='g'><b>{pk(r['net_rakam'])}</b></td></tr>" for r in rco]) or "<tr><td colspan='4' style='text-align:center;color:#9CA3AF;padding:14px'>Koi data nahi</td></tr>"
    ex_rows = "".join([f"<tr><td>{r['tarikh']}</td><td><span class='badge bg-w'>{r['head']}</span></td><td>{r['tafseel']}</td><td class='r'><b>{pk(r['rakam'])}</b></td></tr>" for r in rex]) or "<tr><td colspan='4' style='text-align:center;color:#9CA3AF;padding:14px'>Koi data nahi</td></tr>"

    body = f"""
    {alerts()}
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div style="font-size:12px;color:#6B7280">Tamam business ka overview</div>
      <a href="/export/all" class="btn bs" style="font-size:12px">⬇ Poora Data Export (Excel)</a>
    </div>
    <div class="grid">
      <div class="met"><div class="ml">Courier Amdani</div><div class="mv g">{pk(co)}</div></div>
      <div class="met"><div class="ml">Kul Kharidari</div><div class="mv r">{pk(pu)}</div></div>
      <div class="met"><div class="ml">Kul Akhrajaat</div><div class="mv r">{pk(ex)}</div></div>
      <div class="met"><div class="ml">Net Faida/Nuksan</div><div class="mv {nc}">{pk(net)}</div></div>
      <div class="met"><div class="ml">Investment</div><div class="mv b">{pk(inv)}</div></div>
      <div class="met"><div class="ml">Baqi Loan</div><div class="mv w">{pk(ll-lw)}</div></div>
    </div>
    <div class="g2">
      <div class="card"><div class="ct">Akhri Kharidari</div><div class="tw"><table>
        <thead><tr><th>Tarikh</th><th>Vendor</th><th>Maal</th><th>Qty</th><th>Unit</th><th>Rakam</th><th>Status</th></tr></thead>
        <tbody>{pu_rows}</tbody></table></div></div>
      <div class="card"><div class="ct">Akhri Courier</div><div class="tw"><table>
        <thead><tr><th>Tarikh</th><th>Courier</th><th>Qism</th><th>Net Rakam</th></tr></thead>
        <tbody>{co_rows}</tbody></table></div></div>
    </div>
    <div class="card"><div class="ct">Akhri Akhrajaat</div><div class="tw"><table>
      <thead><tr><th>Tarikh</th><th>Head</th><th>Tafseel</th><th>Rakam</th></tr></thead>
      <tbody>{ex_rows}</tbody></table></div></div>"""
    return layout("Dashboard", "dash", body)

# ── KHARIDARI ─────────────────────────────────────────────────────────────────
@app.route("/kharidari", methods=["GET","POST"])
@login_req
def kharidari():
    db = get_db()
    if request.method == "POST":
        f = request.form
        qty = float(f.get("qty") or 1)
        dm  = float(f.get("daam") or 0)
        db.execute("INSERT INTO kharidari (tarikh,vendor,maal,qty,unit,daam,kul_rakam,status,notes,darj_kiya) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (f.get("tarikh") or today(), f.get("vendor",""), f.get("maal",""),
             qty, f.get("unit","Dozen"), dm, round(qty*dm,2),
             f.get("status","Paid (Ada)"), f.get("notes",""), session.get("naam","")))
        db.commit()
        session.setdefault('_flashes',[]).append(("success","Kharidari save ho gayi!"))
        return redirect("/kharidari")
    rows  = db.execute("SELECT * FROM kharidari ORDER BY created_at DESC").fetchall()
    total = db.execute("SELECT COALESCE(SUM(kul_rakam),0) FROM kharidari").fetchone()[0]
    ada   = db.execute("SELECT COALESCE(SUM(kul_rakam),0) FROM kharidari WHERE status='Paid (Ada)'").fetchone()[0]
    baqi  = db.execute("SELECT COALESCE(SUM(kul_rakam),0) FROM kharidari WHERE status='Unpaid (Baqi)'").fetchone()[0]
    db.close()

    trs = "".join([f"""<tr><td>{r['tarikh']}</td><td>{r['vendor']}</td><td>{r['maal']}</td>
        <td>{int(r['qty'])}</td><td>{r['unit']}</td><td>{pk(r['daam'])}</td>
        <td class='g'><b>{pk(r['kul_rakam'])}</b></td>
        <td><span class='badge {'bg-g' if 'Paid' in str(r['status']) else 'bg-r' if 'Unpaid' in str(r['status']) else 'bg-w'}'>{r['status']}</span></td>
        <td style='color:#9CA3AF;font-size:10px'>{r['darj_kiya']}</td>
        {'<td><a href="/kharidari/del/'+str(r['id'])+'" class="btn bd" onclick="return confirm(\'Delete?\')">Del</a></td>' if session.get('role')=='admin' else ''}
        </tr>""" for r in rows]) or f"<tr><td colspan='10' style='text-align:center;color:#9CA3AF;padding:14px'>Koi record nahi</td></tr>"

    body = f"""{alerts()}
    <div class="card"><div class="ct">Nai Kharidari Darj Karein</div>
    <form method="POST" action="/kharidari">
    <div class="fgrid">
      <div class="fg"><label>Vendor ka Naam</label><input name="vendor" placeholder="Vendor naam" required></div>
      <div class="fg"><label>Maal ka Naam</label><input name="maal" placeholder="Maal naam" required></div>
      <div class="fg"><label>Quantity</label><input name="qty" type="number" step="0.01" value="1" id="qty" oninput="calc()"></div>
      <div class="fg"><label>Unit</label><select name="unit"><option>Dozen</option><option>Piece / Adad</option><option>Box</option><option>Kg</option><option>Man</option><option>Other</option></select></div>
      <div class="fg"><label>Daam per Unit (PKR)</label><input name="daam" type="number" step="0.01" placeholder="0" id="daam" oninput="calc()"></div>
      <div class="fg"><label>Payment Status</label><select name="status"><option>Paid (Ada)</option><option>Unpaid (Baqi)</option><option>Partial (Adha)</option></select></div>
      <div class="fg"><label>Tarikh</label><input name="tarikh" type="date" id="dt"></div>
      <div class="fg"><label>Notes</label><input name="notes" placeholder="Optional"></div>
    </div>
    <div class="kul" id="kul">Kul Rakam: Rs 0</div>
    <button class="btn bp" type="submit">✓ Darj Karein</button>
    </form></div>
    <div class="grid" style="margin-bottom:14px">
      <div class="met"><div class="ml">Kul</div><div class="mv">{pk(total)}</div></div>
      <div class="met"><div class="ml">Ada</div><div class="mv g">{pk(ada)}</div></div>
      <div class="met"><div class="ml">Baqi</div><div class="mv r">{pk(baqi)}</div></div>
    </div>
    <div class="card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div class="ct" style="margin:0">Tamam Kharidari</div>
      <a href="/export/kharidari" class="btn bs" style="font-size:11px;padding:5px 12px">⬇ Excel Export</a>
    </div><div class="tw"><table>
      <thead><tr><th>Tarikh</th><th>Vendor</th><th>Maal</th><th>Qty</th><th>Unit</th><th>Daam</th><th>Kul Rakam</th><th>Status</th><th>Darj Kiya</th>{'<th></th>' if session.get('role')=='admin' else ''}</tr></thead>
      <tbody>{trs}</tbody></table></div></div>
    <script>document.getElementById('dt').valueAsDate=new Date();
    function calc(){{var q=parseFloat(document.getElementById('qty').value)||0;var d=parseFloat(document.getElementById('daam').value)||0;document.getElementById('kul').textContent='Kul Rakam: Rs '+Math.round(q*d).toLocaleString();}}</script>"""
    return layout("Kharidari (Purchases)", "kh", body)

@app.route("/kharidari/del/<int:i>")
@login_req
@admin_req
def del_kh(i):
    db = get_db()
    db.execute("DELETE FROM kharidari WHERE id=?", (i,))
    db.commit(); db.close()
    session.setdefault('_flashes',[]).append(("info","Delete ho gaya"))
    return redirect("/kharidari")

# ── AKHRAJAAT ──────────────────────────────────────────────────────────────────
@app.route("/akhrajaat", methods=["GET","POST"])
@login_req
def akhrajaat():
    db = get_db()
    hds = [r[0] for r in db.execute("SELECT naam FROM heads ORDER BY naam").fetchall()]
    if request.method == "POST":
        f = request.form
        db.execute("INSERT INTO akhrajaat (tarikh,head,tafseel,kise_diya,rakam,tariqa,darj_kiya) VALUES (?,?,?,?,?,?,?)",
            (f.get("tarikh") or today(), f.get("head",""), f.get("tafseel",""),
             f.get("kise_diya",""), float(f.get("rakam") or 0),
             f.get("tariqa","Cash"), session.get("naam","")))
        db.commit()
        session.setdefault('_flashes',[]).append(("success","Kharcha save ho gaya!"))
        return redirect("/akhrajaat")
    rows  = db.execute("SELECT * FROM akhrajaat ORDER BY created_at DESC").fetchall()
    total = db.execute("SELECT COALESCE(SUM(rakam),0) FROM akhrajaat").fetchone()[0]
    by_hd = db.execute("SELECT head, SUM(rakam) t FROM akhrajaat GROUP BY head ORDER BY t DESC").fetchall()
    db.close()

    hd_opts = "".join([f"<option>{h}</option>" for h in hds])
    trs = "".join([f"""<tr><td>{r['tarikh']}</td><td><span class='badge bg-w'>{r['head']}</span></td>
        <td>{r['tafseel']}</td><td>{r['kise_diya'] or '—'}</td>
        <td class='r'><b>{pk(r['rakam'])}</b></td><td>{r['tariqa']}</td>
        <td style='color:#9CA3AF;font-size:10px'>{r['darj_kiya']}</td>
        {'<td><a href="/akhrajaat/del/'+str(r['id'])+'" class="btn bd" onclick="return confirm(\'Delete?\')">Del</a></td>' if session.get('role')=='admin' else ''}
        </tr>""" for r in rows]) or "<tr><td colspan='8' style='text-align:center;color:#9CA3AF;padding:14px'>Koi record nahi</td></tr>"

    hd_summary = "".join([f"<div style='display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #F1F5F9;font-size:12px'><span>{r['head']}</span><span class='r'><b>{pk(r['t'])}</b></span></div>" for r in by_hd]) or "<div style='color:#9CA3AF;font-size:12px;padding:8px'>Koi data nahi</div>"

    add_head_form = ""
    if session.get("role") == "admin":
        add_head_form = f"""<hr style="margin:12px 0;border:none;border-top:1px solid #E2E8F0">
        <div style="font-size:11px;color:#6B7280;margin-bottom:6px">Naya Head Add Karein:</div>
        <form method="POST" action="/head/add" style="display:flex;gap:8px">
        <input name="naam" placeholder="Head naam" style="padding:6px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px;flex:1">
        <button class="btn bs" type="submit">Add</button></form>"""

    body = f"""{alerts()}
    <div class="card"><div class="ct">Naya Kharcha Darj Karein</div>
    <form method="POST" action="/akhrajaat">
    <div class="fgrid">
      <div class="fg"><label>Kharcha Head</label><select name="head">{hd_opts}</select></div>
      <div class="fg"><label>Tafseel</label><input name="tafseel" placeholder="Tafseel" required></div>
      <div class="fg"><label>Rakam (PKR)</label><input name="rakam" type="number" step="0.01" placeholder="0" required></div>
      <div class="fg"><label>Kise Diya</label><input name="kise_diya" placeholder="Optional"></div>
      <div class="fg"><label>Tariqa</label><select name="tariqa"><option>Cash</option><option>JazzCash</option><option>EasyPaisa</option><option>Bank Transfer</option><option>Cheque</option></select></div>
      <div class="fg"><label>Tarikh</label><input name="tarikh" type="date" id="dt"></div>
    </div>
    <button class="btn bp" type="submit">✓ Darj Karein</button>
    </form>{add_head_form}</div>
    <div class="g2">
    <div class="card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div class="ct" style="margin:0">Tamam Akhrajaat — Kul: <span class="r">{pk(total)}</span></div>
      <a href="/export/akhrajaat" class="btn bs" style="font-size:11px;padding:5px 12px">⬇ Excel Export</a>
    </div>
    <div class="tw"><table>
      <thead><tr><th>Tarikh</th><th>Head</th><th>Tafseel</th><th>Kise Diya</th><th>Rakam</th><th>Tariqa</th><th>Darj Kiya</th>{'<th></th>' if session.get('role')=='admin' else ''}</tr></thead>
      <tbody>{trs}</tbody></table></div></div>
    <div class="card"><div class="ct">Head Wise Hisaab</div>{hd_summary}</div>
    </div>
    <script>document.getElementById('dt').valueAsDate=new Date();</script>"""
    return layout("Akhrajaat (Expenses)", "ex", body)

@app.route("/akhrajaat/del/<int:i>")
@login_req
@admin_req
def del_ex(i):
    db = get_db()
    db.execute("DELETE FROM akhrajaat WHERE id=?", (i,))
    db.commit(); db.close()
    session.setdefault('_flashes',[]).append(("info","Delete ho gaya"))
    return redirect("/akhrajaat")

@app.route("/head/add", methods=["POST"])
@login_req
@admin_req
def add_head():
    naam = request.form.get("naam","").strip()
    if naam:
        db = get_db()
        try:
            db.execute("INSERT INTO heads (naam) VALUES (?)", (naam,))
            db.commit()
            session.setdefault('_flashes',[]).append(("success",f"{naam} add ho gaya!"))
        except:
            session.setdefault('_flashes',[]).append(("danger","Head already exists"))
        db.close()
    return redirect("/akhrajaat")

# ── COURIER ────────────────────────────────────────────────────────────────────
@app.route("/courier", methods=["GET","POST"])
@login_req
def courier():
    db = get_db()
    if request.method == "POST":
        f = request.form
        mila = float(f.get("mila") or 0)
        chg  = float(f.get("charges") or 0)
        db.execute("INSERT INTO courier (tarikh,courier_naam,qism,parcel_tadaad,mila,charges,net_rakam,reference,darj_kiya) VALUES (?,?,?,?,?,?,?,?,?)",
            (f.get("tarikh") or today(), f.get("courier_naam","TCS"), f.get("qism","COD"),
             float(f.get("parcel_tadaad") or 0), mila, chg, round(mila-chg,2),
             f.get("reference",""), session.get("naam","")))
        db.commit()
        session.setdefault('_flashes',[]).append(("success","Courier payment save ho gayi!"))
        return redirect("/courier")
    rows = db.execute("SELECT * FROM courier ORDER BY created_at DESC").fetchall()
    tm   = db.execute("SELECT COALESCE(SUM(mila),0) FROM courier").fetchone()[0]
    tc   = db.execute("SELECT COALESCE(SUM(charges),0) FROM courier").fetchone()[0]
    db.close()

    trs = "".join([f"""<tr><td>{r['tarikh']}</td><td><span class='badge bg-b'>{r['courier_naam']}</span></td>
        <td>{r['qism']}</td><td>{int(r['parcel_tadaad'])}</td>
        <td class='g'><b>{pk(r['mila'])}</b></td><td class='r'>{pk(r['charges'])}</td>
        <td><b>{pk(r['net_rakam'])}</b></td><td>{r['reference'] or '—'}</td>
        <td style='color:#9CA3AF;font-size:10px'>{r['darj_kiya']}</td>
        {'<td><a href="/courier/del/'+str(r['id'])+'" class="btn bd" onclick="return confirm(\'Delete?\')">Del</a></td>' if session.get('role')=='admin' else ''}
        </tr>""" for r in rows]) or "<tr><td colspan='10' style='text-align:center;color:#9CA3AF;padding:14px'>Koi record nahi</td></tr>"

    body = f"""{alerts()}
    <div class="card"><div class="ct">Courier Payment Darj Karein</div>
    <form method="POST" action="/courier">
    <div class="fgrid">
      <div class="fg"><label>Courier</label><select name="courier_naam"><option>TCS</option><option>Leopards</option><option>M&P</option><option>BlueEx</option><option>Postex</option><option>Other</option></select></div>
      <div class="fg"><label>Qism</label><select name="qism"><option>COD</option><option>Online/Prepaid</option><option>Settlement</option></select></div>
      <div class="fg"><label>Mila (PKR)</label><input name="mila" type="number" step="0.01" placeholder="0" id="mila" oninput="calc()"></div>
      <div class="fg"><label>Charges (PKR)</label><input name="charges" type="number" step="0.01" placeholder="0" id="chg" oninput="calc()"></div>
      <div class="fg"><label>Parcel Tadaad</label><input name="parcel_tadaad" type="number" placeholder="0"></div>
      <div class="fg"><label>Tarikh</label><input name="tarikh" type="date" id="dt"></div>
      <div class="fg"><label>Reference No.</label><input name="reference" placeholder="Sheet no."></div>
    </div>
    <div class="kul" id="net">Net Rakam: Rs 0</div>
    <button class="btn bp" type="submit">✓ Darj Karein</button>
    </form></div>
    <div class="grid" style="margin-bottom:14px">
      <div class="met"><div class="ml">Kul Mila</div><div class="mv g">{pk(tm)}</div></div>
      <div class="met"><div class="ml">Kul Charges</div><div class="mv r">{pk(tc)}</div></div>
      <div class="met"><div class="ml">Net Rakam</div><div class="mv b">{pk(tm-tc)}</div></div>
    </div>
    <div class="card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div class="ct" style="margin:0">Tamam Courier Records</div>
      <a href="/export/courier" class="btn bs" style="font-size:11px;padding:5px 12px">⬇ Excel Export</a>
    </div><div class="tw"><table>
      <thead><tr><th>Tarikh</th><th>Courier</th><th>Qism</th><th>Parcels</th><th>Mila</th><th>Charges</th><th>Net</th><th>Reference</th><th>Darj Kiya</th>{'<th></th>' if session.get('role')=='admin' else ''}</tr></thead>
      <tbody>{trs}</tbody></table></div></div>
    <script>document.getElementById('dt').valueAsDate=new Date();
    function calc(){{var m=parseFloat(document.getElementById('mila').value)||0;var c=parseFloat(document.getElementById('chg').value)||0;document.getElementById('net').textContent='Net Rakam: Rs '+Math.round(m-c).toLocaleString();}}</script>"""
    return layout("Courier Payments", "co", body)

@app.route("/courier/del/<int:i>")
@login_req
@admin_req
def del_co(i):
    db = get_db()
    db.execute("DELETE FROM courier WHERE id=?", (i,))
    db.commit(); db.close()
    session.setdefault('_flashes',[]).append(("info","Delete ho gaya"))
    return redirect("/courier")

# ── INVESTMENT ─────────────────────────────────────────────────────────────────
@app.route("/investment", methods=["GET","POST"])
@login_req
@admin_req
def investment():
    db = get_db()
    if request.method == "POST":
        f = request.form
        db.execute("INSERT INTO investment (tarikh,tafseel,rakam,darj_kiya) VALUES (?,?,?,?)",
            (f.get("tarikh") or today(), f.get("tafseel",""), float(f.get("rakam") or 0), session.get("naam","")))
        db.commit()
        session.setdefault('_flashes',[]).append(("success","Investment save ho gayi!"))
        return redirect("/investment")
    rows  = db.execute("SELECT * FROM investment ORDER BY created_at DESC").fetchall()
    total = db.execute("SELECT COALESCE(SUM(rakam),0) FROM investment").fetchone()[0]
    db.close()

    trs = "".join([f"<tr><td>{r['tarikh']}</td><td>{r['tafseel']}</td><td class='g'><b>{pk(r['rakam'])}</b></td><td style='color:#9CA3AF;font-size:10px'>{r['darj_kiya']}</td><td><a href='/investment/del/{r['id']}' class='btn bd' onclick=\"return confirm('Delete?')\">Del</a></td></tr>" for r in rows]) or "<tr><td colspan='5' style='text-align:center;color:#9CA3AF;padding:14px'>Koi record nahi</td></tr>"

    body = f"""{alerts()}
    <div class="card"><div class="ct">Nai Investment Darj Karein</div>
    <form method="POST" action="/investment">
    <div class="fgrid">
      <div class="fg"><label>Rakam (PKR)</label><input name="rakam" type="number" step="0.01" placeholder="0" required></div>
      <div class="fg"><label>Tafseel / Source</label><input name="tafseel" placeholder="e.g. Apni savings" required></div>
      <div class="fg"><label>Tarikh</label><input name="tarikh" type="date" id="dt"></div>
    </div>
    <button class="btn bs" type="submit">✓ Darj Karein</button>
    </form></div>
    <div class="card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div class="ct" style="margin:0">Tamam Investment — Kul: <span class="g">{pk(total)}</span></div>
      <a href="/export/investment" class="btn bs" style="font-size:11px;padding:5px 12px">⬇ Excel Export</a>
    </div>
    <div class="tw"><table><thead><tr><th>Tarikh</th><th>Tafseel</th><th>Rakam</th><th>Darj Kiya</th><th></th></tr></thead>
    <tbody>{trs}</tbody></table></div></div>
    <script>document.getElementById('dt').valueAsDate=new Date();</script>"""
    return layout("Investment", "inv", body)

@app.route("/investment/del/<int:i>")
@login_req
@admin_req
def del_inv(i):
    db = get_db()
    db.execute("DELETE FROM investment WHERE id=?", (i,))
    db.commit(); db.close()
    session.setdefault('_flashes',[]).append(("info","Delete ho gaya"))
    return redirect("/investment")

# ── LOAN ───────────────────────────────────────────────────────────────────────
@app.route("/loan", methods=["GET","POST"])
@login_req
@admin_req
def loan():
    db = get_db()
    if request.method == "POST":
        f = request.form
        db.execute("INSERT INTO loan (tarikh,shakhs,qism,rakam,darj_kiya) VALUES (?,?,?,?,?)",
            (f.get("tarikh") or today(), f.get("shakhs",""), f.get("qism","Loan Liya"), float(f.get("rakam") or 0), session.get("naam","")))
        db.commit()
        session.setdefault('_flashes',[]).append(("success","Loan save ho gaya!"))
        return redirect("/loan")
    rows  = db.execute("SELECT * FROM loan ORDER BY created_at DESC").fetchall()
    liya  = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Liya'").fetchone()[0]
    wapas = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Wapas'").fetchone()[0]
    db.close()

    trs = "".join([f"<tr><td>{r['tarikh']}</td><td>{r['shakhs']}</td><td><span class='badge {'bg-r' if r['qism']=='Loan Liya' else 'bg-g'}'>{r['qism']}</span></td><td style='font-weight:600;color:{'#DC2626' if r['qism']=='Loan Liya' else '#16A34A'}'>{pk(r['rakam'])}</td><td style='color:#9CA3AF;font-size:10px'>{r['darj_kiya']}</td><td><a href='/loan/del/{r['id']}' class='btn bd' onclick=\"return confirm('Delete?')\">Del</a></td></tr>" for r in rows]) or "<tr><td colspan='6' style='text-align:center;color:#9CA3AF;padding:14px'>Koi record nahi</td></tr>"

    body = f"""{alerts()}
    <div class="card"><div class="ct">Loan Darj Karein</div>
    <form method="POST" action="/loan">
    <div class="fgrid">
      <div class="fg"><label>Shakhs ka Naam</label><input name="shakhs" placeholder="e.g. Bhai, Hamza" required></div>
      <div class="fg"><label>Qism</label><select name="qism"><option>Loan Liya</option><option>Loan Wapas</option></select></div>
      <div class="fg"><label>Rakam (PKR)</label><input name="rakam" type="number" step="0.01" placeholder="0" required></div>
      <div class="fg"><label>Tarikh</label><input name="tarikh" type="date" id="dt"></div>
    </div>
    <button class="btn bp" type="submit">✓ Darj Karein</button>
    </form></div>
    <div class="grid" style="margin-bottom:14px">
      <div class="met"><div class="ml">Loan Liya</div><div class="mv r">{pk(liya)}</div></div>
      <div class="met"><div class="ml">Loan Wapas</div><div class="mv g">{pk(wapas)}</div></div>
      <div class="met"><div class="ml">Baqi</div><div class="mv w">{pk(liya-wapas)}</div></div>
    </div>
    <div class="card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div class="ct" style="margin:0">Tamam Loan Records</div>
      <a href="/export/loan" class="btn bs" style="font-size:11px;padding:5px 12px">⬇ Excel Export</a>
    </div>
    <div class="tw"><table><thead><tr><th>Tarikh</th><th>Shakhs</th><th>Qism</th><th>Rakam</th><th>Darj Kiya</th><th></th></tr></thead>
    <tbody>{trs}</tbody></table></div></div>
    <script>document.getElementById('dt').valueAsDate=new Date();</script>"""
    return layout("Loan Records", "ln", body)

@app.route("/loan/del/<int:i>")
@login_req
@admin_req
def del_loan(i):
    db = get_db()
    db.execute("DELETE FROM loan WHERE id=?", (i,))
    db.commit(); db.close()
    session.setdefault('_flashes',[]).append(("info","Delete ho gaya"))
    return redirect("/loan")

# ── P&L ────────────────────────────────────────────────────────────────────────
@app.route("/pnl")
@login_req
@admin_req
def pnl():
    db = get_db()
    tr  = db.execute("SELECT COALESCE(SUM(mila),0) FROM courier").fetchone()[0]
    tc  = db.execute("SELECT COALESCE(SUM(charges),0) FROM courier").fetchone()[0]
    nc  = tr - tc
    tp  = db.execute("SELECT COALESCE(SUM(kul_rakam),0) FROM kharidari WHERE status!='Unpaid (Baqi)'").fetchone()[0]
    te  = db.execute("SELECT COALESCE(SUM(rakam),0) FROM akhrajaat").fetchone()[0]
    gp  = tr - tp
    np  = gp - tc - te
    ti  = db.execute("SELECT COALESCE(SUM(rakam),0) FROM investment").fetchone()[0]
    ll  = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Liya'").fetchone()[0]
    lw  = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Wapas'").fetchone()[0]
    hds = db.execute("SELECT head, SUM(rakam) t FROM akhrajaat GROUP BY head ORDER BY t DESC").fetchall()
    db.close()

    hd_rows = "".join([f"<div class='pnl-r'><span style='padding-left:12px'>{r['head']}</span><span class='r'>({pk(r['t'])})</span></div>" for r in hds])
    nc_color = "g" if nc >= 0 else "r"
    gp_color = "g" if gp >= 0 else "r"
    np_color = "g" if np >= 0 else "r"

    body = f"""{alerts()}
    <div class="card" style="max-width:600px">
      <div class="ct" style="font-size:14px">Munafa / Nuksan — P&L Report</div>
      <div class="pnl-s">AMDANI — Courier se Mila</div>
      <div class="pnl-r"><span>Courier se Mila (Total)</span><span class="{nc_color}"><b>{pk(tr)}</b></span></div>
      <div class="pnl-r"><span style="padding-left:12px;color:#6B7280">Courier Charges Kate</span><span class="r">({pk(tc)})</span></div>
      <div class="pnl-r pnl-t"><span>Net Amdani</span><span class="{nc_color}">{pk(nc)}</span></div>
      <div class="pnl-s">KHARIDARI (Lagat)</div>
      <div class="pnl-r"><span>Vendor se Kharidari (Ada)</span><span class="r">({pk(tp)})</span></div>
      <div class="pnl-r pnl-t"><span>Gross Munafa</span><span class="{gp_color}">{pk(gp)}</span></div>
      <div class="pnl-s">AKHRAJAAT — Head Wise</div>
      {hd_rows}
      <div class="pnl-r pnl-t"><span>Kul Akhrajaat</span><span class="r">({pk(te)})</span></div>
      <div class="pnl-grand"><span>NET MUNAFA / NUKSAN</span><span class="{np_color}" style="font-size:16px">{pk(np)}</span></div>
      <div class="pnl-s">CAPITAL & LOAN</div>
      <div class="pnl-r"><span>Apni Investment</span><span class="b">{pk(ti)}</span></div>
      <div class="pnl-r"><span>Loan Liya</span><span class="r">{pk(ll)}</span></div>
      <div class="pnl-r"><span>Loan Wapas Kiya</span><span class="g">{pk(lw)}</span></div>
      <div class="pnl-r pnl-t"><span>Baqi Loan</span><span class="w">{pk(ll-lw)}</span></div>
    </div>"""
    return layout("P&L Report", "pnl", body)

# ── USERS ──────────────────────────────────────────────────────────────────────
@app.route("/users", methods=["GET","POST"])
@login_req
@admin_req
def users():
    db = get_db()
    if request.method == "POST":
        f = request.form
        try:
            db.execute("INSERT INTO users (username,password,role,naam) VALUES (?,?,?,?)",
                (f.get("username",""), generate_password_hash(f.get("password","")),
                 f.get("role","employee"), f.get("naam","")))
            db.commit()
            session.setdefault('_flashes',[]).append(("success",f"{f.get('username')} add ho gaya!"))
        except:
            session.setdefault('_flashes',[]).append(("danger","Username already exists!"))
        return redirect("/users")
    rows = db.execute("SELECT id,username,naam,role FROM users ORDER BY id").fetchall()
    db.close()

    trs = "".join([f"<tr><td>{r['id']}</td><td>{r['naam'] or '—'}</td><td>{r['username']}</td><td><span class='badge {'bg-b' if r['role']=='admin' else 'bg-g'}'>{r['role']}</span></td><td>{'<a href=\"/users/del/'+str(r['id'])+'\" class=\"btn bd\" onclick=\"return confirm(\'Delete?\')\" >Del</a>' if r['id'] != session.get('uid') else '<span style=\"font-size:10px;color:#9CA3AF\">Aap</span>'}</td></tr>" for r in rows])

    body = f"""{alerts()}
    <div class="card"><div class="ct">Naya User Add Karein</div>
    <form method="POST" action="/users">
    <div class="fgrid">
      <div class="fg"><label>Naam</label><input name="naam" placeholder="Employee naam" required></div>
      <div class="fg"><label>Username</label><input name="username" placeholder="login username" required></div>
      <div class="fg"><label>Password</label><input name="password" type="password" placeholder="password" required></div>
      <div class="fg"><label>Role</label><select name="role"><option value="employee">Employee (limited)</option><option value="admin">Admin (full access)</option></select></div>
    </div>
    <button class="btn bp" type="submit">✓ Add Karein</button>
    </form>
    <div style="margin-top:10px;padding:10px;background:#FEF3C7;border-radius:7px;font-size:11px;color:#92400E">
      <b>Employee:</b> Kharidari, Akhrajaat, Courier add/dekh sakta hai.<br>
      <b>Admin:</b> Sab kuch — Delete, Investment, Loan, P&L, Users.
    </div></div>
    <div class="card"><div class="ct">Tamam Users</div>
    <div class="tw"><table><thead><tr><th>ID</th><th>Naam</th><th>Username</th><th>Role</th><th></th></tr></thead>
    <tbody>{trs}</tbody></table></div></div>"""
    return layout("Users", "usr", body)

@app.route("/users/del/<int:i>")
@login_req
@admin_req
def del_user(i):
    if i == session.get("uid"):
        session.setdefault('_flashes',[]).append(("danger","Aap khud ko delete nahi kar sakte"))
        return redirect("/users")
    db = get_db()
    db.execute("DELETE FROM users WHERE id=?", (i,))
    db.commit(); db.close()
    session.setdefault('_flashes',[]).append(("info","User delete ho gaya"))
    return redirect("/users")

# ── EXPORT CSV ────────────────────────────────────────────────────────────────
import csv, io
from flask import Response

def make_csv(headers, rows):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    output.seek(0)
    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment"}
    )

@app.route("/export/kharidari")
@login_req
def export_kharidari():
    db = get_db()
    rows = db.execute("SELECT tarikh,vendor,maal,qty,unit,daam,kul_rakam,status,notes,darj_kiya FROM kharidari ORDER BY created_at DESC").fetchall()
    db.close()
    resp = make_csv(
        ["Tarikh","Vendor","Maal","Qty","Unit","Daam per Unit","Kul Rakam","Status","Notes","Darj Kiya"],
        [list(r) for r in rows]
    )
    resp.headers["Content-Disposition"] = "attachment; filename=kharidari.csv"
    return resp

@app.route("/export/akhrajaat")
@login_req
def export_akhrajaat():
    db = get_db()
    rows = db.execute("SELECT tarikh,head,tafseel,kise_diya,rakam,tariqa,darj_kiya FROM akhrajaat ORDER BY created_at DESC").fetchall()
    db.close()
    resp = make_csv(
        ["Tarikh","Head","Tafseel","Kise Diya","Rakam","Tariqa","Darj Kiya"],
        [list(r) for r in rows]
    )
    resp.headers["Content-Disposition"] = "attachment; filename=akhrajaat.csv"
    return resp

@app.route("/export/courier")
@login_req
def export_courier():
    db = get_db()
    rows = db.execute("SELECT tarikh,courier_naam,qism,parcel_tadaad,mila,charges,net_rakam,reference,darj_kiya FROM courier ORDER BY created_at DESC").fetchall()
    db.close()
    resp = make_csv(
        ["Tarikh","Courier","Qism","Parcel Tadaad","Mila","Charges","Net Rakam","Reference","Darj Kiya"],
        [list(r) for r in rows]
    )
    resp.headers["Content-Disposition"] = "attachment; filename=courier.csv"
    return resp

@app.route("/export/investment")
@login_req
@admin_req
def export_investment():
    db = get_db()
    rows = db.execute("SELECT tarikh,tafseel,rakam,darj_kiya FROM investment ORDER BY created_at DESC").fetchall()
    db.close()
    resp = make_csv(
        ["Tarikh","Tafseel","Rakam","Darj Kiya"],
        [list(r) for r in rows]
    )
    resp.headers["Content-Disposition"] = "attachment; filename=investment.csv"
    return resp

@app.route("/export/loan")
@login_req
@admin_req
def export_loan():
    db = get_db()
    rows = db.execute("SELECT tarikh,shakhs,qism,rakam,darj_kiya FROM loan ORDER BY created_at DESC").fetchall()
    db.close()
    resp = make_csv(
        ["Tarikh","Shakhs","Qism","Rakam","Darj Kiya"],
        [list(r) for r in rows]
    )
    resp.headers["Content-Disposition"] = "attachment; filename=loan.csv"
    return resp

@app.route("/export/all")
@login_req
@admin_req
def export_all():
    db = get_db()
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["=== KHARIDARI ==="])
    writer.writerow(["Tarikh","Vendor","Maal","Qty","Unit","Daam","Kul Rakam","Status","Notes"])
    for r in db.execute("SELECT tarikh,vendor,maal,qty,unit,daam,kul_rakam,status,notes FROM kharidari ORDER BY tarikh DESC").fetchall():
        writer.writerow(list(r))

    writer.writerow([])
    writer.writerow(["=== AKHRAJAAT ==="])
    writer.writerow(["Tarikh","Head","Tafseel","Kise Diya","Rakam","Tariqa"])
    for r in db.execute("SELECT tarikh,head,tafseel,kise_diya,rakam,tariqa FROM akhrajaat ORDER BY tarikh DESC").fetchall():
        writer.writerow(list(r))

    writer.writerow([])
    writer.writerow(["=== COURIER ==="])
    writer.writerow(["Tarikh","Courier","Qism","Parcels","Mila","Charges","Net Rakam","Reference"])
    for r in db.execute("SELECT tarikh,courier_naam,qism,parcel_tadaad,mila,charges,net_rakam,reference FROM courier ORDER BY tarikh DESC").fetchall():
        writer.writerow(list(r))

    writer.writerow([])
    writer.writerow(["=== INVESTMENT ==="])
    writer.writerow(["Tarikh","Tafseel","Rakam"])
    for r in db.execute("SELECT tarikh,tafseel,rakam FROM investment ORDER BY tarikh DESC").fetchall():
        writer.writerow(list(r))

    writer.writerow([])
    writer.writerow(["=== LOAN ==="])
    writer.writerow(["Tarikh","Shakhs","Qism","Rakam"])
    for r in db.execute("SELECT tarikh,shakhs,qism,rakam FROM loan ORDER BY tarikh DESC").fetchall():
        writer.writerow(list(r))

    db.close()
    output.seek(0)
    resp = Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8"
    )
    resp.headers["Content-Disposition"] = "attachment; filename=bizhisaab_poora_data.csv"
    return resp

# ── START ──────────────────────────────────────────────────────────────────────
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
