from flask import Flask, request, redirect, session, Response
from werkzeug.security import generate_password_hash, check_password_hash
import os, csv, io, psycopg2, psycopg2.extras
from datetime import date, datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "bizhisaab2025secret"
from flask_cors import CORS
import requests as ext_req
CORS(app)
DATABASE_URL = os.environ.get("DATABASE_URL", "")

CSS = """
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:'Segoe UI',sans-serif}
body{background:#F1F5F9;display:flex;min-height:100vh}
a{text-decoration:none;color:inherit}
.sb{width:210px;background:#0F172A;display:flex;flex-direction:column;min-height:100vh;flex-shrink:0;position:fixed;top:0;left:0;height:100%;overflow-y:auto}
.sb-brand{padding:16px;color:#fff;font-size:14px;font-weight:700;border-bottom:1px solid #1e293b}
.sb-brand span{color:#3B82F6}
.sb a{display:block;padding:10px 16px;color:#94A3B8;font-size:12px;transition:.15s}
.sb a:hover,.sb a.on{background:#3B82F6;color:#fff}
.sb-foot{margin-top:auto;padding:12px 16px;font-size:11px;color:#475569;border-top:1px solid #1e293b}
.sb-foot a{color:#EF4444;display:block;margin-top:6px}
.main{margin-left:210px;flex:1;display:flex;flex-direction:column}
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
.calc-info{background:#EFF6FF;border-radius:8px;padding:10px 14px;margin-bottom:10px;font-size:12px;color:#1E40AF;display:flex;gap:16px;flex-wrap:wrap}
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
@media(max-width:700px){.sb{display:block;position:fixed;z-index:999;height:100%;transform:translateX(-100%);transition:.3s}.sb.open{transform:translateX(0)}.main{margin-left:0}.g2{grid-template-columns:1fr}.grid{grid-template-columns:1fr 1fr}.mob-menu{display:block!important}}
</style>
"""

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    return conn

def qry(conn, sql, params=()):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params)
    return cur

def init_db():
    conn = get_db()
    cur = conn.cursor()
    for sql in [
        "CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT DEFAULT 'employee', naam TEXT)",
        "CREATE TABLE IF NOT EXISTS purchases (id SERIAL PRIMARY KEY, date TEXT, vendor TEXT, product TEXT, quantity REAL, unit TEXT, total_amount REAL, per_unit_price REAL, status TEXT, notes TEXT, added_by TEXT, created_at TIMESTAMP DEFAULT NOW())",
        "CREATE TABLE IF NOT EXISTS expenses (id SERIAL PRIMARY KEY, date TEXT, category TEXT, description TEXT, paid_to TEXT, amount REAL, payment_method TEXT, added_by TEXT, created_at TIMESTAMP DEFAULT NOW())",
        "CREATE TABLE IF NOT EXISTS courier (id SERIAL PRIMARY KEY, date TEXT, courier_name TEXT, type TEXT, parcels REAL, total_cod REAL, charges REAL, net_amount REAL, reference TEXT, added_by TEXT, account_name TEXT DEFAULT 'Default', created_at TIMESTAMP DEFAULT NOW())",
        "CREATE TABLE IF NOT EXISTS courier_accounts (id SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL, courier TEXT, bank_name TEXT, bank_holder TEXT, active BOOLEAN DEFAULT TRUE)",
        "CREATE TABLE IF NOT EXISTS ad_accounts (id SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL, platform TEXT, currency TEXT DEFAULT 'PKR', site TEXT, active BOOLEAN DEFAULT TRUE)",
        "CREATE TABLE IF NOT EXISTS ad_spend (id SERIAL PRIMARY KEY, date TEXT, ad_account_id INT, ad_account_name TEXT, platform TEXT, site TEXT, dollar_amount REAL DEFAULT 0, dollar_rate REAL DEFAULT 0, pkr_amount REAL, tax_amount REAL DEFAULT 0, total_pkr REAL, description TEXT, added_by TEXT, created_at TIMESTAMP DEFAULT NOW())",
        "CREATE TABLE IF NOT EXISTS investment (id SERIAL PRIMARY KEY, date TEXT, description TEXT, amount REAL, added_by TEXT, created_at TIMESTAMP DEFAULT NOW())",
        "CREATE TABLE IF NOT EXISTS loans (id SERIAL PRIMARY KEY, date TEXT, person TEXT, type TEXT, amount REAL, added_by TEXT, created_at TIMESTAMP DEFAULT NOW())",
        "CREATE TABLE IF NOT EXISTS exp_categories (id SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL)",
        "CREATE TABLE IF NOT EXISTS cashbank (id SERIAL PRIMARY KEY, date TEXT, account TEXT, type TEXT, description TEXT, amount REAL, added_by TEXT, created_at TIMESTAMP DEFAULT NOW())",
    ]:
        cur.execute(sql)
    cur.execute("SELECT id FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username,password,role,naam) VALUES (%s,%s,%s,%s)",
            ("admin", generate_password_hash("admin123"), "admin", "Mudassar"))
    for c in ["Transport/Rickshaw","Rent","Salaries","Marketing & Ads","Utilities","Packaging","Shipping","Bank Charges","Miscellaneous"]:
        cur.execute("INSERT INTO exp_categories (name) VALUES (%s) ON CONFLICT DO NOTHING", (c,))
    # Default courier accounts
    default_accounts = [
        ("Pakmade", "DigiDokaan", "HBL EcomLink", "Mudassar"),
        ("Fridostore", "DigiDokaan", "Faysal Bank", "Asif"),
        ("WomenComfort", "DigiDokaan", "HBL", "Muzamil"),
        ("Home and Glow", "Daewoo", "HBL", "Muzamil"),
    ]
    for acc in default_accounts:
        cur.execute("INSERT INTO courier_accounts (name,courier,bank_name,bank_holder) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING", acc)
    # Default ad accounts
    default_ads = [
        ("Math and Matter", "Facebook", "PKR", "Sehatkart"),
        ("Facebook Account 2", "Facebook", "USD", ""),
        ("Facebook Account 3", "Facebook", "USD", ""),
        ("Facebook Account 4", "Facebook", "USD", ""),
        ("TikTok Main", "TikTok", "USD", ""),
    ]
    for ad in default_ads:
        cur.execute("INSERT INTO ad_accounts (name,platform,currency,site) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING", ad)
    # Add missing columns
    try:
        cur.execute("ALTER TABLE courier ADD COLUMN IF NOT EXISTS account_name TEXT DEFAULT 'Default'")
    except: conn.rollback()
    try:
        cur.execute("ALTER TABLE ad_spend ADD COLUMN IF NOT EXISTS period_from TEXT DEFAULT ''")
        cur.execute("ALTER TABLE ad_spend ADD COLUMN IF NOT EXISTS period_to TEXT DEFAULT ''")
    except: conn.rollback()
    conn.commit()
    conn.close()

def is_admin():
    return session.get("role") == "admin"

def hide_amt(amount_html):
    """Hide amount for employees"""
    if is_admin():
        return amount_html
    return "<span style='color:#9CA3AF;font-size:11px'>—</span>"

def hide_pk(n):
    """Show amount only to admin"""
    if is_admin():
        return pk(n)
    return "—"

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
            session.setdefault('_flashes',[]).append(("danger","Admin access only"))
            return redirect("/dashboard")
        return f(*a, **kw)
    return dec

def pk(n):
    try: return f"Rs {int(float(n or 0)):,}"
    except: return "Rs 0"

def today(): return str(date.today())

def flashes():
    msgs = session.pop('_flashes', [])
    return "".join([f'<div class="alert {"al-s" if c=="success" else "al-d" if c=="danger" else "al-i"}">{m}</div>' for c,m in msgs])

ACCOUNTS = ["Cash in Hand","Bank (HBL/MCB)","JazzCash","EasyPaisa"]

def layout(title, page, body):
    admin_links = ""
    if session.get("role") == "admin":
        admin_links = f"""
        <a href="/adspend" class="{'on' if page=='ads' else ''}">📣 Ad Spend</a>
        <a href="/cashbank" class="{'on' if page=='cb' else ''}">💵 Cash & Bank</a>
        <a href="/investment" class="{'on' if page=='inv' else ''}">💰 Investment</a>
        <a href="/loan" class="{'on' if page=='ln' else ''}">🏦 Loans</a>
        <a href="/pnl" class="{'on' if page=='pnl' else ''}">📊 P&L Report</a>
        <a href="/import" class="{'on' if page=='imp' else ''}">⬆ Import Data</a>
        <a href="/users" class="{'on' if page=='usr' else ''}">👥 Users</a>
        """
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
<title>BizHisaab - {title}</title>{CSS}</head><body>
    <nav class="sb">
      <div class="sb-brand">📊 <span>Biz</span>Hisaab</div>
      <a href="/dashboard" class="{'on' if page=='dash' else ''}">🏠 Dashboard</a>
      <a href="/purchases-summary" class="{'on' if page=='pur' else ''}">📦 Purchases</a>
      <a href="/partial-payments" class="{'on' if page=='pp' else ''}">💳 Partial Payments</a>
      <a href="/expenses" class="{'on' if page=='exp' else ''}">💸 Expenses</a>
      <a href="/courier" class="{'on' if page=='co' else ''}">🚚 Courier</a>
      <a href="/tracking" class="{'on' if page=='trk' else ''}">📡 Courier Tracking</a>
      <a href="/returns" class="{'on' if page=='ret' else ''}">↩ Returns</a>
      <a href="/cashflow" class="{'on' if page=='cf' else ''}">💵 Cash Flow</a>
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
    </div></body></html>"""
# ── LOGIN ─────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET","POST"])
def login():
    if "uid" in session: return redirect("/dashboard")
    err = ""
    if request.method == "POST":
        conn = get_db()
        cur = qry(conn, "SELECT * FROM users WHERE username=%s", (request.form.get("username",""),))
        u = cur.fetchone()
        conn.close()
        if u and check_password_hash(u["password"], request.form.get("password","")):
            session["uid"]  = u["id"]
            session["naam"] = u["naam"] or u["username"]
            session["role"] = u["role"]
            return redirect("/dashboard")
        err = '<div class="alert al-d">Invalid username or password!</div>'
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>BizHisaab — Login</title>{CSS}
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
    <input class="inp" name="username" placeholder="Enter username" required autofocus>
    <label class="lbl">Password</label>
    <input class="inp" type="password" name="password" placeholder="Enter password" required>
    <button class="lbtn" type="submit">Login</button>
    </form>
    <div class="hint">Default: admin / admin123</div>
    </div></body></html>"""

@app.route("/debug/adaccounts")
@login_req
def debug_adaccounts():
    conn = get_db()
    accs = qry(conn,"SELECT id,name,platform,currency FROM ad_accounts").fetchall()
    conn.close()
    result = "<br>".join([f"ID:{a['id']} | {a['name']} | {a['platform']} | Currency:{a['currency']}" for a in accs])
    return f"<pre>{result}</pre>"

@app.route("/logout")
def logout():
    session.clear(); return redirect("/")

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
@app.route("/dashboard")
@login_req
def dashboard():
    conn = get_db()
    pu  = qry(conn,"SELECT COALESCE(SUM(total_amount),0) as v FROM purchases WHERE status!='Unpaid'").fetchone()["v"] or 0
    ex  = qry(conn,"SELECT COALESCE(SUM(amount),0) as v FROM expenses").fetchone()["v"] or 0
    co  = qry(conn,"SELECT COALESCE(SUM(net_amount),0) as v FROM courier").fetchone()["v"] or 0
    tad = qry(conn,"SELECT COALESCE(SUM(total_pkr),0) as v FROM ad_spend").fetchone()["v"] or 0
    inv = qry(conn,"SELECT COALESCE(SUM(amount),0) as v FROM investment").fetchone()["v"] or 0
    ll  = qry(conn,"SELECT COALESCE(SUM(amount),0) as v FROM loans WHERE type='Loan Taken'").fetchone()["v"] or 0
    lw  = qry(conn,"SELECT COALESCE(SUM(amount),0) as v FROM loans WHERE type='Loan Repaid'").fetchone()["v"] or 0
    net = float(co) - float(pu) - float(ex) - float(tad)
    rpu = qry(conn,"SELECT * FROM purchases ORDER BY created_at DESC LIMIT 5").fetchall()
    rco = qry(conn,"SELECT * FROM courier ORDER BY created_at DESC LIMIT 5").fetchall()
    rex = qry(conn,"SELECT * FROM expenses ORDER BY created_at DESC LIMIT 5").fetchall()
    conn.close()

    pu_rows = "".join([f"<tr><td>{r['date']}</td><td>{r['vendor']}</td><td>{r['product']}</td><td>{int(r['quantity'] or 0)}</td><td>{r['unit']}</td>{'<td class=\"g\"><b>'+pk(r['total_amount'])+'</b></td>' if is_admin() else ''}<td><span class='badge {'bg-g' if r['status']=='Paid' else 'bg-r' if r['status']=='Unpaid' else 'bg-w'}'>{r['status']}</span></td></tr>" for r in rpu]) or "<tr><td colspan='7' style='text-align:center;color:#9CA3AF;padding:14px'>No records</td></tr>"
    co_rows = "".join([f"<tr><td>{r['date']}</td><td><span class='badge bg-b'>{r['courier_name']}</span></td><td>{r['type']}</td>{'<td class=\"g\"><b>'+pk(r['net_amount'])+'</b></td>' if is_admin() else ''}</tr>" for r in rco]) or "<tr><td colspan='4' style='text-align:center;color:#9CA3AF;padding:14px'>No records</td></tr>"
    ex_rows = "".join([f"<tr><td>{r['date']}</td><td><span class='badge bg-w'>{r['category']}</span></td><td>{r['description']}</td>{'<td class=\"r\"><b>'+pk(r['amount'])+'</b></td>' if is_admin() else ''}</tr>" for r in rex]) or "<tr><td colspan='4' style='text-align:center;color:#9CA3AF;padding:14px'>No records</td></tr>"

    body = f"""{flashes()}
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div style="font-size:12px;color:#6B7280">Business Overview</div>
      {f'<a href="/export/all" class="btn bs" style="font-size:12px">⬇ Export All Data (Excel)</a>' if is_admin() else ''}
    </div>
    {f'''<div class="grid">
      <div class="met"><div class="ml">Courier Income</div><div class="mv g">{pk(co)}</div></div>
      <div class="met"><div class="ml">Total Purchases</div><div class="mv r">{pk(pu)}</div></div>
      <div class="met"><div class="ml">Total Expenses</div><div class="mv r">{pk(ex)}</div></div>
      <div class="met"><div class="ml">Ad Spend</div><div class="mv r">{pk(tad)}</div></div>
      <div class="met"><div class="ml">Net Profit/Loss</div><div class="mv {"g" if net>=0 else "r"}">{pk(net)}</div></div>
      <div class="met"><div class="ml">Investment</div><div class="mv b">{pk(inv)}</div></div>
      <div class="met"><div class="ml">Outstanding Loan</div><div class="mv w">{pk(float(ll)-float(lw))}</div></div>
    </div>''' if is_admin() else '<div class="card" style="background:#EFF6FF;border:none"><div style="font-size:13px;color:#1E40AF;padding:8px">👋 Welcome! Use sidebar to add Purchases, Expenses, Courier or Ad Spend.</div></div>'}
    <div class="g2">
      <div class="card"><div class="ct">Recent Purchases</div><div class="tw"><table>
        <thead><tr><th>Date</th><th>Vendor</th><th>Product</th><th>Qty</th><th>Unit</th>{f'<th>Amount</th>' if is_admin() else ''}<th>Status</th></tr></thead>
        <tbody>{pu_rows}</tbody></table></div></div>
      <div class="card"><div class="ct">Recent Courier</div><div class="tw"><table>
        <thead><tr><th>Date</th><th>Courier</th><th>Type</th>{f'<th>Net Amount</th>' if is_admin() else ''}</tr></thead>
        <tbody>{co_rows}</tbody></table></div></div>
    </div>
    <div class="card"><div class="ct">Recent Expenses</div><div class="tw"><table>
      <thead><tr><th>Date</th><th>Category</th><th>Description</th>{f'<th>Amount</th>' if is_admin() else ''}</tr></thead>
      <tbody>{ex_rows}</tbody></table></div></div>"""
    return layout("Dashboard","dash",body)

# ── PURCHASES ─────────────────────────────────────────────────────────────────
@app.route("/purchases", methods=["GET","POST"])
@login_req
def purchases():
    conn = get_db()
    if request.method == "POST":
        f = request.form
        qty   = float(f.get("quantity") or 1)
        total = float(f.get("total_amount") or 0)
        per_u = round(total/qty,2) if qty else 0
        st    = f.get("status","Paid")
        qry(conn,"INSERT INTO purchases (date,vendor,product,quantity,unit,total_amount,per_unit_price,status,notes,added_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (f.get("date") or today(), f.get("vendor",""), f.get("product",""), qty, f.get("unit","Piece"), total, per_u, st, f.get("notes",""), session.get("naam","")))
        conn.commit(); conn.close()
        session.setdefault('_flashes',[]).append(("success","Purchase saved!"))
        return redirect("/purchases")
    rows   = qry(conn,"SELECT * FROM purchases ORDER BY created_at DESC").fetchall()
    total  = qry(conn,"SELECT COALESCE(SUM(total_amount),0) as v FROM purchases").fetchone()["v"] or 0
    paid   = qry(conn,"SELECT COALESCE(SUM(total_amount),0) as v FROM purchases WHERE status='Paid'").fetchone()["v"] or 0
    unpaid = qry(conn,"SELECT COALESCE(SUM(total_amount),0) as v FROM purchases WHERE status='Unpaid'").fetchone()["v"] or 0
    conn.close()

    pur_rows_list = []
    for r in rows:
        amt_cols = f"<td class='b'><b>{pk(r['per_unit_price'])}</b></td><td class='g'><b>{pk(r['total_amount'])}</b></td>"
        del_btn = ("<td><a href='/purchases/del/" + str(r["id"]) + "' class='btn bd' onclick='return confirm(chr(39)+chr(68)+chr(101)+chr(108)+chr(101)+chr(116)+chr(101)+chr(63)+chr(39))'>Del</a></td>") if is_admin() else ""
        badge = "bg-g" if r['status']=='Paid' else "bg-r" if r['status']=='Unpaid' else "bg-w"
        pur_rows_list.append(f"<tr><td>{r['date']}</td><td>{r['vendor']}</td><td>{r['product']}</td><td>{int(r['quantity'] or 0)}</td><td>{r['unit']}</td>{amt_cols}<td><span class='badge {badge}'>{r['status']}</span></td><td style='color:#9CA3AF;font-size:10px'>{r['added_by']}</td>{del_btn}</tr>")
    trs = "".join(pur_rows_list) or "<tr><td colspan='10' style='text-align:center;color:#9CA3AF;padding:14px'>No records</td></tr>"

    body = f"""{flashes()}
    <div class="card"><div class="ct">Add New Purchase</div>
    <form method="POST" action="/purchases">
    <div class="fgrid">
      <div class="fg"><label>Vendor Name</label><input name="vendor" placeholder="Vendor name" required></div>
      <div class="fg"><label>Product Name</label><input name="product" placeholder="Product name" required></div>
      <div class="fg"><label>Quantity</label><input name="quantity" type="number" step="0.01" value="1" id="qty" oninput="calc()"></div>
      <div class="fg"><label>Unit</label><select name="unit" onchange="calc()"><option>Piece</option><option>Dozen</option><option>Box</option><option>Kg</option><option>Man</option><option>Other</option></select></div>
      <div class="fg"><label>Total Amount Paid (PKR)</label><input name="total_amount" type="number" step="0.01" placeholder="0" id="tot" oninput="calc()"></div>
      <div class="fg"><label>Payment Status</label><select name="status"><option>Paid</option><option>Unpaid</option><option>Partial</option></select></div>
      <div class="fg"><label>Date</label><input name="date" type="date" id="dt"></div>
      <div class="fg"><label>Notes</label><input name="notes" placeholder="Optional"></div>
    </div>
    <div class="calc-info"><span>Per Unit: <b id="pu">Rs 0</b></span><span>Total: <b id="ts">Rs 0</b></span></div>
    <button class="btn bp" type="submit">✓ Save Purchase</button>
    </form></div>
    <div class="grid" style="margin-bottom:14px">
      <div class="met"><div class="ml">Total</div><div class="mv">{pk(total)}</div></div>
      <div class="met"><div class="ml">Paid</div><div class="mv g">{pk(paid)}</div></div>
      <div class="met"><div class="ml">Unpaid</div><div class="mv r">{pk(unpaid)}</div></div>
    </div>
    <div class="card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div class="ct" style="margin:0">All Purchases</div>
      <a href="/export/purchases" class="btn bs" style="font-size:11px;padding:5px 12px">⬇ Export</a>
    </div><div class="tw"><table>
      <thead><tr><th>Date</th><th>Vendor</th><th>Product</th><th>Qty</th><th>Unit</th><th>Per Unit</th><th>Total</th><th>Status</th><th>Added By</th>{"<th></th>" if is_admin() else ""}</tr></thead>
      <tbody>{trs}</tbody></table></div></div>
    <script>document.getElementById('dt').valueAsDate=new Date();
    function calc(){{var q=parseFloat(document.getElementById('qty').value)||0;var t=parseFloat(document.getElementById('tot').value)||0;
    document.getElementById('pu').textContent='Rs '+(q>0?Math.round(t/q*100)/100:0).toLocaleString();
    document.getElementById('ts').textContent='Rs '+Math.round(t).toLocaleString();}}</script>"""
    return layout("Purchases","pur",body)

@app.route("/purchases/del/<int:i>")
@login_req
@admin_req
def del_purchase(i):
    conn = get_db()
    qry(conn,"DELETE FROM purchases WHERE id=%s",(i,))
    conn.commit(); conn.close()
    session.setdefault('_flashes',[]).append(("info","Deleted"))
    return redirect("/purchases")

# ── EXPENSES ──────────────────────────────────────────────────────────────────
@app.route("/expenses", methods=["GET","POST"])
@login_req
def expenses():
    conn = get_db()
    cats = [r["name"] for r in qry(conn,"SELECT name FROM exp_categories ORDER BY name").fetchall()]
    if request.method == "POST":
        f = request.form
        qry(conn,"INSERT INTO expenses (date,category,description,paid_to,amount,payment_method,added_by) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (f.get("date") or today(), f.get("category",""), f.get("description",""),
             f.get("paid_to",""), float(f.get("amount") or 0), f.get("payment_method","Cash"), session.get("naam","")))
        conn.commit(); conn.close()
        session.setdefault('_flashes',[]).append(("success","Expense saved!"))
        return redirect("/expenses")
    rows  = qry(conn,"SELECT * FROM expenses ORDER BY created_at DESC").fetchall()
    total = qry(conn,"SELECT COALESCE(SUM(amount),0) as v FROM expenses").fetchone()["v"] or 0
    by_cat= qry(conn,"SELECT category, SUM(amount) t FROM expenses GROUP BY category ORDER BY t DESC").fetchall()
    conn.close()

    cat_opts = "".join([f"<option>{c}</option>" for c in cats])
    trs = "".join([f"""<tr><td>{r['date']}</td><td><span class='badge bg-w'>{r['category']}</span></td>
        <td>{r['description']}</td><td>{r['paid_to'] or '—'}</td>
        <td class='r'><b>{pk(r['amount'])}</b></td><td>{r['payment_method']}</td>
        <td style='color:#9CA3AF;font-size:10px'>{r['added_by']}</td>
        {'<td><a href="/expenses/del/'+str(r["id"])+'" class="btn bd" onclick="return confirm(\'Delete?\')">Del</a></td>' if session.get('role')=='admin' else ''}
        </tr>""" for r in rows]) or "<tr><td colspan='8' style='text-align:center;color:#9CA3AF;padding:14px'>No records</td></tr>"
    cat_sum = "".join([f"<div style='display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #F1F5F9;font-size:12px'><span>{r['category']}</span><span class='r'><b>{pk(r['t'])}</b></span></div>" for r in by_cat]) or "<div style='color:#9CA3AF;font-size:12px;padding:8px'>No data</div>"

    add_cat = ""
    if session.get("role") == "admin":
        add_cat = """<hr style="margin:12px 0;border:none;border-top:1px solid #E2E8F0">
        <div style="font-size:11px;color:#6B7280;margin-bottom:6px">Add New Category:</div>
        <form method="POST" action="/expenses/category" style="display:flex;gap:8px">
        <input name="name" placeholder="Category name" style="padding:6px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px;flex:1">
        <button class="btn bs" type="submit">Add</button></form>"""

    body = f"""{flashes()}
    <div class="card"><div class="ct">Add New Expense</div>
    <form method="POST" action="/expenses">
    <div class="fgrid">
      <div class="fg"><label>Category</label><select name="category">{cat_opts}</select></div>
      <div class="fg"><label>Description</label><input name="description" placeholder="Details" required></div>
      <div class="fg"><label>Amount (PKR)</label><input name="amount" type="number" step="0.01" placeholder="0" required></div>
      <div class="fg"><label>Paid To</label><input name="paid_to" placeholder="Optional"></div>
      <div class="fg"><label>Payment Method</label><select name="payment_method"><option>Cash</option><option>JazzCash</option><option>EasyPaisa</option><option>Bank Transfer</option><option>Cheque</option></select></div>
      <div class="fg"><label>Date</label><input name="date" type="date" id="dt"></div>
    </div>
    <button class="btn bp" type="submit">✓ Save Expense</button>
    </form>{add_cat}</div>
    <div class="g2">
    <div class="card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div class="ct" style="margin:0">All Expenses — Total: <span class="r">{pk(total)}</span></div>
      {f'<a href="/export/expenses" class="btn bs" style="font-size:11px;padding:5px 12px">⬇ Export</a>' if is_admin() else ''}
    </div><div class="tw"><table>
      <thead><tr><th>Date</th><th>Category</th><th>Description</th><th>Paid To</th><th>Amount</th><th>Method</th><th>Added By</th>{'<th></th>' if session.get('role')=='admin' else ''}</tr></thead>
      <tbody>{trs}</tbody></table></div></div>
    <div class="card"><div class="ct">Category Breakdown</div>{cat_sum}</div>
    </div>
    <script>document.getElementById('dt').valueAsDate=new Date();</script>"""
    return layout("Expenses","exp",body)

@app.route("/expenses/del/<int:i>")
@login_req
@admin_req
def del_expense(i):
    conn = get_db()
    qry(conn,"DELETE FROM expenses WHERE id=%s",(i,))
    conn.commit(); conn.close()
    session.setdefault('_flashes',[]).append(("info","Deleted"))
    return redirect("/expenses")

@app.route("/expenses/category", methods=["POST"])
@login_req
@admin_req
def add_category():
    name = request.form.get("name","").strip()
    if name:
        conn = get_db()
        qry(conn,"INSERT INTO exp_categories (name) VALUES (%s) ON CONFLICT DO NOTHING",(name,))
        conn.commit(); conn.close()
        session.setdefault('_flashes',[]).append(("success",f"'{name}' added!"))
    return redirect("/expenses")

# ── COURIER ───────────────────────────────────────────────────────────────────
@app.route("/courier", methods=["GET","POST"])
@login_req
def courier():
    conn = get_db()
    accounts = qry(conn,"SELECT * FROM courier_accounts WHERE active=TRUE ORDER BY name").fetchall()
    if request.method == "POST":
        f   = request.form
        cod = float(f.get("total_cod") or 0)
        chg = float(f.get("charges") or 0)
        acc = f.get("account_name","Default")
        # Auto-set courier name from account
        acc_data = next((a for a in accounts if a['name']==acc), None)
        courier_nm = acc_data['courier'] if acc_data else f.get("courier_name","Other")
        qry(conn,"INSERT INTO courier (date,courier_name,type,parcels,total_cod,charges,net_amount,reference,added_by,account_name) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (f.get("date") or today(), courier_nm, f.get("type","COD"),
             float(f.get("parcels") or 0), cod, chg, round(cod-chg,2),
             f.get("reference",""), session.get("naam",""), acc))
        conn.commit(); conn.close()
        session.setdefault('_flashes',[]).append(("success","Courier payment saved!"))
        return redirect("/courier")

    acc_filter = request.args.get("acc","")
    if acc_filter:
        rows = qry(conn,"SELECT * FROM courier WHERE account_name=%s ORDER BY created_at DESC",(acc_filter,)).fetchall()
        t_cod = qry(conn,"SELECT COALESCE(SUM(total_cod),0) as v FROM courier WHERE account_name=%s",(acc_filter,)).fetchone()["v"] or 0
        t_chg = qry(conn,"SELECT COALESCE(SUM(charges),0) as v FROM courier WHERE account_name=%s",(acc_filter,)).fetchone()["v"] or 0
    else:
        rows  = qry(conn,"SELECT * FROM courier ORDER BY created_at DESC").fetchall()
        t_cod = qry(conn,"SELECT COALESCE(SUM(total_cod),0) as v FROM courier").fetchone()["v"] or 0
        t_chg = qry(conn,"SELECT COALESCE(SUM(charges),0) as v FROM courier").fetchone()["v"] or 0

    # Per account summary
    acc_summary = qry(conn,"""SELECT account_name,
        COUNT(*) as cnt,
        COALESCE(SUM(total_cod),0) as total_cod,
        COALESCE(SUM(charges),0) as charges,
        COALESCE(SUM(net_amount),0) as net
        FROM courier GROUP BY account_name ORDER BY net DESC""").fetchall()
    conn.close()

    # Account filter buttons
    acc_btns = f"<a href='/courier' class='btn {'bp' if not acc_filter else ''}' style='font-size:11px;padding:5px 12px;margin-right:4px;margin-bottom:4px'>All Accounts</a>"
    for a in accounts:
        acc_btns += f"<a href='/courier?acc={a['name']}' class='btn {'bp' if acc_filter==a['name'] else ''}' style='font-size:11px;padding:5px 12px;margin-right:4px;margin-bottom:4px;border:1px solid #E2E8F0'>{a['name']}</a>"

    # Account summary cards
    acc_cards = ""
    for s in acc_summary:
        acc_info = next((a for a in accounts if a['name']==s['account_name']), None)
        bank_info = f"{acc_info['bank_holder']} — {acc_info['bank_name']}" if acc_info else ""
        acc_cards += f"""<div class="met" style="cursor:pointer" onclick="window.location='/courier?acc={s['account_name']}'">
            <div class="ml">{s['account_name']}</div>
            <div class="mv g">{pk(s['net'])}</div>
            <div style="font-size:10px;color:#6B7280;margin-top:2px">{bank_info}</div>
            <div style="font-size:10px;color:#9CA3AF">{s['cnt']} records</div>
        </div>"""

    acc_opts = "".join([f"<option value='{a['name']}'>{a['name']} ({a['courier']} → {a['bank_holder']} {a['bank_name']})</option>" for a in accounts])

    trs = "".join([f"""<tr>
        <td>{r['date']}</td>
        <td><span class='badge bg-b'>{r['account_name']}</span></td>
        <td><span class='badge bg-w'>{r['courier_name']}</span></td>
        <td>{r['type']}</td><td>{int(r['parcels'] or 0)}</td>
        <td class='g'><b>{pk(r['total_cod'])}</b></td>
        <td class='r'>{pk(r['charges'])}</td>
        <td><b>{pk(r['net_amount'])}</b></td>
        <td>{r['reference'] or '—'}</td>
        <td style='color:#9CA3AF;font-size:10px'>{r['added_by']}</td>
        {'<td><a href="/courier/del/'+str(r["id"])+'" class="btn bd" onclick="return confirm(\'Delete?\')">Del</a></td>' if session.get('role')=='admin' else ''}
        </tr>""" for r in rows]) or "<tr><td colspan='11' style='text-align:center;color:#9CA3AF;padding:14px'>No records</td></tr>"

    body = f"""{flashes()}

    {'' if not is_admin() else ''}<!-- ACCOUNT SUMMARY CARDS -->
    <div style="margin-bottom:6px;font-size:11px;font-weight:600;color:#6B7280">Account-wise Summary (click to filter)</div>
    <div class="grid" style="margin-bottom:14px">{acc_cards}</div>

    <div class="card"><div class="ct">Add Courier Payment</div>
    <form method="POST" action="/courier">
    <div class="fgrid">
      <div class="fg"><label>Account</label>
        <select name="account_name" id="acc_sel" onchange="setBank(this)">
          {acc_opts}
          <option value="Other">Other</option>
        </select>
      </div>
      <div class="fg"><label>Bank / Recipient</label>
        <input id="bank_info" readonly style="background:#F8FAFC;color:#6B7280" placeholder="Auto-filled from account">
      </div>
      <div class="fg"><label>Payment Type</label><select name="type"><option>COD</option><option>Online/Prepaid</option><option>Settlement</option></select></div>
      <div class="fg"><label>Total COD Amount (PKR)</label><input name="total_cod" type="number" step="0.01" placeholder="0" id="cod" oninput="calc()"></div>
      <div class="fg"><label>Courier Charges (PKR)</label><input name="charges" type="number" step="0.01" placeholder="0" id="chg" oninput="calc()"></div>
      <div class="fg"><label>No. of Parcels</label><input name="parcels" type="number" placeholder="0"></div>
      <div class="fg"><label>Date</label><input name="date" type="date" id="dt"></div>
      <div class="fg"><label>Reference / Sheet No.</label><input name="reference" placeholder="Settlement sheet no."></div>
    </div>
    <div class="calc-info"><span>Total COD: <b id="cs">Rs 0</b></span><span>Charges: <b id="xs" style="color:#DC2626">Rs 0</b></span><span>Net: <b id="ns" style="color:#16A34A">Rs 0</b></span></div>
    <button class="btn bp" type="submit">✓ Save Payment</button>
    </form>
    {f'''<hr style="margin:12px 0;border:none;border-top:1px solid #E2E8F0">
    <div style="font-size:11px;color:#6B7280;margin-bottom:6px">Add New Courier Account:</div>
    <form method="POST" action="/courier/account/add">
    <div class="fgrid">
      <div class="fg"><label>Account Name</label><input name="name" placeholder="e.g. NewStore" required></div>
      <div class="fg"><label>Courier</label><select name="courier"><option>DigiDokaan</option><option>Daewoo</option><option>TCS</option><option>Leopards</option><option>Other</option></select></div>
      <div class="fg"><label>Bank Name</label><input name="bank_name" placeholder="e.g. HBL, Faysal Bank"></div>
      <div class="fg"><label>Account Holder</label><input name="bank_holder" placeholder="e.g. Mudassar"></div>
    </div>
    <button class="btn bs" type="submit">+ Add Account</button>
    </form>''' if session.get('role')=='admin' else ''}
    </div>

{f'''<div class="grid" style="margin-bottom:14px">
      <div class="met"><div class="ml">{"Account: "+acc_filter if acc_filter else "All Accounts"}</div><div class="mv" style="font-size:13px;color:#6B7280">Filter Active</div></div>
      <div class="met"><div class="ml">Total COD</div><div class="mv g">{pk(t_cod)}</div></div>
      <div class="met"><div class="ml">Total Charges</div><div class="mv r">{pk(t_chg)}</div></div>
      <div class="met"><div class="ml">Net Amount</div><div class="mv b">{pk(float(t_cod)-float(t_chg))}</div></div>
    </div>''' if is_admin() else ''}

    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:8px">
        <div class="ct" style="margin:0">Courier Records</div>
        {f'<a href="/export/courier" class="btn bs" style="font-size:11px;padding:5px 12px">⬇ Export</a>' if is_admin() else ''}
      </div>
      <div style="margin-bottom:10px;display:flex;flex-wrap:wrap">{acc_btns}</div>
      <div class="tw"><table>
        <thead><tr><th>Date</th><th>Account</th><th>Courier</th><th>Type</th><th>Parcels</th><th>Total COD</th><th>Charges</th><th>Net</th><th>Reference</th><th>Added By</th>{'<th></th>' if session.get('role')=='admin' else ''}</tr></thead>
        <tbody>{trs}</tbody></table></div></div>

    <script>
    document.getElementById('dt').valueAsDate=new Date();
    var bankInfo = {{{",".join([f"'{a['name']}':'{a['bank_holder']} — {a['bank_name']} ({a['courier']})'" for a in accounts])}}};
    function setBank(sel){{
      var info = bankInfo[sel.value] || '';
      document.getElementById('bank_info').value = info;
    }}
    setBank(document.getElementById('acc_sel'));
    function calc(){{var c=parseFloat(document.getElementById('cod').value)||0;var x=parseFloat(document.getElementById('chg').value)||0;
    document.getElementById('cs').textContent='Rs '+Math.round(c).toLocaleString();
    document.getElementById('xs').textContent='Rs '+Math.round(x).toLocaleString();
    document.getElementById('ns').textContent='Rs '+Math.round(c-x).toLocaleString();}}</script>"""
    return layout("Courier Payments","co",body)

@app.route("/courier/account/add", methods=["POST"])
@login_req
@admin_req
def add_courier_account():
    f = request.form
    conn = get_db()
    try:
        qry(conn,"INSERT INTO courier_accounts (name,courier,bank_name,bank_holder) VALUES (%s,%s,%s,%s)",
            (f.get("name",""), f.get("courier","DigiDokaan"), f.get("bank_name",""), f.get("bank_holder","")))
        conn.commit()
        session.setdefault('_flashes',[]).append(("success",f"Account '{f.get('name')}' added!"))
    except:
        conn.rollback()
        session.setdefault('_flashes',[]).append(("danger","Account already exists!"))
    conn.close()
    return redirect("/courier")

@app.route("/courier/del/<int:i>")
@login_req
@admin_req
def del_courier(i):
    conn = get_db()
    qry(conn,"DELETE FROM courier WHERE id=%s",(i,))
    conn.commit(); conn.close()
    session.setdefault('_flashes',[]).append(("info","Deleted"))
    return redirect("/courier")

# ── INVESTMENT ────────────────────────────────────────────────────────────────
@app.route("/investment", methods=["GET","POST"])
@login_req
@admin_req
def investment():
    conn = get_db()
    if request.method == "POST":
        f = request.form
        qry(conn,"INSERT INTO investment (date,description,amount,added_by) VALUES (%s,%s,%s,%s)",
            (f.get("date") or today(), f.get("description",""), float(f.get("amount") or 0), session.get("naam","")))
        conn.commit(); conn.close()
        session.setdefault('_flashes',[]).append(("success","Investment saved!"))
        return redirect("/investment")
    rows  = qry(conn,"SELECT * FROM investment ORDER BY created_at DESC").fetchall()
    total = qry(conn,"SELECT COALESCE(SUM(amount),0) as v FROM investment").fetchone()["v"] or 0
    conn.close()
    trs = "".join([f"<tr><td>{r['date']}</td><td>{r['description']}</td><td class='g'><b>{pk(r['amount'])}</b></td><td style='color:#9CA3AF;font-size:10px'>{r['added_by']}</td><td><a href='/investment/del/{r['id']}' class='btn bd' onclick=\"return confirm('Delete?')\">Del</a></td></tr>" for r in rows]) or "<tr><td colspan='5' style='text-align:center;color:#9CA3AF;padding:14px'>No records</td></tr>"
    body = f"""{flashes()}
    <div class="card"><div class="ct">Add Investment</div>
    <form method="POST" action="/investment"><div class="fgrid">
      <div class="fg"><label>Amount (PKR)</label><input name="amount" type="number" step="0.01" placeholder="0" required></div>
      <div class="fg"><label>Description</label><input name="description" placeholder="e.g. Personal savings" required></div>
      <div class="fg"><label>Date</label><input name="date" type="date" id="dt"></div>
    </div><button class="btn bs" type="submit">✓ Save</button></form></div>
    <div class="card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div class="ct" style="margin:0">All Investments — Total: <span class="g">{pk(total)}</span></div>
      <a href="/export/investment" class="btn bs" style="font-size:11px;padding:5px 12px">⬇ Export</a>
    </div><div class="tw"><table><thead><tr><th>Date</th><th>Description</th><th>Amount</th><th>Added By</th><th></th></tr></thead>
    <tbody>{trs}</tbody></table></div></div>
    <script>document.getElementById('dt').valueAsDate=new Date();</script>"""
    return layout("Investment","inv",body)

@app.route("/investment/del/<int:i>")
@login_req
@admin_req
def del_investment(i):
    conn = get_db()
    qry(conn,"DELETE FROM investment WHERE id=%s",(i,))
    conn.commit(); conn.close()
    session.setdefault('_flashes',[]).append(("info","Deleted"))
    return redirect("/investment")

# ── LOANS ─────────────────────────────────────────────────────────────────────
@app.route("/loan", methods=["GET","POST"])
@login_req
@admin_req
def loan():
    conn = get_db()
    if request.method == "POST":
        f = request.form
        qry(conn,"INSERT INTO loans (date,person,type,amount,added_by) VALUES (%s,%s,%s,%s,%s)",
            (f.get("date") or today(), f.get("person",""), f.get("type","Loan Taken"),
             float(f.get("amount") or 0), session.get("naam","")))
        conn.commit(); conn.close()
        session.setdefault('_flashes',[]).append(("success","Loan record saved!"))
        return redirect("/loan")
    rows  = qry(conn,"SELECT * FROM loans ORDER BY created_at DESC").fetchall()
    taken = qry(conn,"SELECT COALESCE(SUM(amount),0) as v FROM loans WHERE type='Loan Taken'").fetchone()["v"] or 0
    repaid= qry(conn,"SELECT COALESCE(SUM(amount),0) as v FROM loans WHERE type='Loan Repaid'").fetchone()["v"] or 0
    conn.close()
    trs = "".join([f"<tr><td>{r['date']}</td><td>{r['person']}</td><td><span class='badge {'bg-r' if r['type']=='Loan Taken' else 'bg-g'}'>{r['type']}</span></td><td style='font-weight:600;color:{'#DC2626' if r['type']=='Loan Taken' else '#16A34A'}'>{pk(r['amount'])}</td><td style='color:#9CA3AF;font-size:10px'>{r['added_by']}</td><td><a href='/loan/del/{r['id']}' class='btn bd' onclick=\"return confirm('Delete?')\">Del</a></td></tr>" for r in rows]) or "<tr><td colspan='6' style='text-align:center;color:#9CA3AF;padding:14px'>No records</td></tr>"
    body = f"""{flashes()}
    <div class="card"><div class="ct">Add Loan Record</div>
    <form method="POST" action="/loan"><div class="fgrid">
      <div class="fg"><label>Person Name</label><input name="person" placeholder="e.g. Brother, Hamza" required></div>
      <div class="fg"><label>Type</label><select name="type"><option>Loan Taken</option><option>Loan Repaid</option></select></div>
      <div class="fg"><label>Amount (PKR)</label><input name="amount" type="number" step="0.01" placeholder="0" required></div>
      <div class="fg"><label>Date</label><input name="date" type="date" id="dt"></div>
    </div><button class="btn bp" type="submit">✓ Save</button></form></div>
    <div class="grid" style="margin-bottom:14px">
      <div class="met"><div class="ml">Loan Taken</div><div class="mv r">{pk(taken)}</div></div>
      <div class="met"><div class="ml">Loan Repaid</div><div class="mv g">{pk(repaid)}</div></div>
      <div class="met"><div class="ml">Outstanding</div><div class="mv w">{pk(float(taken)-float(repaid))}</div></div>
    </div>
    <div class="card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div class="ct" style="margin:0">All Loan Records</div>
      <a href="/export/loans" class="btn bs" style="font-size:11px;padding:5px 12px">⬇ Export</a>
    </div><div class="tw"><table><thead><tr><th>Date</th><th>Person</th><th>Type</th><th>Amount</th><th>Added By</th><th></th></tr></thead>
    <tbody>{trs}</tbody></table></div></div>
    <script>document.getElementById('dt').valueAsDate=new Date();</script>"""
    return layout("Loans","ln",body)

@app.route("/loan/del/<int:i>")
@login_req
@admin_req
def del_loan(i):
    conn = get_db()
    qry(conn,"DELETE FROM loans WHERE id=%s",(i,))
    conn.commit(); conn.close()
    session.setdefault('_flashes',[]).append(("info","Deleted"))
    return redirect("/loan")

# ── CASH & BANK ───────────────────────────────────────────────────────────────
@app.route("/cashbank", methods=["GET","POST"])
@login_req
@admin_req
def cashbank():
    conn = get_db()
    if request.method == "POST":
        f = request.form
        amount = float(f.get("amount") or 0)
        if not amount:
            session.setdefault('_flashes',[]).append(("danger","Amount required"))
            return redirect("/cashbank")
        qry(conn,"INSERT INTO cashbank (date,account,type,description,amount,added_by) VALUES (%s,%s,%s,%s,%s,%s)",
            (f.get("date") or today(), f.get("account","Cash in Hand"),
             f.get("type","Money In"), f.get("description",""), amount, session.get("naam","")))
        conn.commit(); conn.close()
        session.setdefault('_flashes',[]).append(("success","Entry saved!"))
        return redirect("/cashbank")

    acc_filter = request.args.get("acc","")
    if acc_filter:
        rows = qry(conn,"SELECT * FROM cashbank WHERE account=%s ORDER BY date ASC, created_at ASC",(acc_filter,)).fetchall()
    else:
        rows = qry(conn,"SELECT * FROM cashbank ORDER BY date ASC, created_at ASC").fetchall()

    balances = {}
    for acc in ACCOUNTS:
        in_  = qry(conn,"SELECT COALESCE(SUM(amount),0) as v FROM cashbank WHERE account=%s AND type IN ('Money In','Opening Balance')",(acc,)).fetchone()["v"] or 0
        out_ = qry(conn,"SELECT COALESCE(SUM(amount),0) as v FROM cashbank WHERE account=%s AND type='Money Out'",(acc,)).fetchone()["v"] or 0
        balances[acc] = float(in_) - float(out_)
    total_bal = sum(balances.values())
    conn.close()

    acc_btns = f"<a href='/cashbank' class='btn {'bp' if not acc_filter else ''}' style='font-size:11px;padding:5px 12px;margin-right:4px;margin-bottom:4px'>All</a>"
    for acc in ACCOUNTS:
        bal = balances[acc]
        col = "#16A34A" if bal >= 0 else "#DC2626"
        acc_btns += f"<a href='/cashbank?acc={acc}' class='btn {'bp' if acc_filter==acc else ''}' style='font-size:11px;padding:5px 12px;margin-right:4px;margin-bottom:4px;border:1px solid #E2E8F0'>{acc}<br><small style='color:{col}'>{pk(bal)}</small></a>"

    running = {}
    trs = ""
    if not rows:
        trs = "<tr><td colspan='8' style='text-align:center;color:#9CA3AF;padding:16px'>No entries — add Opening Balance first</td></tr>"
    else:
        for r in rows:
            acc = r['account']
            if acc not in running: running[acc] = 0
            if r['type'] in ('Money In','Opening Balance'):
                running[acc] += float(r['amount'] or 0); sign,col = "+","g"
            else:
                running[acc] -= float(r['amount'] or 0); sign,col = "-","r"
            bal = running[acc]
            bal_col = "#16A34A" if bal >= 0 else "#DC2626"
            badge = "bg-g" if r['type'] in ('Money In','Opening Balance') else "bg-r"
            del_btn = f"<a href='/cashbank/del/{r['id']}' class='btn bd' onclick=\"return confirm('Delete?')\">Del</a>" if session.get('role')=='admin' else ""
            trs += f"<tr><td>{r['date']}</td><td><span class='badge bg-b'>{r['account']}</span></td><td><span class='badge {badge}'>{r['type']}</span></td><td>{r['description'] or '—'}</td><td class='{col}'><b>{sign} {pk(r['amount'])}</b></td><td style='font-weight:700;color:{bal_col}'>{pk(bal)}</td><td style='color:#9CA3AF;font-size:10px'>{r['added_by']}</td><td>{del_btn}</td></tr>"

    acc_opts = "".join([f"<option>{a}</option>" for a in ACCOUNTS])
    body = f"""{flashes()}
    <div class="grid">
      <div class="met"><div class="ml">Total Balance</div><div class="mv {'g' if total_bal>=0 else 'r'}">{pk(total_bal)}</div></div>
      {"".join([f'<div class="met"><div class="ml">{acc}</div><div class="mv {"g" if balances[acc]>=0 else "r"}">{pk(balances[acc])}</div></div>' for acc in ACCOUNTS])}
    </div>
    <div class="card"><div class="ct">Add Entry</div>
    <form method="POST" action="/cashbank"><div class="fgrid">
      <div class="fg"><label>Account</label><select name="account">{acc_opts}</select></div>
      <div class="fg"><label>Type</label><select name="type"><option>Opening Balance</option><option>Money In</option><option>Money Out</option></select></div>
      <div class="fg"><label>Amount (PKR)</label><input name="amount" type="number" step="0.01" placeholder="0" required></div>
      <div class="fg"><label>Description</label><input name="description" placeholder="e.g. Received from courier"></div>
      <div class="fg"><label>Date</label><input name="date" type="date" id="dt"></div>
    </div><button class="btn bp" type="submit">✓ Save Entry</button></form></div>
    <div class="card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:8px">
      <div class="ct" style="margin:0">Cash & Bank Ledger</div>
      <a href="/export/cashbank" class="btn bs" style="font-size:11px;padding:5px 12px">⬇ Export</a>
    </div>
    <div style="margin-bottom:10px;display:flex;flex-wrap:wrap">{acc_btns}</div>
    <div class="tw"><table><thead><tr><th>Date</th><th>Account</th><th>Type</th><th>Description</th><th>Amount</th><th>Balance</th><th>Added By</th><th></th></tr></thead>
    <tbody>{trs}</tbody></table></div></div>
    <div style="background:#EFF6FF;border-radius:8px;padding:10px;font-size:11px;color:#1E40AF;margin-top:8px">
      Opening Balance = starting balance | Money In = received | Money Out = paid
    </div>
    <script>document.getElementById('dt').valueAsDate=new Date();</script>"""
    return layout("Cash & Bank","cb",body)

@app.route("/cashbank/del/<int:i>")
@login_req
@admin_req
def del_cashbank(i):
    conn = get_db()
    qry(conn,"DELETE FROM cashbank WHERE id=%s",(i,))
    conn.commit(); conn.close()
    session.setdefault('_flashes',[]).append(("info","Deleted"))
    return redirect("/cashbank")

# ── P&L ───────────────────────────────────────────────────────────────────────
@app.route("/pnl")
@login_req
@admin_req
def pnl():
    conn = get_db()

    # Date filter
    date_from = request.args.get("from","")
    date_to   = request.args.get("to","")

    # Build WHERE clause
    if date_from and date_to:
        w_courier  = "WHERE date>=%s AND date<=%s"
        w_purchase = "WHERE date>=%s AND date<=%s AND status!='Unpaid'"
        w_expense  = "WHERE date>=%s AND date<=%s"
        w_adspend  = "WHERE date>=%s AND date<=%s"
        p2 = (date_from, date_to)
        period_label = f"{date_from} to {date_to}"
    elif date_from:
        w_courier  = "WHERE date>=%s"
        w_purchase = "WHERE date>=%s AND status!='Unpaid'"
        w_expense  = "WHERE date>=%s"
        w_adspend  = "WHERE date>=%s"
        p2 = (date_from,)
        period_label = f"From {date_from}"
    elif date_to:
        w_courier  = "WHERE date<=%s"
        w_purchase = "WHERE date<=%s AND status!='Unpaid'"
        w_expense  = "WHERE date<=%s"
        w_adspend  = "WHERE date<=%s"
        p2 = (date_to,)
        period_label = f"Until {date_to}"
    else:
        w_courier  = ""
        w_purchase = "WHERE status!='Unpaid'"
        w_expense  = ""
        w_adspend  = ""
        p2 = ()
        period_label = "All Time"

    tr  = float(qry(conn,f"SELECT COALESCE(SUM(total_cod),0) as v FROM courier {w_courier}",p2).fetchone()["v"] or 0)
    tc  = float(qry(conn,f"SELECT COALESCE(SUM(charges),0) as v FROM courier {w_courier}",p2).fetchone()["v"] or 0)
    tp  = float(qry(conn,f"SELECT COALESCE(SUM(total_amount),0) as v FROM purchases {w_purchase}",p2).fetchone()["v"] or 0)
    te  = float(qry(conn,f"SELECT COALESCE(SUM(amount),0) as v FROM expenses {w_expense}",p2).fetchone()["v"] or 0)
    tad = float(qry(conn,f"SELECT COALESCE(SUM(total_pkr),0) as v FROM ad_spend {w_adspend}",p2).fetchone()["v"] or 0)
    tad_tax = float(qry(conn,f"SELECT COALESCE(SUM(tax_amount),0) as v FROM ad_spend {w_adspend}",p2).fetchone()["v"] or 0)
    ti  = float(qry(conn,"SELECT COALESCE(SUM(amount),0) as v FROM investment").fetchone()["v"] or 0)
    ll  = float(qry(conn,"SELECT COALESCE(SUM(amount),0) as v FROM loans WHERE type='Loan Taken'").fetchone()["v"] or 0)
    lw  = float(qry(conn,"SELECT COALESCE(SUM(amount),0) as v FROM loans WHERE type='Loan Repaid'").fetchone()["v"] or 0)
    cats    = qry(conn,f"SELECT category, SUM(amount) t FROM expenses {w_expense} GROUP BY category ORDER BY t DESC",p2).fetchall()
    ad_plats= qry(conn,f"SELECT platform, SUM(total_pkr) t FROM ad_spend {w_adspend} GROUP BY platform ORDER BY t DESC",p2).fetchall()
    conn.close()

    nc=tr-tc; gp=tr-tp; np=gp-tc-te-tad

    cat_rows = "".join([f"<div class='pnl-r'><span style='padding-left:12px'>{r['category']}</span><span class='r'>({pk(r['t'])})</span></div>" for r in cats])
    ad_rows  = "".join([f"<div class='pnl-r'><span style='padding-left:12px'>{r['platform']}</span><span class='r'>({pk(r['t'])})</span></div>" for r in ad_plats])

    body = f"""{flashes()}
    <div class="card" style="max-width:620px">
      <!-- Date Filter -->
      <form method="GET" action="/pnl" style="display:flex;gap:8px;align-items:flex-end;flex-wrap:wrap;margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid #E2E8F0">
        <div class="fg" style="margin:0;flex:1;min-width:130px"><label>From Date</label><input name="from" type="date" value="{date_from}" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px"></div>
        <div class="fg" style="margin:0;flex:1;min-width:130px"><label>To Date</label><input name="to" type="date" value="{date_to}" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px"></div>
        <button class="btn bp" type="submit" style="padding:7px 16px">🔍 Filter</button>
        <a href="/pnl" class="btn" style="padding:7px 16px;background:#F1F5F9;color:#6B7280">Reset</a>
        <a href="/export/pnl?from={date_from}&to={date_to}" class="btn bs" style="padding:7px 16px">⬇ Export P&L</a>
      </form>
      <div class="ct" style="font-size:14px">Profit & Loss — <span style="color:#3B82F6;font-size:12px">{period_label}</span></div>
      <div class="pnl-s">INCOME — Courier Payments</div>
      <div class="pnl-r"><span>Total COD Received</span><span class="g"><b>{pk(tr)}</b></span></div>
      <div class="pnl-r"><span style="padding-left:12px;color:#6B7280">Courier Charges</span><span class="r">({pk(tc)})</span></div>
      <div class="pnl-r pnl-t"><span>Net Income</span><span class="{'g' if nc>=0 else 'r'}">{pk(nc)}</span></div>
      <div class="pnl-s">COST OF GOODS (Purchases)</div>
      <div class="pnl-r"><span>Total Purchases (Paid)</span><span class="r">({pk(tp)})</span></div>
      <div class="pnl-r pnl-t"><span>Gross Profit</span><span class="{'g' if gp>=0 else 'r'}">{pk(gp)}</span></div>
      <div class="pnl-s">OPERATING EXPENSES</div>
      {cat_rows}
      <div class="pnl-r pnl-t"><span>Total Expenses</span><span class="r">({pk(te)})</span></div>
      <div class="pnl-s">AD SPEND (Marketing)</div>
      {ad_rows}
      <div class="pnl-r"><span style="padding-left:12px;color:#6B7280">Tax on Ads</span><span style="color:#D97706">({pk(tad_tax)})</span></div>
      <div class="pnl-r pnl-t"><span>Total Ad Spend</span><span class="r">({pk(tad)})</span></div>
      <div class="pnl-grand"><span>NET PROFIT / LOSS</span><span class="{'g' if np>=0 else 'r'}" style="font-size:16px">{pk(np)}</span></div>
      <div class="pnl-s">CAPITAL & LIABILITIES</div>
      <div class="pnl-r"><span>Total Investment</span><span class="b">{pk(ti)}</span></div>
      <div class="pnl-r"><span>Loans Taken</span><span class="r">{pk(ll)}</span></div>
      <div class="pnl-r"><span>Loans Repaid</span><span class="g">{pk(lw)}</span></div>
      <div class="pnl-r pnl-t"><span>Outstanding Loan</span><span class="w">{pk(ll-lw)}</span></div>
    </div>"""
    return layout("P&L Report","pnl",body)

# ── USERS ─────────────────────────────────────────────────────────────────────
@app.route("/users", methods=["GET","POST"])
@login_req
@admin_req
def users():
    conn = get_db()
    if request.method == "POST":
        f = request.form
        try:
            qry(conn,"INSERT INTO users (username,password,role,naam) VALUES (%s,%s,%s,%s)",
                (f.get("username",""), generate_password_hash(f.get("password","")),
                 f.get("role","employee"), f.get("naam","")))
            conn.commit()
            session.setdefault('_flashes',[]).append(("success",f"User added!"))
        except:
            conn.rollback()
            session.setdefault('_flashes',[]).append(("danger","Username already exists!"))
        conn.close()
        return redirect("/users")
    rows = qry(conn,"SELECT id,username,naam,role FROM users ORDER BY id").fetchall()
    conn.close()
    trs_list = []
    for r in rows:
        badge = "bg-b" if r['role']=='admin' else "bg-g"
        if r['id'] != session.get('uid'):
            del_btn = '<a href="/users/del/'+str(r["id"])+'" class="btn bd" onclick="return confirm(chr(39)+chr(68)+chr(101)+chr(108)+chr(101)+chr(116)+chr(101)+chr(63)+chr(39))">Del</a>'
        else:
            del_btn = '<span style="font-size:10px;color:#9CA3AF">You</span>'
        trs_list.append(f"<tr><td>{r['id']}</td><td>{r['naam'] or chr(8212)}</td><td>{r['username']}</td><td><span class='badge {badge}'>{r['role']}</span></td><td>{del_btn}</td></tr>")
    trs = "".join(trs_list)
    body = f"""{flashes()}
    <div class="card"><div class="ct">Add New User</div>
    <form method="POST" action="/users"><div class="fgrid">
      <div class="fg"><label>Full Name</label><input name="naam" placeholder="Employee name" required></div>
      <div class="fg"><label>Username</label><input name="username" placeholder="login username" required></div>
      <div class="fg"><label>Password</label><input name="password" type="password" placeholder="password" required></div>
      <div class="fg"><label>Role</label><select name="role"><option value="employee">Employee</option><option value="admin">Admin</option></select></div>
    </div><button class="btn bp" type="submit">✓ Add User</button></form>
    <div style="margin-top:10px;padding:10px;background:#FEF3C7;border-radius:7px;font-size:11px;color:#92400E">
      <b>Employee:</b> Can add/view Purchases, Expenses, Courier.<br><b>Admin:</b> Full access including delete, reports, users.
    </div></div>
    <div class="card"><div class="ct">All Users</div>
    <div class="tw"><table><thead><tr><th>ID</th><th>Name</th><th>Username</th><th>Role</th><th></th></tr></thead>
    <tbody>{trs}</tbody></table></div></div>"""
    return layout("Users","usr",body)

@app.route("/users/del/<int:i>")
@login_req
@admin_req
def del_user(i):
    if i == session.get("uid"):
        session.setdefault('_flashes',[]).append(("danger","Cannot delete yourself"))
        return redirect("/users")
    conn = get_db()
    qry(conn,"DELETE FROM users WHERE id=%s",(i,))
    conn.commit(); conn.close()
    session.setdefault('_flashes',[]).append(("info","User deleted"))
    return redirect("/users")

# ── COURIER TRACKING ──────────────────────────────────────────────────────────
@app.route("/tracking", methods=["GET","POST"])
@login_req
def tracking():
    result = error = None
    track_no = courier_type = ""
    try:
        import requests as req_lib
        REQUESTS_OK = True
    except:
        REQUESTS_OK = False

    if request.method == "POST" and REQUESTS_OK:
        track_no     = request.form.get("track_no","").strip()
        courier_type = request.form.get("courier_type","daewoo")
        if track_no:
            if courier_type == "daewoo":
                key  = os.environ.get("DAEWOO_API_KEY","")
                user = os.environ.get("DAEWOO_API_USER","")
                pwd  = os.environ.get("DAEWOO_API_PASS","")
                if key:
                    try:
                        r = req_lib.get(f"https://codapi.daewoo.net.pk/api/booking/quickTrack?trackingNo={track_no}", timeout=10)
                        d = r.json()
                        if d.get("Result",{}).get("Success"): result = d["Result"]
                        else: error = "Tracking number not found"
                    except Exception as e: error = str(e)
                else: error = "Daewoo API credentials not set in Railway Variables"
            else:
                phone = os.environ.get("DIGI_PHONE","")
                pwd   = os.environ.get("DIGI_PASS","")
                if phone:
                    try:
                        lr = req_lib.post("https://dev.digidokaan.pk/api/v1/digidokaan/auth/login", json={"phone":phone,"password":pwd}, timeout=10)
                        token = lr.json().get("token")
                        if token:
                            tr = req_lib.post("https://dev.digidokaan.pk/api/v1/digidokaan/get-order-tracking",
                                            json={"tracking_no":track_no}, headers={"Authorization":f"Bearer {token}"}, timeout=10)
                            d = tr.json()
                            if d.get("code") == 200: result = d
                            else: error = d.get("error","Not found")
                        else: error = "DigiDokaan login failed"
                    except Exception as e: error = str(e)
                else: error = "DigiDokaan credentials not set in Railway Variables"

    result_html = ""
    if error: result_html = f"<div class='alert al-d'>⚠️ {error}</div>"
    elif result and courier_type == "daewoo":
        cur = result.get("CurrentTrackStatus",[])
        det = result.get("TrackingDetails",[])
        if cur:
            c = cur[0]
            sc = "#16A34A" if "DELIVER" in str(c.get("status_name","")).upper() else "#D97706"
            det_rows = "".join([f"<tr><td>{d.get('Date','')}</td><td><span class='badge bg-w'>{d.get('Status','')}</span></td><td>{d.get('TransactionTerminal','')}</td><td>{d.get('Rem','')}</td></tr>" for d in det])
            result_html = f"""<div class="card" style="border-left:4px solid {sc}">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                <div class="ct" style="margin:0">Daewoo — {track_no}</div>
                <span style="background:{sc};color:#fff;padding:4px 12px;border-radius:99px;font-size:12px;font-weight:600">{c.get('status_name','—')}</span>
              </div>
              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:12px">
                <div class="met"><div class="ml">Customer</div><div style="font-size:13px;font-weight:600">{c.get('receiver_name','—')}</div></div>
                <div class="met"><div class="ml">Contact</div><div style="font-size:12px">{c.get('receiver_contact1','—')}</div></div>
                <div class="met"><div class="ml">COD Amount</div><div style="font-size:13px;font-weight:600;color:#16A34A">Rs {c.get('amount_cod',0):,}</div></div>
                <div class="met"><div class="ml">From</div><div style="font-size:12px">{c.get('source_terminal','—')}</div></div>
                <div class="met"><div class="ml">To</div><div style="font-size:12px">{c.get('destination_terminal','—')}</div></div>
                <div class="met"><div class="ml">Booked</div><div style="font-size:11px">{str(c.get('booking_date_time','—'))[:10]}</div></div>
              </div>
              <div class="ct">Tracking History</div>
              <div class="tw"><table><thead><tr><th>Date</th><th>Status</th><th>Terminal</th><th>Remarks</th></tr></thead>
              <tbody>{det_rows}</tbody></table></div></div>"""

    conn = get_db()
    all_co = qry(conn,"SELECT * FROM courier ORDER BY created_at DESC LIMIT 15").fetchall()
    tot_cod = float(qry(conn,"SELECT COALESCE(SUM(total_cod),0) as v FROM courier").fetchone()["v"] or 0)
    tot_net = float(qry(conn,"SELECT COALESCE(SUM(net_amount),0) as v FROM courier").fetchone()["v"] or 0)
    tot_cnt = qry(conn,"SELECT COUNT(*) as v FROM courier").fetchone()["v"] or 0
    conn.close()

    dw_ok = bool(os.environ.get("DAEWOO_API_KEY"))
    di_ok = bool(os.environ.get("DIGI_PHONE"))
    rec_rows = "".join([f"<tr><td>{r['date']}</td><td><span class='badge bg-b'>{r['courier_name']}</span></td><td>{r['type']}</td><td>{int(r['parcels'] or 0)}</td><td class='g'><b>{pk(r['total_cod'])}</b></td><td class='r'>{pk(r['charges'])}</td><td><b>{pk(r['net_amount'])}</b></td><td>{r['reference'] or '—'}</td></tr>" for r in all_co])

    body = f"""{flashes()}
    <div style="display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap">
      <div style="padding:6px 12px;border-radius:7px;font-size:11px;font-weight:600;background:{'#DCFCE7' if dw_ok else '#FEE2E2'};color:{'#166534' if dw_ok else '#991B1B'}">{'✓' if dw_ok else '✗'} Daewoo API</div>
      <div style="padding:6px 12px;border-radius:7px;font-size:11px;font-weight:600;background:{'#DCFCE7' if di_ok else '#FEE2E2'};color:{'#166534' if di_ok else '#991B1B'}">{'✓' if di_ok else '✗'} DigiDokaan API</div>
    </div>
    <div class="card" style="background:linear-gradient(135deg,#0F172A,#1E3A8A);border:none">
      <div style="color:#fff;font-size:15px;font-weight:700;margin-bottom:4px">📡 Courier Tracking</div>
      <div style="color:#93C5FD;font-size:12px;margin-bottom:14px">Enter tracking number for real-time status</div>
      <form method="POST" action="/tracking" style="display:flex;gap:8px;flex-wrap:wrap">
        <input name="track_no" value="{track_no}" placeholder="Enter tracking number..."
               style="flex:1;min-width:200px;padding:10px 14px;border:none;border-radius:8px;font-size:13px;background:#fff">
        <select name="courier_type" style="padding:10px 14px;border:none;border-radius:8px;font-size:13px;background:#fff">
          <option value="daewoo" {'selected' if courier_type=='daewoo' else ''}>🚛 Daewoo Express</option>
          <option value="digi" {'selected' if courier_type=='digi' else ''}>📦 DigiDokaan</option>
        </select>
        <button class="btn bp" type="submit" style="padding:10px 20px">🔍 Track</button>
      </form>
    </div>
    {result_html}
    <div class="grid" style="margin-bottom:14px">
      <div class="met"><div class="ml">Total Records</div><div class="mv b">{tot_cnt}</div></div>
      {f'<div class="met"><div class="ml">Total COD</div><div class="mv g">{pk(tot_cod)}</div></div><div class="met"><div class="ml">Net Income</div><div class="mv g">{pk(tot_net)}</div></div>' if is_admin() else ''}
    </div>
    <div class="card"><div class="ct">Courier Records</div>
    <div class="tw"><table><thead><tr><th>Date</th><th>Courier</th><th>Type</th><th>Parcels</th><th>Total COD</th><th>Charges</th><th>Net</th><th>Reference</th></tr></thead>
    <tbody>{rec_rows or '<tr><td colspan="8" style="text-align:center;color:#9CA3AF;padding:14px">No records</td></tr>'}</tbody></table></div></div>"""
    return layout("Courier Tracking","trk",body)

# ── IMPORT ────────────────────────────────────────────────────────────────────
@app.route("/import", methods=["GET","POST"])
@login_req
@admin_req
def import_data():
    if request.method == "POST":
        f    = request.files.get("file")
        dtype= request.form.get("type","purchases")
        if not f:
            session.setdefault('_flashes',[]).append(("danger","Please select a file"))
            return redirect("/import")
        try:
            content = f.read().decode("utf-8-sig")
            reader  = csv.DictReader(io.StringIO(content))
            rows    = list(reader)
            conn    = get_db()
            count   = 0
            for r in rows:
                try:
                    if dtype == "purchases":
                        qty   = float(r.get("quantity") or r.get("Qty") or 1)
                        total = float(r.get("total_amount") or r.get("Total Amount") or r.get("Kul Rakam") or 0)
                        per_u = round(total/qty,2) if qty else 0
                        st    = str(r.get("status") or r.get("Status","Paid")).replace("Paid (Ada)","Paid").replace("Unpaid (Baqi)","Unpaid").replace("Partial (Adha)","Partial")
                        qry(conn,"INSERT INTO purchases (date,vendor,product,quantity,unit,total_amount,per_unit_price,status,notes,added_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            (r.get("date") or r.get("Tarikh") or today(),
                             r.get("vendor") or r.get("Vendor",""),
                             r.get("product") or r.get("Product") or r.get("Maal",""),
                             qty, r.get("unit") or r.get("Unit","Piece"),
                             total, per_u, st,
                             r.get("notes") or r.get("Notes",""),
                             r.get("added_by") or session.get("naam","")))
                        count += 1
                    elif dtype == "expenses":
                        qry(conn,"INSERT INTO expenses (date,category,description,paid_to,amount,payment_method,added_by) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                            (r.get("date") or r.get("Tarikh") or today(),
                             r.get("category") or r.get("Head",""),
                             r.get("description") or r.get("Tafseel",""),
                             r.get("paid_to") or r.get("Kise Diya",""),
                             float(r.get("amount") or r.get("Rakam") or 0),
                             r.get("payment_method") or r.get("Tariqa","Cash"),
                             r.get("added_by") or session.get("naam","")))
                        count += 1
                    elif dtype == "investment":
                        qry(conn,"INSERT INTO investment (date,description,amount,added_by) VALUES (%s,%s,%s,%s)",
                            (r.get("date") or r.get("Tarikh") or today(),
                             r.get("description") or r.get("Tafseel",""),
                             float(r.get("amount") or r.get("Rakam") or 0),
                             r.get("added_by") or session.get("naam","")))
                        count += 1
                    elif dtype == "loans":
                        tp = str(r.get("type") or r.get("Qism","Loan Taken")).replace("Loan Liya","Loan Taken").replace("Loan Wapas","Loan Repaid")
                        qry(conn,"INSERT INTO loans (date,person,type,amount,added_by) VALUES (%s,%s,%s,%s,%s)",
                            (r.get("date") or r.get("Tarikh") or today(),
                             r.get("person") or r.get("Shakhs",""),
                             tp, float(r.get("amount") or r.get("Rakam") or 0),
                             r.get("added_by") or session.get("naam","")))
                        count += 1
                    elif dtype == "courier":
                        cod = float(r.get("total_cod") or r.get("Mila") or 0)
                        chg = float(r.get("charges") or r.get("Charges") or 0)
                        qry(conn,"INSERT INTO courier (date,courier_name,type,parcels,total_cod,charges,net_amount,reference,added_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            (r.get("date") or r.get("Tarikh") or today(),
                             r.get("courier_name") or r.get("Courier",""),
                             r.get("type") or r.get("Qism","COD"),
                             float(r.get("parcels") or 0),
                             cod, chg, round(cod-chg,2),
                             r.get("reference") or r.get("Reference",""),
                             r.get("added_by") or session.get("naam","")))
                        count += 1
                except: continue
            conn.commit(); conn.close()
            session.setdefault('_flashes',[]).append(("success",f"✓ {count} records imported!"))
        except Exception as e:
            session.setdefault('_flashes',[]).append(("danger",f"Error: {str(e)}"))
        return redirect("/import")

    body = f"""{flashes()}
    <div class="card" style="max-width:600px">
      <div class="ct">Import Data from CSV</div>
      <div style="background:#FEF3C7;border-radius:8px;padding:12px;margin-bottom:14px;font-size:12px;color:#92400E">
        ⚠️ Use the converted CSV files. Importing twice will create duplicates.
      </div>
      <form method="POST" action="/import" enctype="multipart/form-data">
        <div class="fgrid">
          <div class="fg"><label>Data Type</label>
            <select name="type"><option value="purchases">Purchases</option><option value="expenses">Expenses</option><option value="investment">Investment</option><option value="loans">Loans</option><option value="courier">Courier</option></select>
          </div>
          <div class="fg"><label>CSV File</label><input type="file" name="file" accept=".csv" required></div>
        </div>
        <button class="btn bp" type="submit">⬆ Import Data</button>
      </form>
    </div>
    <div class="card" style="max-width:600px">
      <div class="ct">Import Order</div>
      <div style="font-size:12px;line-height:2.2">
        <div style="padding:5px 0;border-bottom:1px solid #F1F5F9"><b>1.</b> Select <b>Purchases</b> → Upload <b>purchases_import.csv</b></div>
        <div style="padding:5px 0;border-bottom:1px solid #F1F5F9"><b>2.</b> Select <b>Expenses</b> → Upload <b>expenses_import.csv</b></div>
        <div style="padding:5px 0;border-bottom:1px solid #F1F5F9"><b>3.</b> Select <b>Investment</b> → Upload <b>investment_import.csv</b></div>
        <div style="padding:5px 0;border-bottom:1px solid #F1F5F9"><b>4.</b> Select <b>Loans</b> → Upload <b>loans_import.csv</b></div>
        <div style="padding:5px 0"><b>5.</b> Select <b>Courier</b> → Upload original <b>courier.csv</b></div>
      </div>
    </div>"""
    return layout("Import Data","imp",body)

# ── AD SPEND ──────────────────────────────────────────────────────────────────
@app.route("/adspend", methods=["GET","POST"])
@login_req
@admin_req
def adspend():
    conn = get_db()
    ad_accounts = qry(conn,"SELECT * FROM ad_accounts WHERE active=TRUE ORDER BY platform,name").fetchall()

    if request.method == "POST":
        f = request.form
        acc_id   = int(f.get("ad_account_id") or 0)
        # Fresh DB se account lo - list pe depend mat karo
        acc_row  = qry(conn,"SELECT * FROM ad_accounts WHERE id=%s",(acc_id,)).fetchone()
        platform = acc_row['platform'] if acc_row else ""
        site     = f.get("site") or (acc_row['site'] if acc_row else "")
        currency = acc_row['currency'] if acc_row else "PKR"
        acc_name = acc_row['name'] if acc_row else ""

        if currency == "USD":
            if platform == "Facebook":
                # Facebook USD - tax % based
                fb_spend   = float(f.get("fb_usd_spend") or 0)
                fb_tax_pct = float(f.get("fb_tax_pct") or 0)
                fb_rate    = float(f.get("fb_usd_rate") or 0)
                tax_d      = fb_spend * fb_tax_pct / 100
                total_d    = fb_spend + tax_d
                dollar_amt = fb_spend
                dollar_rate= fb_rate
                pkr_amt    = round(fb_spend * fb_rate, 2)
                tax_amt    = round(tax_d * fb_rate, 2)
                total_pkr  = round(total_d * fb_rate, 2)
            else:
                # TikTok USD - billed dollars different
                dollar_amt  = float(f.get("usd_spend") or 0)
                dollar_rate = float(f.get("usd_rate") or 0)
                billed_d    = float(f.get("usd_billed") or dollar_amt)
                pkr_amt     = round(dollar_amt * dollar_rate, 2)
                tax_amt     = round((billed_d - dollar_amt) * dollar_rate, 2)
                total_pkr   = round(billed_d * dollar_rate, 2)
        else:
            pkr_type = f.get("pkr_type","dollar")
            if pkr_type == "dollar":
                pkr_paid    = float(f.get("pkr_paid") or 0)
                buy_rate    = float(f.get("dollar_buy_rate") or 0)
                spend_rate  = float(f.get("dollar_spend_rate") or 0)
                if buy_rate > 0 and spend_rate > 0:
                    d_bought    = pkr_paid / buy_rate
                    d_spent     = d_bought * (buy_rate / spend_rate)
                    d_extra     = d_spent - d_bought
                    tax_amt     = round(d_extra * buy_rate, 2)  # tax = extra × buy rate
                    total_pkr   = round(pkr_paid + tax_amt, 2)
                    dollar_amt  = round(d_bought, 2)
                    dollar_rate = buy_rate
                    pkr_amt     = pkr_paid
                else:
                    dollar_amt = dollar_rate = pkr_amt = tax_amt = total_pkr = 0
            else:
                # Direct PKR
                dollar_amt  = 0
                dollar_rate = 0
                pkr_amt     = float(f.get("pkr_amount_direct") or 0)
                tax_amt     = float(f.get("tax_amount_direct") or 0)
                total_pkr   = round(pkr_amt + tax_amt, 2)

        qry(conn,"""INSERT INTO ad_spend
            (date,ad_account_id,ad_account_name,platform,site,dollar_amount,dollar_rate,pkr_amount,tax_amount,total_pkr,description,added_by,period_from,period_to)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (f.get("date") or today(), acc_id, acc_name, platform, site,
             dollar_amt, dollar_rate, pkr_amt, tax_amt, total_pkr,
             f.get("description",""), session.get("naam",""),
             f.get("period_from",""), f.get("period_to","")))
        conn.commit()
        session.setdefault('_flashes',[]).append(("success","Ad spend saved!"))
        conn.close()
        return redirect("/adspend")

    # Filter
    acc_filter  = request.args.get("acc","")
    plat_filter = request.args.get("plat","")
    site_filter = request.args.get("site","")

    sql = "SELECT * FROM ad_spend WHERE 1=1"
    params = []
    if acc_filter:  sql += " AND ad_account_name=%s"; params.append(acc_filter)
    if plat_filter: sql += " AND platform=%s"; params.append(plat_filter)
    if site_filter: sql += " AND site=%s"; params.append(site_filter)
    sql += " ORDER BY created_at DESC"
    rows = qry(conn, sql, params).fetchall()

    # Totals
    total_pkr = sum(float(r['total_pkr'] or 0) for r in rows)
    total_tax = sum(float(r['tax_amount'] or 0) for r in rows)

    # Summary by account
    acc_summary = qry(conn,"""SELECT ad_account_name, platform,
        COUNT(*) cnt, SUM(total_pkr) total, SUM(tax_amount) tax
        FROM ad_spend GROUP BY ad_account_name, platform ORDER BY total DESC""").fetchall()

    # Summary by platform
    plat_summary = qry(conn,"""SELECT platform,
        COUNT(*) cnt, SUM(total_pkr) total, SUM(tax_amount) tax
        FROM ad_spend GROUP BY platform ORDER BY total DESC""").fetchall()

    # Summary by site
    site_summary = qry(conn,"""SELECT site,
        COUNT(*) cnt, SUM(total_pkr) total
        FROM ad_spend WHERE site!='' GROUP BY site ORDER BY total DESC""").fetchall()

    # Unique sites for filter
    all_sites = list(set([r['site'] for r in qry(conn,"SELECT DISTINCT site FROM ad_spend WHERE site!=''").fetchall()]))

    conn.close()

    # Platform colors
    plat_colors = {"Facebook":"#1877F2","TikTok":"#010101","Google":"#EA4335","Other":"#6B7280"}

    # Account options grouped by platform
    acc_opts = ""
    for plat in ["Facebook","TikTok","Google","Other"]:
        plat_accs = [a for a in ad_accounts if a['platform']==plat]
        if plat_accs:
            acc_opts += f"<optgroup label='{plat}'>"
            for a in plat_accs:
                curr = f" ({a['currency']})" if a['currency']=='USD' else ""
                site_info = f" → {a['site']}" if a['site'] else ""
                acc_opts += f"<option value='{a['id']}'>{a['name']}{curr}{site_info}</option>"
            acc_opts += "</optgroup>"

    # Account summary cards
    acc_cards = ""
    for s in acc_summary:
        col = plat_colors.get(s['platform'],"#6B7280")
        acc_cards += f"""<div class="met" style="border-top:3px solid {col}">
            <div class="ml">{s['ad_account_name']}</div>
            <div class="mv r">{pk(s['total'])}</div>
            <div style="font-size:10px;color:{col};margin-top:2px">{s['platform']}</div>
            <div style="font-size:10px;color:#9CA3AF">Tax: {pk(s['tax'])} | {s['cnt']} entries</div>
        </div>"""

    # Platform summary
    plat_cards = ""
    for s in plat_summary:
        col = plat_colors.get(s['platform'],"#6B7280")
        plat_cards += f"""<div class="met" style="border-top:3px solid {col}">
            <div class="ml">{s['platform']}</div>
            <div class="mv r">{pk(s['total'])}</div>
            <div style="font-size:10px;color:#9CA3AF">Tax: {pk(s['tax'])} | {s['cnt']} entries</div>
        </div>"""

    # Site summary
    site_cards = "".join([f"""<div style='display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #F1F5F9;font-size:12px'>
        <span>{s['site']}</span><span class='r'><b>{pk(s['total'])}</b></span>
        </div>""" for s in site_summary]) or "<div style='color:#9CA3AF;font-size:12px;padding:8px'>No data</div>"

    # Table rows
    trs = "".join([f"""<tr>
        <td>{r['date']}</td>
        <td><span style='background:{plat_colors.get(r["platform"],"#6B7280")};color:#fff;padding:2px 8px;border-radius:99px;font-size:10px;font-weight:600'>{r['platform']}</span></td>
        <td>{r['ad_account_name']}</td>
        <td>{r['site'] or '—'}</td>
        <td style='color:#6B7280;font-size:11px'>{'$'+str(r['dollar_amount']) if r['dollar_amount'] else '—'}</td>
        <td style='color:#6B7280;font-size:11px'>{str(r['dollar_rate'])+'x' if r['dollar_rate'] else '—'}</td>
        <td class='r'>{pk(r['pkr_amount'])}</td>
        <td style='color:#D97706'>{pk(r['tax_amount'])}</td>
        <td class='r'><b>{pk(r['total_pkr'])}</b></td>
        <td style='color:#6B7280;font-size:10px'>{(str(r['period_from'])[:10]+' → '+str(r['period_to'])[:10]) if r.get('period_from') else '—'}</td>
        <td style='color:#9CA3AF;font-size:10px'>{r['description'] or '—'}</td>
        <td style='color:#9CA3AF;font-size:10px'>{r['added_by']}</td>
        {'<td><a href="/adspend/del/'+str(r["id"])+'" class="btn bd" onclick="return confirm(\'Delete?\')">Del</a></td>' if session.get('role')=='admin' else ''}
        </tr>""" for r in rows]) or "<tr><td colspan='12' style='text-align:center;color:#9CA3AF;padding:14px'>No records</td></tr>"

    # Filter buttons
    plat_btns = f"<a href='/adspend' class='btn {'bp' if not plat_filter else ''}' style='font-size:11px;padding:4px 10px;margin-right:4px;margin-bottom:4px'>All</a>"
    for p in ["Facebook","TikTok","Google"]:
        col = plat_colors.get(p,"#6B7280")
        plat_btns += f"<a href='/adspend?plat={p}' class='btn' style='font-size:11px;padding:4px 10px;margin-right:4px;margin-bottom:4px;background:{''+col if plat_filter==p else '#fff'};color:{'#fff' if plat_filter==p else col};border:1px solid {col}'>{p}</a>"

    # Add account form (admin only)
    add_acc_form = ""
    if session.get("role") == "admin":
        add_acc_form = """<hr style="margin:14px 0;border:none;border-top:1px solid #E2E8F0">
        <div style="font-size:12px;font-weight:600;margin-bottom:8px">Add New Ad Account:</div>
        <form method="POST" action="/adspend/account/add">
        <div class="fgrid">
          <div class="fg"><label>Account Name</label><input name="name" placeholder="e.g. Facebook Account 5" required></div>
          <div class="fg"><label>Platform</label><select name="platform"><option>Facebook</option><option>TikTok</option><option>Google</option><option>Other</option></select></div>
          <div class="fg"><label>Currency</label><select name="currency"><option value="PKR">PKR</option><option value="USD">USD (Dollar)</option></select></div>
          <div class="fg"><label>Site / Product</label><input name="site" placeholder="e.g. Sehatkart, WomenComfort"></div>
        </div>
        <button class="btn bs" type="submit">+ Add Account</button>
        </form>"""

    body = f"""{flashes()}

    <!-- SUMMARIES -->
    <div class="g2" style="margin-bottom:14px">
      <div>
        <div style="font-size:11px;font-weight:600;color:#6B7280;margin-bottom:6px">BY PLATFORM</div>
        <div class="grid">{plat_cards or '<div style="color:#9CA3AF;font-size:12px">No data</div>'}</div>
      </div>
      <div class="card"><div class="ct">By Site/Product</div>{site_cards}</div>
    </div>

    <div style="font-size:11px;font-weight:600;color:#6B7280;margin-bottom:6px">BY AD ACCOUNT</div>
    <div class="grid" style="margin-bottom:14px">{acc_cards or '<div style="color:#9CA3AF;font-size:12px">No data</div>'}</div>

    <!-- ADD FORM -->
    <div class="card"><div class="ct">Add Ad Spend</div>
    <form method="POST" action="/adspend">
    <div class="fgrid">
      <div class="fg"><label>Ad Account</label>
        <select name="ad_account_id" id="acc_sel" onchange="onAccChange(this)">
          {acc_opts}
        </select>
      </div>
      <div class="fg"><label>Site / Product</label>
        <input name="site" id="site_inp" placeholder="Which site/product?">
      </div>
      <div class="fg"><label>Entry Date</label><input name="date" type="date" id="dt"></div>
      <div class="fg"><label>Ad Period — From</label><input name="period_from" type="date" id="pf"></div>
      <div class="fg"><label>Ad Period — To</label><input name="period_to" type="date" id="pt"></div>
      <div class="fg"><label>Description</label><input name="description" placeholder="Campaign details"></div>
    </div>

    <!-- PKR Account — Dollar Purchase -->
    <div id="pkr_usd_fields" style="display:none;background:#EFF6FF;border-radius:8px;padding:12px;margin-bottom:10px">
      <div style="font-size:11px;font-weight:600;color:#1E40AF;margin-bottom:8px">💳 PKR Account — Dollar Purchase</div>
      <div class="fgrid">
        <div class="fg"><label>PKR Amount (jo aapne diya dollar khareedne ke liye)</label>
          <input name="pkr_paid" type="number" step="0.01" placeholder="e.g. 601968" id="pk_pkr" oninput="calcPKR_USD()"></div>
        <div class="fg"><label>Dollar Buy Rate (1$=?PKR — jis rate pe kharida)</label>
          <input name="dollar_buy_rate" type="number" step="0.01" placeholder="e.g. 293.5" id="pk_buy" oninput="calcPKR_USD()"></div>
        <div class="fg"><label>Dollar Spend Rate (1$=?PKR — jis rate pe Facebook/TikTok ne charge kiya)</label>
          <input name="dollar_spend_rate" type="number" step="0.01" placeholder="e.g. 272.5" id="pk_spend" oninput="calcPKR_USD()"></div>
      </div>
      <div class="calc-info" id="pk_info" style="flex-direction:column;gap:4px">
        <div>Dollar Kharida: <b id="pk_d1">$0</b> | Dollar Kata: <b id="pk_d2">$0</b> | Extra Dollar (Tax): <b id="pk_d3" style="color:#D97706">$0</b></div>
        <div>Tax PKR: <b id="pk_tax_pkr" style="color:#D97706">Rs 0</b> | Total PKR: <b id="pk_tot" style="color:#DC2626">Rs 0</b></div>
      </div>
    </div>

    <!-- PKR Account — Direct PKR -->
    <div id="pkr_direct_fields" style="display:none;background:#F0FDF4;border-radius:8px;padding:12px;margin-bottom:10px">
      <div style="font-size:11px;font-weight:600;color:#166534;margin-bottom:8px">💚 PKR Account — Direct Payment</div>
      <div class="fgrid">
        <div class="fg"><label>Amount (PKR)</label><input name="pkr_amount_direct" type="number" step="0.01" placeholder="0" id="pd_amt" oninput="calcPKR_Direct()"></div>
        <div class="fg"><label>Tax (PKR)</label><input name="tax_amount_direct" type="number" step="0.01" placeholder="0" id="pd_tax" oninput="calcPKR_Direct()"></div>
        <div class="fg"><label>Total (auto)</label><input id="pd_tot" readonly style="background:#F8FAFC;color:#DC2626" placeholder="Auto calculated"></div>
      </div>
    </div>

    <!-- USD Account - TikTok (billed dollars different) -->
    <div id="usd_tiktok_fields" style="display:none;background:#FEF3C7;border-radius:8px;padding:12px;margin-bottom:10px">
      <div style="font-size:11px;font-weight:600;color:#92400E;margin-bottom:8px">💵 TikTok USD — Dollar Bill</div>
      <div class="fgrid">
        <div class="fg"><label>Actual Dollar Spend ($) — e.g. 100</label><input name="usd_spend" type="number" step="0.01" placeholder="e.g. 100" id="u_spend" oninput="calcUSD()"></div>
        <div class="fg"><label>Dollar Billed/Charged ($) — e.g. 102 (tax ke baad)</label><input name="usd_billed" type="number" step="0.01" placeholder="e.g. 102" id="u_billed" oninput="calcUSD()"></div>
        <div class="fg"><label>Dollar Rate (1$=?PKR) — e.g. 280</label><input name="usd_rate" type="number" step="0.01" placeholder="e.g. 280" id="u_rate" oninput="calcUSD()"></div>
      </div>
      <div class="calc-info">
        <span>Spend: <b id="u_s">$0</b></span>
        <span>Billed: <b id="u_b">$0</b></span>
        <span>Tax ($): <b id="u_td" style="color:#D97706">$0</b></span>
        <span>Rate: <b id="u_r">0</b></span>
        <span>Total PKR: <b id="u_tot" style="color:#DC2626">Rs 0</b></span>
      </div>
    </div>

    <!-- USD Account - Facebook (tax % based) -->
    <div id="usd_facebook_fields" style="display:none;background:#FEF3C7;border-radius:8px;padding:12px;margin-bottom:10px">
      <div style="font-size:11px;font-weight:600;color:#92400E;margin-bottom:8px">💵 Facebook USD — Tax % based</div>
      <div class="fgrid">
        <div class="fg"><label>Dollar Spend ($)</label><input name="fb_usd_spend" type="number" step="0.01" placeholder="e.g. 100" id="fb_spend" oninput="calcFBUSD()"></div>
        <div class="fg"><label>Tax % — e.g. 2 ya 3</label><input name="fb_tax_pct" type="number" step="0.01" placeholder="e.g. 2.5" id="fb_tax_pct" oninput="calcFBUSD()" value="2"></div>
        <div class="fg"><label>Dollar Rate (1$=?PKR)</label><input name="fb_usd_rate" type="number" step="0.01" placeholder="e.g. 280" id="fb_rate" oninput="calcFBUSD()"></div>
      </div>
      <div class="calc-info">
        <span>Spend: <b id="fb_s">$0</b></span>
        <span>Tax %: <b id="fb_tp">0%</b></span>
        <span>Tax $: <b id="fb_td" style="color:#D97706">$0</b></span>
        <span>Total $: <b id="fb_tot_d">$0</b></span>
        <span>Total PKR: <b id="fb_tot" style="color:#DC2626">Rs 0</b></span>
      </div>
    </div>

    <!-- PKR type selector for PKR accounts -->
    <div id="pkr_type_sel" style="display:none;margin-bottom:10px">
      <label style="font-size:11px;color:#6B7280;font-weight:600">Payment Type:</label>
      <label style="margin-left:12px;font-size:12px"><input type="radio" name="pkr_type" value="dollar" checked onchange="showPKRType()"> Dollar Purchase kiya tha</label>
      <label style="margin-left:12px;font-size:12px"><input type="radio" name="pkr_type" value="direct" onchange="showPKRType()"> Direct PKR payment</label>
    </div>

    <button class="btn bp" type="submit">✓ Save Ad Spend</button>
    </form>
    {add_acc_form}
    </div>

    <!-- RECORDS TABLE -->
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:8px">
        <div class="ct" style="margin:0">Ad Spend Records{f' — Total: <span class="r">{pk(total_pkr)}</span> | Tax: <span style="color:#D97706">{pk(total_tax)}</span>' if is_admin() else ''}</div>
        {f'<a href="/export/adspend" class="btn bs" style="font-size:11px;padding:5px 12px">⬇ Export</a>' if is_admin() else ''}
      </div>
      <div style="margin-bottom:10px;display:flex;flex-wrap:wrap;align-items:center;gap:4px">
        <span style="font-size:11px;color:#6B7280;margin-right:4px">Platform:</span>{plat_btns}
      </div>
      <div class="tw"><table>
        <thead><tr><th>Date</th><th>Platform</th><th>Account</th><th>Site</th><th>Dollar</th><th>Rate</th><th>Base PKR</th><th>Tax</th><th>Total PKR</th><th>Period</th><th>Description</th><th>Added By</th>{'<th></th>' if is_admin() else ''}</tr></thead>
        <tbody>{trs}</tbody></table></div></div>

    <script>
    document.getElementById('dt').valueAsDate=new Date();
    var today=new Date();var fd=new Date(today.getFullYear(),today.getMonth()-1,1);var ld=new Date(today.getFullYear(),today.getMonth(),0);document.getElementById('pf').valueAsDate=fd;document.getElementById('pt').valueAsDate=ld;
    var accCurrency = {{{",".join([f'"{a["id"]}":"{a["currency"]}"' for a in ad_accounts])}}};
    var accSite = {{{",".join([f'"{a["id"]}":"{a["site"]}"' for a in ad_accounts])}}};
    var accPlatform = {{{",".join([f'"{a["id"]}":"{a["platform"]}"' for a in ad_accounts])}}};

    function onAccChange(sel){{
      var id = sel.value;
      var curr = accCurrency[id] || 'PKR';
      var site = accSite[id] || '';
      var plat = accPlatform[id] || '';
      document.getElementById('site_inp').value = site;
      document.getElementById('pkr_usd_fields').style.display='none';
      document.getElementById('pkr_direct_fields').style.display='none';
      document.getElementById('usd_tiktok_fields').style.display='none';
      document.getElementById('usd_facebook_fields').style.display='none';
      document.getElementById('pkr_type_sel').style.display='none';
      if(curr==='USD'){{
        if(plat==='Facebook'){{
          document.getElementById('usd_facebook_fields').style.display='block';
        }} else {{
          document.getElementById('usd_tiktok_fields').style.display='block';
        }}
      }} else {{
        document.getElementById('pkr_type_sel').style.display='block';
        showPKRType();
      }}
    }}

    function showPKRType(){{
      var type = document.querySelector('input[name="pkr_type"]:checked').value;
      if(type==='dollar'){{
        document.getElementById('pkr_usd_fields').style.display='block';
        document.getElementById('pkr_direct_fields').style.display='none';
      }} else {{
        document.getElementById('pkr_usd_fields').style.display='none';
        document.getElementById('pkr_direct_fields').style.display='block';
      }}
    }}

    function calcPKR_USD(){{
      var pkr      = parseFloat(document.getElementById('pk_pkr').value)||0;
      var buy_rate = parseFloat(document.getElementById('pk_buy').value)||0;
      var spd_rate = parseFloat(document.getElementById('pk_spend').value)||0;
      if(buy_rate<=0 || spd_rate<=0) return;
      var d_bought = pkr / buy_rate;                    // dollar kharida
      var d_spent  = d_bought * (buy_rate/spd_rate);   // dollar kata
      var d_extra  = d_spent - d_bought;                // extra dollar
      var tax_pkr  = Math.round(d_extra * buy_rate);   // tax = extra × BUY rate (293.5)
      var total    = pkr + tax_pkr;
      document.getElementById('pk_d1').textContent      = '$'+d_bought.toFixed(2);
      document.getElementById('pk_d2').textContent      = '$'+d_spent.toFixed(2);
      document.getElementById('pk_d3').textContent      = '$'+d_extra.toFixed(2);
      document.getElementById('pk_tax_pkr').textContent = 'Rs '+tax_pkr.toLocaleString();
      document.getElementById('pk_tot').textContent     = 'Rs '+Math.round(total).toLocaleString();
    }}

    function calcPKR_Direct(){{
      var p = parseFloat(document.getElementById('pd_amt').value)||0;
      var t = parseFloat(document.getElementById('pd_tax').value)||0;
      document.getElementById('pd_tot').value = 'Rs '+Math.round(p+t).toLocaleString();
    }}

    function calcFBUSD(){{
      var spend = parseFloat(document.getElementById('fb_spend').value)||0;
      var pct   = parseFloat(document.getElementById('fb_tax_pct').value)||0;
      var rate  = parseFloat(document.getElementById('fb_rate').value)||0;
      var tax_d = spend * pct / 100;
      var total_d = spend + tax_d;
      var total_pkr = Math.round(total_d * rate);
      document.getElementById('fb_s').textContent    = '$'+spend.toFixed(2);
      document.getElementById('fb_tp').textContent   = pct+'%';
      document.getElementById('fb_td').textContent   = '$'+tax_d.toFixed(2);
      document.getElementById('fb_tot_d').textContent= '$'+total_d.toFixed(2);
      document.getElementById('fb_tot').textContent  = 'Rs '+total_pkr.toLocaleString();
    }}

    function calcUSD(){{
      var spend  = parseFloat(document.getElementById('u_spend').value)||0;
      var billed = parseFloat(document.getElementById('u_billed').value)||0;
      var rate   = parseFloat(document.getElementById('u_rate').value)||0;
      var tax_d  = billed - spend;
      var tot_pkr= Math.round(billed * rate);
      document.getElementById('u_s').textContent   = '$'+spend.toFixed(2);
      document.getElementById('u_b').textContent   = '$'+billed.toFixed(2);
      document.getElementById('u_td').textContent  = '$'+tax_d.toFixed(2);
      document.getElementById('u_r').textContent   = rate;
      document.getElementById('u_tot').textContent = 'Rs '+tot_pkr.toLocaleString();
    }}

    onAccChange(document.getElementById('acc_sel'));
    </script>"""
    return layout("Ad Spend","ads",body)

@app.route("/adspend/del/<int:i>")
@login_req
@admin_req
def del_adspend(i):
    conn = get_db()
    qry(conn,"DELETE FROM ad_spend WHERE id=%s",(i,))
    conn.commit(); conn.close()
    session.setdefault('_flashes',[]).append(("info","Deleted"))
    return redirect("/adspend")

@app.route("/adspend/account/add", methods=["POST"])
@login_req
@admin_req
def add_ad_account():
    f = request.form
    conn = get_db()
    try:
        qry(conn,"INSERT INTO ad_accounts (name,platform,currency,site) VALUES (%s,%s,%s,%s)",
            (f.get("name",""), f.get("platform","Facebook"), f.get("currency","PKR"), f.get("site","")))
        conn.commit()
        session.setdefault('_flashes',[]).append(("success",f"Account '{f.get('name')}' added!"))
    except:
        conn.rollback()
        session.setdefault('_flashes',[]).append(("danger","Account already exists!"))
    conn.close()
    return redirect("/adspend")

@app.route("/export/adspend")
@login_req
def exp_adspend():
    conn = get_db()
    rows = qry(conn,"SELECT date,platform,ad_account_name,site,dollar_amount,dollar_rate,pkr_amount,tax_amount,total_pkr,description,added_by FROM ad_spend ORDER BY date DESC").fetchall()
    conn.close()
    return make_csv(["Date","Platform","Account","Site","Dollar Amt","Rate","Base PKR","Tax","Total PKR","Description","Added By"],rows,"ad_spend.csv")

# ── EXPORTS ───────────────────────────────────────────────────────────────────
def make_csv(headers, rows, filename):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(headers)
    for r in rows: w.writerow(list(r.values()) if hasattr(r,'values') else r)
    out.seek(0)
    resp = Response("\ufeff"+out.getvalue(), mimetype="text/csv; charset=utf-8")
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return resp

@app.route("/export/purchases")
@login_req
def exp_purchases():
    conn = get_db()
    rows = qry(conn,"SELECT date,vendor,product,quantity,unit,per_unit_price,total_amount,status,notes,added_by FROM purchases ORDER BY date DESC").fetchall()
    conn.close()
    return make_csv(["Date","Vendor","Product","Qty","Unit","Per Unit","Total","Status","Notes","Added By"],rows,"purchases.csv")

@app.route("/export/expenses")
@login_req
def exp_expenses():
    conn = get_db()
    rows = qry(conn,"SELECT date,category,description,paid_to,amount,payment_method,added_by FROM expenses ORDER BY date DESC").fetchall()
    conn.close()
    return make_csv(["Date","Category","Description","Paid To","Amount","Method","Added By"],rows,"expenses.csv")

@app.route("/export/courier")
@login_req
def exp_courier():
    conn = get_db()
    rows = qry(conn,"SELECT date,courier_name,type,parcels,total_cod,charges,net_amount,reference,added_by FROM courier ORDER BY date DESC").fetchall()
    conn.close()
    return make_csv(["Date","Courier","Type","Parcels","Total COD","Charges","Net","Reference","Added By"],rows,"courier.csv")

@app.route("/export/investment")
@login_req
@admin_req
def exp_investment():
    conn = get_db()
    rows = qry(conn,"SELECT date,description,amount,added_by FROM investment ORDER BY date DESC").fetchall()
    conn.close()
    return make_csv(["Date","Description","Amount","Added By"],rows,"investment.csv")

@app.route("/export/loans")
@login_req
@admin_req
def exp_loans():
    conn = get_db()
    rows = qry(conn,"SELECT date,person,type,amount,added_by FROM loans ORDER BY date DESC").fetchall()
    conn.close()
    return make_csv(["Date","Person","Type","Amount","Added By"],rows,"loans.csv")

@app.route("/export/cashbank")
@login_req
def exp_cashbank():
    conn = get_db()
    rows = qry(conn,"SELECT date,account,type,description,amount,added_by FROM cashbank ORDER BY date ASC").fetchall()
    conn.close()
    return make_csv(["Date","Account","Type","Description","Amount","Added By"],rows,"cash_bank.csv")

@app.route("/export/pnl")
@login_req
@admin_req
def exp_pnl():
    conn = get_db()
    date_from = request.args.get("from","")
    date_to   = request.args.get("to","")

    if date_from and date_to:
        w2 = "WHERE date>=%s AND date<=%s"; p2=(date_from,date_to)
        wp = "WHERE date>=%s AND date<=%s AND status!='Unpaid'"; period=f"{date_from} to {date_to}"
    elif date_from:
        w2 = "WHERE date>=%s"; p2=(date_from,); wp="WHERE date>=%s AND status!='Unpaid'"; period=f"From {date_from}"
    elif date_to:
        w2 = "WHERE date<=%s"; p2=(date_to,); wp="WHERE date<=%s AND status!='Unpaid'"; period=f"Until {date_to}"
    else:
        w2=""; p2=(); wp="WHERE status!='Unpaid'"; period="All Time"

    tr  = float(qry(conn,f"SELECT COALESCE(SUM(total_cod),0) as v FROM courier {w2}",p2).fetchone()["v"] or 0)
    tc  = float(qry(conn,f"SELECT COALESCE(SUM(charges),0) as v FROM courier {w2}",p2).fetchone()["v"] or 0)
    tp  = float(qry(conn,f"SELECT COALESCE(SUM(total_amount),0) as v FROM purchases {wp}",p2).fetchone()["v"] or 0)
    te  = float(qry(conn,f"SELECT COALESCE(SUM(amount),0) as v FROM expenses {w2}",p2).fetchone()["v"] or 0)
    tad = float(qry(conn,f"SELECT COALESCE(SUM(total_pkr),0) as v FROM ad_spend {w2}",p2).fetchone()["v"] or 0)
    tad_tax = float(qry(conn,f"SELECT COALESCE(SUM(tax_amount),0) as v FROM ad_spend {w2}",p2).fetchone()["v"] or 0)
    ti  = float(qry(conn,"SELECT COALESCE(SUM(amount),0) as v FROM investment").fetchone()["v"] or 0)
    ll  = float(qry(conn,"SELECT COALESCE(SUM(amount),0) as v FROM loans WHERE type='Loan Taken'").fetchone()["v"] or 0)
    lw  = float(qry(conn,"SELECT COALESCE(SUM(amount),0) as v FROM loans WHERE type='Loan Repaid'").fetchone()["v"] or 0)
    cats    = qry(conn,f"SELECT category, SUM(amount) t FROM expenses {w2} GROUP BY category ORDER BY t DESC",p2).fetchall()
    ad_plats= qry(conn,f"SELECT platform, SUM(total_pkr) t, SUM(tax_amount) tax FROM ad_spend {w2} GROUP BY platform ORDER BY t DESC",p2).fetchall()
    conn.close()

    nc=tr-tc; gp=tr-tp; np=gp-tc-te-tad

    out = io.StringIO(); w = csv.writer(out)
    w.writerow([f"BizHisaab — Profit & Loss Report"])
    w.writerow([f"Period: {period}"])
    w.writerow([])
    w.writerow(["INCOME","",""])
    w.writerow(["Total COD Received","",tr])
    w.writerow(["Courier Charges","",f"-{tc}"])
    w.writerow(["Net Income","",tr-tc])
    w.writerow([])
    w.writerow(["COST OF GOODS","",""])
    w.writerow(["Total Purchases (Paid)","",f"-{tp}"])
    w.writerow(["Gross Profit","",gp])
    w.writerow([])
    w.writerow(["OPERATING EXPENSES","",""])
    for r in cats:
        w.writerow([r['category'],"",f"-{float(r['t'] or 0):.0f}"])
    w.writerow(["Total Expenses","",f"-{te}"])
    w.writerow([])
    w.writerow(["AD SPEND (Marketing)","",""])
    for r in ad_plats:
        w.writerow([r['platform'],"",f"-{float(r['t'] or 0):.0f}"])
    w.writerow(["Tax on Ads","",f"-{tad_tax}"])
    w.writerow(["Total Ad Spend","",f"-{tad}"])
    w.writerow([])
    w.writerow(["NET PROFIT / LOSS","",np])
    w.writerow([])
    w.writerow(["CAPITAL & LIABILITIES","",""])
    w.writerow(["Total Investment","",ti])
    w.writerow(["Loans Taken","",ll])
    w.writerow(["Loans Repaid","",lw])
    w.writerow(["Outstanding Loan","",ll-lw])

    out.seek(0)
    fname = f"pnl_{period.replace(' ','_')}.csv"
    resp = Response("\ufeff"+out.getvalue(), mimetype="text/csv; charset=utf-8")
    resp.headers["Content-Disposition"] = f"attachment; filename={fname}"
    return resp

@app.route("/export/all")
@login_req
@admin_req
def exp_all():
    conn = get_db()
    out = io.StringIO(); w = csv.writer(out)
    for name, headers, sql in [
        ("PURCHASES",["Date","Vendor","Product","Qty","Unit","Per Unit","Total","Status","Notes","Added By"],
         "SELECT date,vendor,product,quantity,unit,per_unit_price,total_amount,status,notes,added_by FROM purchases ORDER BY date DESC"),
        ("EXPENSES",["Date","Category","Description","Paid To","Amount","Method","Added By"],
         "SELECT date,category,description,paid_to,amount,payment_method,added_by FROM expenses ORDER BY date DESC"),
        ("COURIER",["Date","Account","Courier","Type","Parcels","Total COD","Charges","Net","Reference","Added By"],
         "SELECT date,account_name,courier_name,type,parcels,total_cod,charges,net_amount,reference,added_by FROM courier ORDER BY date DESC"),
        ("AD SPEND",["Date","Platform","Account","Site","Dollar","Rate","Base PKR","Tax","Total PKR","Period From","Period To","Description"],
         "SELECT date,platform,ad_account_name,site,dollar_amount,dollar_rate,pkr_amount,tax_amount,total_pkr,period_from,period_to,description FROM ad_spend ORDER BY date DESC"),
        ("INVESTMENT",["Date","Description","Amount","Added By"],
         "SELECT date,description,amount,added_by FROM investment ORDER BY date DESC"),
        ("LOANS",["Date","Person","Type","Amount","Added By"],
         "SELECT date,person,type,amount,added_by FROM loans ORDER BY date DESC"),
        ("CASH & BANK",["Date","Account","Type","Description","Amount","Added By"],
         "SELECT date,account,type,description,amount,added_by FROM cashbank ORDER BY date ASC"),
    ]:
        w.writerow([]); w.writerow([f"=== {name} ==="]); w.writerow(headers)
        for r in qry(conn,sql).fetchall(): w.writerow(list(r.values()))
    conn.close()
    out.seek(0)
    from datetime import datetime
    fname = f"bizhisaab_full_export_{datetime.now().strftime('%Y%m%d')}.csv"
    resp = Response("\ufeff"+out.getvalue(), mimetype="text/csv; charset=utf-8")
    resp.headers["Content-Disposition"] = f"attachment; filename={fname}"
    return resp

# ── START ─────────────────────────────────────────────────────────────────────
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)
    # ═══════════════════════════════════════════════════════════════════
# COURIER PROXY ROUTES — BizHisaab mein add karo app.py ke BILKUL END mein
# (before if __name__ == '__main__': line)
# ═══════════════════════════════════════════════════════════════════
#
# Step 1: requirements.txt mein ye line add karo:
#   flask-cors
#
# Step 2: app.py ke TOP mein (imports ke saath) ye add karo:
#   from flask_cors import CORS
#   import requests as ext_req
#   CORS(app)
#
# Step 3: Ye saara code app.py ke END mein paste karo
# ═══════════════════════════════════════════════════════════════════

POSTEX_TOKEN = "ZmU0N2Q4OTU2NTNlNDg2NGFlMDgwM2E2ZTc3ZTEwMjM6ZDgzMDZiMWI2YjU0NDI2M2E1ODY4MTM1MTU1MGUwNDA="
DIGI_PHONE   = "923123456789"
DIGI_PASS    = "12345678"
DIGI_BASE    = "https://dev.digidokaan.pk/api/v1/digidokaan"
PX_BASE      = "https://api.postex.pk/services/integration/api/order"

# ── DigiDokaan: Login ─────────────────────────────────────────────
@app.route("/proxy/digi/login", methods=["POST","OPTIONS"])
def proxy_digi_login():
    if request.method == "OPTIONS":
        return Response("", 200)
    try:
        r = ext_req.post(
            f"{DIGI_BASE}/auth/login",
            json={"phone": DIGI_PHONE, "password": DIGI_PASS},
            timeout=15
        )
        return Response(r.content, r.status_code, {"Content-Type": "application/json"})
    except Exception as e:
        return {"error": str(e)}, 500

# ── DigiDokaan: Tracking ──────────────────────────────────────────
@app.route("/proxy/digi/track", methods=["POST","OPTIONS"])
def proxy_digi_track():
    if request.method == "OPTIONS":
        return Response("", 200)
    try:
        body = request.get_json()
        token = body.get("token","")
        tracking_no = body.get("tracking_no","")
        r = ext_req.post(
            f"{DIGI_BASE}/get-order-tracking",
            json={"tracking_no": tracking_no},
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        return Response(r.content, r.status_code, {"Content-Type": "application/json"})
    except Exception as e:
        return {"error": str(e)}, 500

# ── DigiDokaan: Shipper Advice ────────────────────────────────────
@app.route("/proxy/digi/advice", methods=["POST","OPTIONS"])
def proxy_digi_advice():
    if request.method == "OPTIONS":
        return Response("", 200)
    try:
        body = request.get_json()
        token = body.get("token","")
        r = ext_req.post(
            f"{DIGI_BASE}/shipper_advice_action",
            json={
                "phone": DIGI_PHONE,
                "gateway_id": body.get("gateway_id", 3),
                "tracking_no": body.get("tracking_no",""),
                "shipper_advice_status": body.get("action","reattempt"),
                "shipper_advice_remarks": body.get("remarks",""),
                "source": "core_api"
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        return Response(r.content, r.status_code, {"Content-Type": "application/json"})
    except Exception as e:
        return {"error": str(e)}, 500

# ── PostEx: List Orders ───────────────────────────────────────────
@app.route("/proxy/postex/orders", methods=["POST","OPTIONS"])
def proxy_postex_orders():
    if request.method == "OPTIONS":
        return Response("", 200)
    try:
        body = request.get_json()
        r = ext_req.get(
            f"{PX_BASE}/v1/get-all-order",
            json={
                "orderStatusID": body.get("orderStatusID", 0),
                "fromDate": body.get("fromDate",""),
                "toDate": body.get("toDate","")
            },
            headers={"token": POSTEX_TOKEN, "Content-Type": "application/json"},
            timeout=20
        )
        return Response(r.content, r.status_code, {"Content-Type": "application/json"})
    except Exception as e:
        return {"error": str(e)}, 500

# ── PostEx: Single Track ──────────────────────────────────────────
@app.route("/proxy/postex/track/<tracking_no>", methods=["GET","OPTIONS"])
def proxy_postex_track(tracking_no):
    if request.method == "OPTIONS":
        return Response("", 200)
    try:
        r = ext_req.get(
            f"{PX_BASE}/v1/track-order/{tracking_no}",
            headers={"token": POSTEX_TOKEN},
            timeout=15
        )
        return Response(r.content, r.status_code, {"Content-Type": "application/json"})
    except Exception as e:
        return {"error": str(e)}, 500

# ── PostEx: Bulk Track ────────────────────────────────────────────
@app.route("/proxy/postex/bulk-track", methods=["POST","OPTIONS"])
def proxy_postex_bulk_track():
    if request.method == "OPTIONS":
        return Response("", 200)
    try:
        body = request.get_json()
        r = ext_req.get(
            f"{PX_BASE}/v1/track-bulk-order",
            json={"trackingNumber": body.get("trackingNumbers",[])},
            headers={"token": POSTEX_TOKEN, "Content-Type": "application/json"},
            timeout=20
        )
        return Response(r.content, r.status_code, {"Content-Type": "application/json"})
    except Exception as e:
        return {"error": str(e)}, 500

# ── PostEx: Payment Status ────────────────────────────────────────
@app.route("/proxy/postex/payment/<tracking_no>", methods=["GET","OPTIONS"])
def proxy_postex_payment(tracking_no):
    if request.method == "OPTIONS":
        return Response("", 200)
    try:
        r = ext_req.get(
            f"{PX_BASE}/v1/payment-status/{tracking_no}",
            headers={"token": POSTEX_TOKEN},
            timeout=15
        )
        return Response(r.content, r.status_code, {"Content-Type": "application/json"})
    except Exception as e:
        return {"error": str(e)}, 500

# ═══════════════════════════════════════════════════════════════════
# SHOPIFY + RETURNS MODULE — app.py ke BILKUL END mein paste karo
# ═══════════════════════════════════════════════════════════════════

SHOPIFY_TOKEN = os.environ.get("SHOPIFY_TOKEN", "")
SHOPIFY_STORE = "womencomforts.myshopify.com"
SHOPIFY_BASE  = f"https://{SHOPIFY_STORE}/admin/api/2024-01"
SHOPIFY_HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_TOKEN,
    "Content-Type": "application/json"
}
# ── Database: Returns table banana ───────────────────────────────
def init_returns_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS returns (
        id SERIAL PRIMARY KEY,
        shopify_order_id TEXT,
        shopify_order_name TEXT,
        tracking_number TEXT,
        courier_name TEXT,
        product_name TEXT,
        quantity INTEGER DEFAULT 1,
        reason TEXT,
        status TEXT DEFAULT 'returned',
        return_date TEXT,
        added_by TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )""")
    conn.commit()
    conn.close()

init_returns_db()

# ── Shopify Proxy: Orders list ────────────────────────────────────
@app.route("/proxy/shopify/orders", methods=["GET","OPTIONS"])
@login_req
def proxy_shopify_orders():
    if request.method == "OPTIONS":
        return Response("", 200)
    try:
        status = request.args.get("status", "any")
        limit  = request.args.get("limit", "50")
        r = ext_req.get(
            f"{SHOPIFY_BASE}/orders.json?status={status}&limit={limit}",
            headers={"X-Shopify-Access-Token": SHOPIFY_TOKEN},
            timeout=15
        )
        return Response(r.content, r.status_code, {"Content-Type": "application/json"})
    except Exception as e:
        return {"error": str(e)}, 500

# ── Shopify Proxy: Single order ───────────────────────────────────
@app.route("/proxy/shopify/order/<order_id>", methods=["GET","OPTIONS"])
@login_req
def proxy_shopify_order(order_id):
    if request.method == "OPTIONS":
        return Response("", 200)
    try:
        r = ext_req.get(
            f"{SHOPIFY_BASE}/orders/{order_id}.json",
            headers={"X-Shopify-Access-Token": SHOPIFY_TOKEN},
            timeout=15
        )
        return Response(r.content, r.status_code, {"Content-Type": "application/json"})
    except Exception as e:
        return {"error": str(e)}, 500

# ── Shopify Proxy: Order by name (#WC4675) ────────────────────────
@app.route("/proxy/shopify/search", methods=["GET","OPTIONS"])
@login_req
def proxy_shopify_search():
    if request.method == "OPTIONS":
        return Response("", 200)
    try:
        name = request.args.get("name", "")
        r = ext_req.get(
            f"{SHOPIFY_BASE}/orders.json?name={name}&status=any",
            headers={"X-Shopify-Access-Token": SHOPIFY_TOKEN},
            timeout=15
        )
        return Response(r.content, r.status_code, {"Content-Type": "application/json"})
    except Exception as e:
        return {"error": str(e)}, 500

# ── Returns: Add return record ────────────────────────────────────
@app.route("/returns", methods=["GET","POST"])
@login_req
def returns():
    conn = get_db()
    if request.method == "POST":
        f = request.form
        qry(conn, """INSERT INTO returns
            (shopify_order_id, shopify_order_name, tracking_number, courier_name,
             product_name, quantity, reason, status, return_date, added_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (f.get("shopify_order_id",""), f.get("shopify_order_name",""),
             f.get("tracking_number",""), f.get("courier_name",""),
             f.get("product_name",""), int(f.get("quantity",1)),
             f.get("reason",""), f.get("status","returned"),
             f.get("return_date") or today(), session.get("naam","")))
        conn.commit()
        conn.close()
        session.setdefault('_flashes',[]).append(("success","Return record save ho gaya!"))
        return redirect("/returns")

    # Stats
    rows     = qry(conn,"SELECT * FROM returns ORDER BY created_at DESC").fetchall()
    total    = qry(conn,"SELECT COUNT(*) as v FROM returns").fetchone()["v"] or 0
    returned = qry(conn,"SELECT COUNT(*) as v FROM returns WHERE status='returned'").fetchone()["v"] or 0
    lost     = qry(conn,"SELECT COUNT(*) as v FROM returns WHERE status='lost'").fetchone()["v"] or 0
    conn.close()

    trs = "".join([f"""<tr>
        <td>{r['return_date']}</td>
        <td><b style="color:#3B82F6">{r['shopify_order_name'] or '—'}</b></td>
        <td style="font-size:11px;font-family:monospace">{r['tracking_number'] or '—'}</td>
        <td><span class='badge bg-w'>{r['courier_name'] or '—'}</span></td>
        <td>{r['product_name'] or '—'}</td>
        <td>{r['quantity']}</td>
        <td>{r['reason'] or '—'}</td>
        <td><span class='badge {"bg-g" if r["status"]=="returned" else "bg-r"}'>{r['status']}</span></td>
        <td style="color:#9CA3AF;font-size:10px">{r['added_by']}</td>
        {'<td><a href="/returns/del/'+str(r["id"])+'" class="btn bd" onclick="return confirm(\'Delete?\')">Del</a></td>' if session.get('role')=='admin' else ''}
    </tr>""" for r in rows]) or "<tr><td colspan='10' style='text-align:center;color:#9CA3AF;padding:16px'>Koi return record nahi</td></tr>"

    body = f"""{flashes()}

    <div class="grid" style="margin-bottom:14px">
        <div class="met"><div class="ml">Total Returns</div><div class="mv b">{total}</div></div>
        <div class="met"><div class="ml">Returned</div><div class="mv g">{returned}</div></div>
        <div class="met"><div class="ml">Lost/Written Off</div><div class="mv r">{lost}</div></div>
    </div>

    <!-- BARCODE SCANNER SECTION -->
    <div class="card" style="border-left:4px solid #3B82F6">
        <div class="ct">📷 Barcode Scanner — Tracking Number Scan karo</div>
        <div style="font-size:12px;color:#6B7280;margin-bottom:12px">Camera se courier slip ka barcode scan karo — tracking number auto fill ho jayega</div>
        <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap">
            <button class="btn bp" onclick="startScanner()" id="scan-btn">📷 Camera Scan karo</button>
            <button class="btn" onclick="stopScanner()" id="stop-btn" style="display:none">⏹ Scan Band karo</button>
        </div>
        <div id="scanner-container" style="display:none;margin-bottom:10px">
            <video id="scanner-video" style="width:100%;max-width:400px;border-radius:8px;border:2px solid #3B82F6"></video>
            <div id="scan-status" style="font-size:12px;color:#3B82F6;margin-top:6px">Camera ready — barcode frame mein rakhein</div>
        </div>
        <div id="scan-result" style="font-size:13px;color:#16A34A;font-weight:600;margin-bottom:8px"></div>
    </div>

    <!-- ADD RETURN FORM -->
    <div class="card">
        <div class="ct">Return Record Add karo</div>
        <form method="POST" action="/returns" id="return-form">
        <div class="fgrid">
            <div class="fg">
                <label>Shopify Order # (e.g. WC4675)</label>
                <div style="display:flex;gap:8px">
                    <input name="shopify_order_name" id="order-name-input" placeholder="#WC4675" style="flex:1;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
                    <button type="button" class="btn bp" onclick="searchOrder()" style="white-space:nowrap">🔍 Search</button>
                </div>
                <input type="hidden" name="shopify_order_id" id="order-id-hidden">
            </div>
            <div class="fg">
                <label>Tracking Number</label>
                <input name="tracking_number" id="tracking-input" placeholder="Courier tracking number" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
            </div>
            <div class="fg">
                <label>Product Name</label>
                <input name="product_name" id="product-input" placeholder="Auto fill hoga ya manually likho" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
            </div>
            <div class="fg">
                <label>Courier</label>
                <select name="courier_name" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
                    <option>DigiDokaan</option>
                    <option>PostEx</option>
                    <option>MNP</option>
                    <option>Leopards</option>
                    <option>TCS</option>
                    <option>Other</option>
                </select>
            </div>
            <div class="fg">
                <label>Quantity</label>
                <input name="quantity" type="number" value="1" min="1" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
            </div>
            <div class="fg">
                <label>Return Status</label>
                <select name="status" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
                    <option value="returned">Returned ✅</option>
                    <option value="lost">Lost / Written Off ❌</option>
                </select>
            </div>
            <div class="fg">
                <label>Return Date</label>
                <input name="return_date" type="date" id="ret-dt" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
            </div>
            <div class="fg">
                <label>Reason</label>
                <input name="reason" placeholder="e.g. Customer refused, Wrong address" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
            </div>
        </div>

        <!-- Order detail preview -->
        <div id="order-preview" style="display:none;background:#EFF6FF;border-radius:8px;padding:12px;margin-bottom:10px;font-size:12px">
            <div style="font-weight:600;color:#1E40AF;margin-bottom:6px">📦 Order Details</div>
            <div id="order-preview-content"></div>
        </div>

        <button class="btn bp" type="submit">✓ Return Record Save karo</button>
        </form>
    </div>

    <!-- RETURNS TABLE -->
    <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <div class="ct" style="margin:0">All Returns</div>
            <a href="/export/returns" class="btn bs" style="font-size:11px;padding:5px 12px">⬇ Export</a>
        </div>
        <div class="tw"><table>
            <thead><tr>
                <th>Date</th><th>Order #</th><th>Tracking</th><th>Courier</th>
                <th>Product</th><th>Qty</th><th>Reason</th><th>Status</th>
                <th>Added By</th>{'<th></th>' if session.get('role')=='admin' else ''}
            </tr></thead>
            <tbody>{trs}</tbody>
        </table></div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/quagga/0.12.1/quagga.min.js"></script>
    <script>
    document.getElementById('ret-dt').valueAsDate = new Date();

    // ── Barcode Scanner ──────────────────────────────────────────
    function startScanner() {{
        document.getElementById('scanner-container').style.display = 'block';
        document.getElementById('scan-btn').style.display = 'none';
        document.getElementById('stop-btn').style.display = 'inline-block';

        Quagga.init({{
            inputStream: {{
                name: "Live",
                type: "LiveStream",
                target: document.getElementById('scanner-video'),
                constraints: {{ facingMode: "environment" }}
            }},
            decoder: {{
                readers: ["code_128_reader","ean_reader","code_39_reader","upc_reader"]
            }}
        }}, function(err) {{
            if (err) {{
                document.getElementById('scan-status').textContent = 'Camera error: ' + err;
                return;
            }}
            Quagga.start();
        }});

        Quagga.onDetected(function(result) {{
            var code = result.codeResult.code;
            document.getElementById('tracking-input').value = code;
            document.getElementById('scan-result').textContent = '✅ Scanned: ' + code;
            document.getElementById('scan-status').textContent = 'Barcode detected!';
            stopScanner();
        }});
    }}

    function stopScanner() {{
        Quagga.stop();
        document.getElementById('scanner-container').style.display = 'none';
        document.getElementById('scan-btn').style.display = 'inline-block';
        document.getElementById('stop-btn').style.display = 'none';
    }}

    // ── Shopify Order Search ─────────────────────────────────────
    async function searchOrder() {{
        var name = document.getElementById('order-name-input').value.trim();
        if (!name) {{ alert('Order number likho pehle'); return; }}
        if (!name.startsWith('#')) name = '#' + name;

        try {{
            var r = await fetch('/proxy/shopify/search?name=' + encodeURIComponent(name));
            var d = await r.json();
            var orders = d.orders || [];
            if (orders.length > 0) {{
                var o = orders[0];
                document.getElementById('order-id-hidden').value = o.id;
                document.getElementById('order-name-input').value = o.name;

                // Product names
                var products = (o.line_items || []).map(i => i.title + ' x' + i.quantity).join(', ');
                document.getElementById('product-input').value = products;

                // Preview
                var customer = (o.shipping_address || {{}});
                var preview = '<b>' + o.name + '</b> — ' + (o.customer ? o.customer.first_name + ' ' + o.customer.last_name : 'Guest') +
                    '<br>📍 ' + (customer.city || '') + ', ' + (customer.address1 || '') +
                    '<br>📦 ' + products +
                    '<br>💰 PKR ' + parseInt(o.total_price || 0).toLocaleString() +
                    '<br>📊 Status: ' + o.fulfillment_status;
                document.getElementById('order-preview-content').innerHTML = preview;
                document.getElementById('order-preview').style.display = 'block';
            }} else {{
                alert('Order nahi mila: ' + name);
            }}
        }} catch(e) {{
            alert('Error: ' + e.message);
        }}
    }}
    </script>"""

    return layout("Returns Management","ret",body)

@app.route("/returns/del/<int:i>")
@login_req
@admin_req
def del_return(i):
    conn = get_db()
    qry(conn,"DELETE FROM returns WHERE id=%s",(i,))
    conn.commit(); conn.close()
    session.setdefault('_flashes',[]).append(("info","Deleted"))
    return redirect("/returns")

@app.route("/export/returns")
@login_req
def exp_returns():
    conn = get_db()
    rows = qry(conn,"SELECT return_date,shopify_order_name,tracking_number,courier_name,product_name,quantity,reason,status,added_by FROM returns ORDER BY created_at DESC").fetchall()
    conn.close()
    return make_csv(["Date","Order #","Tracking","Courier","Product","Qty","Reason","Status","Added By"],rows,"returns.csv")

# ═══════════════════════════════════════════════════════════════════
# CASH FLOW STATEMENT — app.py ke BILKUL END mein paste karo
# (if __name__ == '__main__': se pehle)
# ═══════════════════════════════════════════════════════════════════

@app.route("/cashflow")
@login_req
@admin_req
def cashflow():
    conn = get_db()

    # Date filter
    date_from = request.args.get("from", "")
    date_to   = request.args.get("to", "")

    if date_from and date_to:
        w  = "WHERE date>=%s AND date<=%s"
        p2 = (date_from, date_to)
        period = f"{date_from} to {date_to}"
    elif date_from:
        w  = "WHERE date>=%s"
        p2 = (date_from,)
        period = f"From {date_from}"
    elif date_to:
        w  = "WHERE date<=%s"
        p2 = (date_to,)
        period = f"Until {date_to}"
    else:
        w  = ""
        p2 = ()
        period = "All Time"

    # ── CASH IN ───────────────────────────────────────────────────
    cod_in     = float(qry(conn, f"SELECT COALESCE(SUM(net_amount),0) as v FROM courier {w}", p2).fetchone()["v"] or 0)
    loan_in    = float(qry(conn, f"SELECT COALESCE(SUM(amount),0) as v FROM loans WHERE type='Loan Taken' {('AND date>=%s AND date<=%s' if date_from and date_to else ('AND date>=%s' if date_from else ('AND date<=%s' if date_to else '')))}",  p2).fetchone()["v"] or 0)
    invest_in  = float(qry(conn, f"SELECT COALESCE(SUM(amount),0) as v FROM investment {w}", p2).fetchone()["v"] or 0)
    cb_in      = float(qry(conn, f"SELECT COALESCE(SUM(amount),0) as v FROM cashbank WHERE type IN ('Money In','Opening Balance') {('AND date>=%s AND date<=%s' if date_from and date_to else ('AND date>=%s' if date_from else ('AND date<=%s' if date_to else '')))}",  p2).fetchone()["v"] or 0)
    total_in   = cod_in + loan_in + invest_in

    # ── CASH OUT ──────────────────────────────────────────────────
    purchases  = float(qry(conn, f"SELECT COALESCE(SUM(total_amount),0) as v FROM purchases WHERE status!='Unpaid' {('AND date>=%s AND date<=%s' if date_from and date_to else ('AND date>=%s' if date_from else ('AND date<=%s' if date_to else '')))}",  p2).fetchone()["v"] or 0)
    expenses   = float(qry(conn, f"SELECT COALESCE(SUM(amount),0) as v FROM expenses {w}", p2).fetchone()["v"] or 0)
    adspend    = float(qry(conn, f"SELECT COALESCE(SUM(total_pkr),0) as v FROM ad_spend {w}", p2).fetchone()["v"] or 0)
    loan_out   = float(qry(conn, f"SELECT COALESCE(SUM(amount),0) as v FROM loans WHERE type='Loan Repaid' {('AND date>=%s AND date<=%s' if date_from and date_to else ('AND date>=%s' if date_from else ('AND date<=%s' if date_to else '')))}",  p2).fetchone()["v"] or 0)
    cb_out     = float(qry(conn, f"SELECT COALESCE(SUM(amount),0) as v FROM cashbank WHERE type='Money Out' {('AND date>=%s AND date<=%s' if date_from and date_to else ('AND date>=%s' if date_from else ('AND date<=%s' if date_to else '')))}",  p2).fetchone()["v"] or 0)
    total_out  = purchases + expenses + adspend + loan_out

    # ── NET ───────────────────────────────────────────────────────
    net_cash   = total_in - total_out

    # ── ACTUAL CASH (Cash & Bank) ─────────────────────────────────
    actual_cash_in  = float(qry(conn, "SELECT COALESCE(SUM(amount),0) as v FROM cashbank WHERE type IN ('Money In','Opening Balance')").fetchone()["v"] or 0)
    actual_cash_out = float(qry(conn, "SELECT COALESCE(SUM(amount),0) as v FROM cashbank WHERE type='Money Out'").fetchone()["v"] or 0)
    actual_cash     = actual_cash_in - actual_cash_out

    # ── OUTSTANDING LOAN ──────────────────────────────────────────
    total_loan_taken  = float(qry(conn, "SELECT COALESCE(SUM(amount),0) as v FROM loans WHERE type='Loan Taken'").fetchone()["v"] or 0)
    total_loan_repaid = float(qry(conn, "SELECT COALESCE(SUM(amount),0) as v FROM loans WHERE type='Loan Repaid'").fetchone()["v"] or 0)
    outstanding_loan  = total_loan_taken - total_loan_repaid

    # ── LOAN DETAILS ──────────────────────────────────────────────
    loan_taken_rows  = qry(conn, "SELECT * FROM loans WHERE type='Loan Taken' ORDER BY date DESC LIMIT 10").fetchall()
    loan_repaid_rows = qry(conn, "SELECT * FROM loans WHERE type='Loan Repaid' ORDER BY date DESC LIMIT 10").fetchall()

    conn.close()

    untracked = net_cash - actual_cash if actual_cash > 0 else 0

    # ── STATUS COLOR ──────────────────────────────────────────────
    net_col = "g" if net_cash >= 0 else "r"

    # ── LOAN ROWS ─────────────────────────────────────────────────
    lt_rows = "".join([f"<tr><td>{r['date']}</td><td>{r['person']}</td><td class='g'><b>{pk(r['amount'])}</b></td></tr>" for r in loan_taken_rows]) or "<tr><td colspan='3' style='text-align:center;color:#9CA3AF'>No records</td></tr>"
    lr_rows = "".join([f"<tr><td>{r['date']}</td><td>{r['person']}</td><td class='r'><b>{pk(r['amount'])}</b></td></tr>" for r in loan_repaid_rows]) or "<tr><td colspan='3' style='text-align:center;color:#9CA3AF'>No records</td></tr>"

    body = f"""{flashes()}

    <!-- DATE FILTER -->
    <div class="card" style="margin-bottom:14px">
      <form method="GET" action="/cashflow" style="display:flex;gap:8px;align-items:flex-end;flex-wrap:wrap">
        <div class="fg" style="margin:0;flex:1;min-width:130px">
          <label style="font-size:11px;color:#6B7280;font-weight:600;display:block;margin-bottom:3px">From Date</label>
          <input name="from" type="date" value="{date_from}" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
        </div>
        <div class="fg" style="margin:0;flex:1;min-width:130px">
          <label style="font-size:11px;color:#6B7280;font-weight:600;display:block;margin-bottom:3px">To Date</label>
          <input name="to" type="date" value="{date_to}" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
        </div>
        <button class="btn bp" type="submit" style="padding:7px 16px">Filter</button>
        <a href="/cashflow" class="btn" style="padding:7px 16px;background:#F1F5F9;color:#6B7280">Reset</a>
      </form>
    </div>

    <!-- SUMMARY CARDS -->
    <div class="grid" style="margin-bottom:14px">
      <div class="met"><div class="ml">Total Cash Aaya</div><div class="mv g">{pk(total_in)}</div></div>
      <div class="met"><div class="ml">Total Cash Gaya</div><div class="mv r">{pk(total_out)}</div></div>
      <div class="met"><div class="ml">Net Cash</div><div class="mv {net_col}">{pk(net_cash)}</div></div>
      <div class="met"><div class="ml">Loan Baaki Dena</div><div class="mv w">{pk(outstanding_loan)}</div></div>
    </div>

    <div class="g2">

      <!-- CASH IN -->
      <div class="card">
        <div class="ct" style="color:#16A34A">Cash Aaya (+)</div>
        <div style="font-size:11px;color:#6B7280;margin-bottom:10px">Period: {period}</div>

        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #F1F5F9;font-size:13px">
          <span style="color:#6B7280">COD Received (Net)</span>
          <span class="g"><b>{pk(cod_in)}</b></span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #F1F5F9;font-size:13px">
          <span style="color:#6B7280">Loan Liya</span>
          <span class="g"><b>{pk(loan_in)}</b></span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #F1F5F9;font-size:13px">
          <span style="color:#6B7280">Investment</span>
          <span class="g"><b>{pk(invest_in)}</b></span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:10px 0;font-size:14px;font-weight:700">
          <span>Total Aaya</span>
          <span class="g">{pk(total_in)}</span>
        </div>
      </div>

      <!-- CASH OUT -->
      <div class="card">
        <div class="ct" style="color:#DC2626">Cash Gaya (-)</div>
        <div style="font-size:11px;color:#6B7280;margin-bottom:10px">Period: {period}</div>

        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #F1F5F9;font-size:13px">
          <span style="color:#6B7280">Purchases (Paid)</span>
          <span class="r"><b>{pk(purchases)}</b></span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #F1F5F9;font-size:13px">
          <span style="color:#6B7280">Expenses</span>
          <span class="r"><b>{pk(expenses)}</b></span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #F1F5F9;font-size:13px">
          <span style="color:#6B7280">Ad Spend</span>
          <span class="r"><b>{pk(adspend)}</b></span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #F1F5F9;font-size:13px">
          <span style="color:#6B7280">Loan Wapas Diya</span>
          <span class="r"><b>{pk(loan_out)}</b></span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:10px 0;font-size:14px;font-weight:700">
          <span>Total Gaya</span>
          <span class="r">{pk(total_out)}</span>
        </div>
      </div>
    </div>

    <!-- NET CASH BOX -->
    <div class="card" style="border-left:4px solid {'#16A34A' if net_cash >= 0 else '#DC2626'};margin-bottom:14px">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
        <div>
          <div class="ct" style="margin:0">Net Cash Position</div>
          <div style="font-size:12px;color:#6B7280;margin-top:2px">Total Aaya - Total Gaya</div>
        </div>
        <div style="font-size:26px;font-weight:700;color:{'#16A34A' if net_cash >= 0 else '#DC2626'}">{pk(net_cash)}</div>
      </div>

      <div style="margin-top:14px;padding-top:14px;border-top:1px solid #F1F5F9">
        <div style="display:flex;justify-content:space-between;font-size:13px;padding:6px 0;border-bottom:1px solid #F1F5F9">
          <span style="color:#6B7280">Cash & Bank mein actual</span>
          <span style="font-weight:600">{pk(actual_cash) if actual_cash > 0 else "Record nahi hai — Cash & Bank use karo"}</span>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:13px;padding:6px 0;border-bottom:1px solid #F1F5F9">
          <span style="color:#6B7280">Loan abhi baaki dena hai</span>
          <span style="font-weight:600;color:#D97706">{pk(outstanding_loan)}</span>
        </div>
        {f'''<div style="display:flex;justify-content:space-between;font-size:13px;padding:6px 0">
          <span style="color:#6B7280">Untracked (stock / unsettled COD)</span>
          <span style="font-weight:600;color:#D97706">{pk(untracked)}</span>
        </div>''' if actual_cash > 0 and untracked > 0 else ''}
      </div>
    </div>

    <!-- LOAN DETAIL -->
    <div class="g2">
      <div class="card">
        <div class="ct">Loan Liya — Detail</div>
        <div class="tw"><table>
          <thead><tr><th>Date</th><th>Person</th><th>Amount</th></tr></thead>
          <tbody>{lt_rows}</tbody>
        </table></div>
      </div>
      <div class="card">
        <div class="ct">Loan Wapas Diya — Detail</div>
        <div class="tw"><table>
          <thead><tr><th>Date</th><th>Person</th><th>Amount</th></tr></thead>
          <tbody>{lr_rows}</tbody>
        </table></div>
      </div>
    </div>

    <div style="background:#EFF6FF;border-radius:8px;padding:10px 14px;font-size:11px;color:#1E40AF;margin-top:8px">
      Cash Flow = COD + Loan Liya + Investment - Purchases - Expenses - Ads - Loan Wapas Diya
    </div>"""

    return layout("Cash Flow", "cf", body)

# ═══════════════════════════════════════════════════════════════════
# PARTIAL PAYMENT TRACKER — app.py ke BILKUL END mein paste karo
# ═══════════════════════════════════════════════════════════════════

def init_partial_payments_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS purchase_payments (
        id SERIAL PRIMARY KEY,
        purchase_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        payment_method TEXT DEFAULT 'Cash',
        payment_date TEXT,
        notes TEXT,
        added_by TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )""")
    try:
        cur.execute("ALTER TABLE purchases ADD COLUMN IF NOT EXISTS total_paid REAL DEFAULT 0")
        cur.execute("ALTER TABLE purchases ADD COLUMN IF NOT EXISTS remaining REAL DEFAULT 0")
    except: conn.rollback()
    conn.commit()
    conn.close()

init_partial_payments_db()

# ── Partial Payments Page ─────────────────────────────────────────
@app.route("/partial-payments", methods=["GET","POST"])
@login_req
def partial_payments():
    conn = get_db()

    if request.method == "POST":
        f = request.form
        purchase_id = int(f.get("purchase_id", 0))
        amount = float(f.get("amount", 0))
        if purchase_id and amount > 0:
            # Payment record karo
            qry(conn, """INSERT INTO purchase_payments
                (purchase_id, amount, payment_method, payment_date, notes, added_by)
                VALUES (%s,%s,%s,%s,%s,%s)""",
                (purchase_id, amount, f.get("payment_method","Cash"),
                 f.get("payment_date") or today(),
                 f.get("notes",""), session.get("naam","")))

            # Purchase ki total_paid aur remaining update karo
            purchase = qry(conn, "SELECT * FROM purchases WHERE id=%s", (purchase_id,)).fetchone()
            if purchase:
                total_payments = qry(conn,
                    "SELECT COALESCE(SUM(amount),0) as v FROM purchase_payments WHERE purchase_id=%s",
                    (purchase_id,)).fetchone()["v"] or 0
                total_amount = float(purchase["total_amount"] or 0)
                remaining = total_amount - float(total_payments)
                new_status = "Paid" if remaining <= 0 else "Partial"
                qry(conn, """UPDATE purchases SET
                    total_paid=%s, remaining=%s, status=%s WHERE id=%s""",
                    (float(total_payments), max(0, remaining), new_status, purchase_id))

            conn.commit()
            session.setdefault('_flashes',[]).append(("success", f"Payment Rs {int(amount):,} record ho gaya!"))
        conn.close()
        return redirect("/partial-payments")

    # Stats
    total_purchases = float(qry(conn,"SELECT COALESCE(SUM(total_amount),0) as v FROM purchases").fetchone()["v"] or 0)
    total_paid_all  = float(qry(conn,"SELECT COALESCE(SUM(amount),0) as v FROM purchase_payments").fetchone()["v"] or 0)
    partial_rows    = qry(conn,"SELECT * FROM purchases WHERE status='Partial' ORDER BY created_at DESC").fetchall()
    unpaid_rows     = qry(conn,"SELECT * FROM purchases WHERE status='Unpaid' ORDER BY created_at DESC").fetchall()
    total_baaki     = float(qry(conn,"SELECT COALESCE(SUM(total_amount),0) as v FROM purchases WHERE status IN ('Partial','Unpaid')").fetchone()["v"] or 0) - float(qry(conn,"SELECT COALESCE(SUM(total_paid),0) as v FROM purchases WHERE status='Partial'").fetchone()["v"] or 0)

    conn.close()

    def purchase_row(r, show_pay_btn=True):
        total = float(r["total_amount"] or 0)
        paid  = float(r.get("total_paid") or 0)
        rem   = float(r.get("remaining") or total if r["status"]=="Unpaid" else r.get("remaining") or 0)
        pct   = int((paid/total*100)) if total > 0 else 0
        badge = "bg-w" if r["status"]=="Partial" else "bg-r"
        pay_btn = f"<a href='/partial-payments/pay/{r['id']}' class='btn bp' style='font-size:10px;padding:3px 8px'>+ Payment</a>" if show_pay_btn and is_admin() else ""
        return f"""<tr>
            <td>{r['date']}</td>
            <td>{r['vendor']}</td>
            <td>{r['product']}</td>
            <td>{pk(total)}</td>
            <td>
                <div style="font-size:12px">{pk(paid)}</div>
                <div style="background:#E2E8F0;border-radius:4px;height:5px;width:80px;margin-top:3px">
                    <div style="background:#16A34A;border-radius:4px;height:5px;width:{pct}%"></div>
                </div>
            </td>
            <td style="color:#DC2626;font-weight:600">{pk(rem)}</td>
            <td><span class='badge {badge}'>{r['status']}</span></td>
            <td>{pay_btn}</td>
        </tr>"""

    partial_trs = "".join([purchase_row(r) for r in partial_rows]) or "<tr><td colspan='8' style='text-align:center;color:#9CA3AF;padding:12px'>Koi partial payment nahi</td></tr>"
    unpaid_trs  = "".join([purchase_row(r) for r in unpaid_rows]) or "<tr><td colspan='8' style='text-align:center;color:#9CA3AF;padding:12px'>Koi unpaid record nahi</td></tr>"

    # Partial purchases dropdown ke liye
    all_pending = partial_rows + unpaid_rows
    pending_opts = "".join([f"<option value='{r['id']}'>{r['vendor']} — {r['product']} (Baaki: {pk(float(r.get('remaining') or r['total_amount']))})</option>" for r in all_pending])

    body = f"""{flashes()}

    <div class="grid" style="margin-bottom:14px">
        <div class="met"><div class="ml">Total Purchases</div><div class="mv">{pk(total_purchases)}</div></div>
        <div class="met"><div class="ml">Total Paid</div><div class="mv g">{pk(total_paid_all)}</div></div>
        <div class="met"><div class="ml">Partial/Unpaid Baaki</div><div class="mv r">{pk(total_baaki)}</div></div>
        <div class="met"><div class="ml">Partial Records</div><div class="mv w">{len(partial_rows)}</div></div>
    </div>

    <!-- PAYMENT ADD FORM -->
    <div class="card">
        <div class="ct">Payment Record Karo</div>
        <form method="POST" action="/partial-payments">
        <div class="fgrid">
            <div class="fg">
                <label>Purchase Select Karo</label>
                <select name="purchase_id" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
                    <option value="">-- Select karo --</option>
                    {pending_opts}
                </select>
            </div>
            <div class="fg">
                <label>Payment Amount (PKR)</label>
                <input name="amount" type="number" step="0.01" placeholder="0" required style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
            </div>
            <div class="fg">
                <label>Payment Method</label>
                <select name="payment_method" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
                    <option>Cash</option>
                    <option>Bank Transfer</option>
                    <option>JazzCash</option>
                    <option>EasyPaisa</option>
                    <option>Cheque</option>
                </select>
            </div>
            <div class="fg">
                <label>Date</label>
                <input name="payment_date" type="date" id="pp-dt" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
            </div>
            <div class="fg">
                <label>Notes (Optional)</label>
                <input name="notes" placeholder="e.g. Bank transfer kiya" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
            </div>
        </div>
        <button class="btn bp" type="submit">✓ Payment Save Karo</button>
        </form>
    </div>

    <!-- PARTIAL TABLE -->
    <div class="card">
        <div class="ct">Partial Payments — Baaki Hai</div>
        <div class="tw"><table>
            <thead><tr><th>Date</th><th>Vendor</th><th>Product</th><th>Total</th><th>Paid</th><th>Baaki</th><th>Status</th><th></th></tr></thead>
            <tbody>{partial_trs}</tbody>
        </table></div>
    </div>

    <!-- UNPAID TABLE -->
    <div class="card">
        <div class="ct">Unpaid Purchases</div>
        <div class="tw"><table>
            <thead><tr><th>Date</th><th>Vendor</th><th>Product</th><th>Total</th><th>Paid</th><th>Baaki</th><th>Status</th><th></th></tr></thead>
            <tbody>{unpaid_trs}</tbody>
        </table></div>
    </div>

    <script>document.getElementById('pp-dt').valueAsDate = new Date();</script>"""

    return layout("Partial Payments", "pp", body)

# ── Quick Pay Route ───────────────────────────────────────────────
@app.route("/partial-payments/pay/<int:purchase_id>")
@login_req
@admin_req
def quick_pay(purchase_id):
    conn = get_db()
    purchase = qry(conn,"SELECT * FROM purchases WHERE id=%s",(purchase_id,)).fetchone()
    payments  = qry(conn,"SELECT * FROM purchase_payments WHERE purchase_id=%s ORDER BY created_at DESC",(purchase_id,)).fetchall()
    conn.close()

    if not purchase:
        return redirect("/partial-payments")

    total   = float(purchase["total_amount"] or 0)
    paid    = float(purchase.get("total_paid") or 0)
    rem     = float(purchase.get("remaining") or total)
    pct     = int(paid/total*100) if total > 0 else 0

    pay_rows = "".join([f"<tr><td>{p['payment_date']}</td><td>{pk(p['amount'])}</td><td>{p['payment_method']}</td><td style='color:#9CA3AF;font-size:10px'>{p['added_by']}</td></tr>" for p in payments]) or "<tr><td colspan='4' style='text-align:center;color:#9CA3AF'>Koi payment nahi</td></tr>"

    body = f"""{flashes()}
    <a href="/partial-payments" class="btn" style="margin-bottom:14px;display:inline-block">← Wapas</a>

    <div class="g2">
    <div class="card">
        <div class="ct">{purchase['vendor']} — {purchase['product']}</div>
        <div style="margin-bottom:12px">
            <div style="display:flex;justify-content:space-between;font-size:13px;padding:6px 0;border-bottom:1px solid #F1F5F9">
                <span style="color:#6B7280">Total Amount</span><span style="font-weight:600">{pk(total)}</span>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:13px;padding:6px 0;border-bottom:1px solid #F1F5F9">
                <span style="color:#6B7280">Total Paid</span><span style="color:#16A34A;font-weight:600">{pk(paid)}</span>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:13px;padding:6px 0">
                <span style="color:#6B7280">Baaki</span><span style="color:#DC2626;font-weight:600">{pk(rem)}</span>
            </div>
        </div>
        <div style="background:#E2E8F0;border-radius:6px;height:8px;margin-bottom:16px">
            <div style="background:#16A34A;border-radius:6px;height:8px;width:{pct}%"></div>
        </div>
        <form method="POST" action="/partial-payments">
            <input type="hidden" name="purchase_id" value="{purchase_id}">
            <div class="fg"><label>Payment Amount</label>
                <input name="amount" type="number" step="0.01" placeholder="Rs {int(rem):,}" value="{int(rem)}" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
            </div>
            <div class="fg"><label>Method</label>
                <select name="payment_method" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
                    <option>Cash</option><option>Bank Transfer</option><option>JazzCash</option><option>EasyPaisa</option>
                </select>
            </div>
            <div class="fg"><label>Date</label>
                <input name="payment_date" type="date" id="qp-dt" style="width:100%;padding:7px 9px;border:1px solid #E2E8F0;border-radius:7px;font-size:12px">
            </div>
            <button class="btn bp" type="submit">✓ Payment Save Karo</button>
        </form>
    </div>
    <div class="card">
        <div class="ct">Payment History</div>
        <div class="tw"><table>
            <thead><tr><th>Date</th><th>Amount</th><th>Method</th><th>By</th></tr></thead>
            <tbody>{pay_rows}</tbody>
        </table></div>
    </div>
    </div>
    <script>document.getElementById('qp-dt').valueAsDate = new Date();</script>"""

    return layout(f"Payment — {purchase['vendor']}", "pp", body)
# ═══════════════════════════════════════════════════════════════════
# SMART LEDGER v2 — BizHisaab
# ═══════════════════════════════════════════════════════════════════
#
# ⚠️ DATA SAFETY GUARANTEE:
#   - Sirf SELECT queries (read-only)
#   - Koi UPDATE / DELETE / INSERT nahi
#   - Existing /purchases route bilkul untouched
#
# 🔗 ACCESS:
#   URL: yoursite.up.railway.app/purchases-summary
#
# ═══════════════════════════════════════════════════════════════════

from datetime import datetime, timedelta

# ── Helper: Date Ranges ──────────────────────────────────────────
def _ledger_date_ranges():
    today_dt = datetime.now().date()
    yesterday_dt = today_dt - timedelta(days=1)
    week_start = today_dt - timedelta(days=today_dt.weekday())
    month_start = today_dt.replace(day=1)
    return {
        "today": today_dt.strftime("%Y-%m-%d"),
        "yesterday": yesterday_dt.strftime("%Y-%m-%d"),
        "week_start": week_start.strftime("%Y-%m-%d"),
        "month_start": month_start.strftime("%Y-%m-%d"),
    }


# ═══════════════════════════════════════════════════════════════════
# ROUTE 1: Purchases Summary + Vendor Ledger
# URL: /purchases-summary
# ═══════════════════════════════════════════════════════════════════

@app.route("/purchases-summary")
@login_req
def purchases_summary():
    conn = get_db()
    dates = _ledger_date_ranges()

    # ── Time-based queries ──
    today_data = qry(conn, """
        SELECT COALESCE(SUM(total_amount),0) AS total,
               COUNT(*)                       AS count
        FROM purchases WHERE date = %s
    """, (dates["today"],)).fetchone()

    yest_data = qry(conn, """
        SELECT COALESCE(SUM(total_amount),0) AS total,
               COUNT(*)                       AS count
        FROM purchases WHERE date = %s
    """, (dates["yesterday"],)).fetchone()

    week_data = qry(conn, """
        SELECT COALESCE(SUM(total_amount),0) AS total,
               COUNT(*)                       AS count
        FROM purchases WHERE date >= %s
    """, (dates["week_start"],)).fetchone()

    month_data = qry(conn, """
        SELECT COALESCE(SUM(total_amount),0) AS total,
               COUNT(*)                       AS count
        FROM purchases WHERE date >= %s
    """, (dates["month_start"],)).fetchone()

    # ── Vendor Summary ──
    vendors = qry(conn, """
        SELECT vendor,
               COUNT(*)                       AS purchase_count,
               COALESCE(SUM(total_amount),0)  AS total_amount,
               COALESCE(SUM(CASE WHEN status='Paid' THEN total_amount ELSE 0 END),0) AS paid_amount,
               COALESCE(SUM(CASE WHEN status!='Paid' THEN total_amount ELSE 0 END),0) AS unpaid_amount,
               MAX(date)                       AS last_purchase
        FROM purchases
        WHERE vendor IS NOT NULL AND vendor != ''
        GROUP BY vendor
        ORDER BY unpaid_amount DESC, total_amount DESC
    """).fetchall()

    conn.close()

    # ── Helpers ──
    def fmt(n):
        try:
            return f"{int(float(n)):,}"
        except:
            return "0"

    def card(title, icon, data, color):
        return f"""
        <div class="sum-card" style="border-left:4px solid {color}">
            <div class="sc-label">{icon} {title}</div>
            <div class="sc-amount" style="color:{color}">Rs {fmt(data['total'])}</div>
            <div class="sc-meta">
                <span>📦 {data['count']} purchases</span>
            </div>
        </div>"""

    cards_html = (
        card("Aaj ki Purchases", "📅", today_data, "#3B82F6") +
        card("Kal ki Purchases", "🕐", yest_data, "#8B5CF6") +
        card("Is Hafte (Mon se)", "📊", week_data, "#10B981") +
        card("Is Mahine", "📈", month_data, "#F59E0B")
    )

    # ── Vendor Table ──
    vendor_rows = ""
    if vendors:
        for v in vendors:
            name = v["vendor"] or "Unknown"
            unpaid_amt = float(v["unpaid_amount"] or 0)
            if unpaid_amt > 0:
                status_badge = f'<span class="badge-unpaid">Baaki Rs {fmt(unpaid_amt)}</span>'
            else:
                status_badge = '<span class="badge-paid">Sab Clear ✓</span>'

            vendor_rows += f"""
            <tr>
                <td><strong>{name}</strong></td>
                <td style="text-align:center">{v['purchase_count']}</td>
                <td style="text-align:right;color:#1E40AF;font-weight:600">Rs {fmt(v['total_amount'])}</td>
                <td style="text-align:right;color:#059669">Rs {fmt(v['paid_amount'])}</td>
                <td style="text-align:right;color:#DC2626;font-weight:600">Rs {fmt(v['unpaid_amount'])}</td>
                <td style="text-align:center;font-size:12px;color:#6B7280">{v['last_purchase'] or '—'}</td>
                <td style="text-align:center">{status_badge}</td>
                <td style="text-align:center">
                    <a href="/vendor/{name}" class="btn-view">👁 Dekho</a>
                </td>
            </tr>"""
    else:
        vendor_rows = '<tr><td colspan="8" style="text-align:center;padding:20px;color:#6B7280">Abhi koi vendor data nahi hai</td></tr>'

    body = f"""
    <style>
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 14px;
            margin-bottom: 20px;
        }}
        .sum-card {{
            background: white;
            padding: 16px 18px;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}
        .sc-label {{ font-size: 13px; color: #6B7280; margin-bottom: 8px; font-weight: 500; }}
        .sc-amount {{ font-size: 22px; font-weight: 700; margin-bottom: 6px; }}
        .sc-meta {{ font-size: 12px; color: #4B5563; }}

        .card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            margin-bottom: 20px;
        }}
        .ct {{ font-size: 17px; font-weight: 700; margin-bottom: 14px; color: #1F2937; }}
        .tw {{ overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{
            background: #F9FAFB;
            padding: 10px 12px;
            text-align: left;
            font-size: 12px;
            font-weight: 600;
            color: #374151;
            border-bottom: 2px solid #E5E7EB;
        }}
        td {{ padding: 12px; border-bottom: 1px solid #F3F4F6; font-size: 13px; }}
        tr:hover {{ background: #F9FAFB; }}
        .badge-paid {{
            background: #D1FAE5; color: #065F46;
            padding: 4px 10px; border-radius: 12px;
            font-size: 11px; font-weight: 600;
        }}
        .badge-unpaid {{
            background: #FEE2E2; color: #991B1B;
            padding: 4px 10px; border-radius: 12px;
            font-size: 11px; font-weight: 600;
        }}
        .btn-view {{
            background: #3B82F6; color: white;
            padding: 5px 12px; border-radius: 6px;
            text-decoration: none; font-size: 12px; font-weight: 500;
        }}
        .btn-view:hover {{ background: #2563EB; }}
        .top-nav {{ display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }}
        .nav-link {{
            background: white;
            padding: 8px 16px;
            border-radius: 8px;
            text-decoration: none;
            color: #374151;
            font-size: 13px;
            font-weight: 500;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }}
        .nav-link:hover {{ background: #F3F4F6; }}
        .nav-link.active {{ background: #3B82F6; color: white; }}
    </style>

    <div class="top-nav">
        <a href="/purchases" class="nav-link">➕ Add Purchase</a>
        <a href="/purchases-summary" class="nav-link active">📊 Summary & Vendors</a>
        <a href="/partial-payments" class="nav-link">💳 Partial Payments</a>
    </div>

    <div class="summary-grid">
        {cards_html}
    </div>

    <div class="card">
        <div class="ct">🏪 Vendor-wise Ledger ({len(vendors) if vendors else 0} vendors)</div>
        <div class="tw">
            <table>
                <thead>
                    <tr>
                        <th>Vendor Name</th>
                        <th style="text-align:center">Purchases</th>
                        <th style="text-align:right">Total Amount</th>
                        <th style="text-align:right">Paid</th>
                        <th style="text-align:right">Baaki</th>
                        <th style="text-align:center">Last Purchase</th>
                        <th style="text-align:center">Status</th>
                        <th style="text-align:center">Action</th>
                    </tr>
                </thead>
                <tbody>{vendor_rows}</tbody>
            </table>
        </div>
    </div>
    """
    return layout("Purchases Summary", "purchases", body)

# ═══════════════════════════════════════════════════════════════════
# ROUTE 2: Vendor Detail Page
# URL: /vendor/<vendor_name>
# ═══════════════════════════════════════════════════════════════════

@app.route("/vendor/<path:vendor_name>")
@login_req
def vendor_detail(vendor_name):
    conn = get_db()

    purchases = qry(conn, """
        SELECT * FROM purchases
        WHERE vendor = %s
        ORDER BY date DESC, id DESC
    """, (vendor_name,)).fetchall()

    summary = qry(conn, """
        SELECT COUNT(*)                        AS count,
               COALESCE(SUM(total_amount),0)   AS total,
               COALESCE(SUM(CASE WHEN status='Paid' THEN total_amount ELSE 0 END),0) AS paid,
               COALESCE(SUM(CASE WHEN status!='Paid' THEN total_amount ELSE 0 END),0) AS unpaid,
               MIN(date)                        AS first_purchase,
               MAX(date)                        AS last_purchase
        FROM purchases WHERE vendor = %s
    """, (vendor_name,)).fetchone()

    conn.close()

    def fmt(n):
        try:
            return f"{int(float(n)):,}"
        except:
            return "0"

    rows = ""
    if purchases:
        for p in purchases:
            status = p.get("status") or "Unpaid"
            badge_bg = "#D1FAE5;color:#065F46" if status == "Paid" else ("#FEF3C7;color:#92400E" if status == "Partial" else "#FEE2E2;color:#991B1B")
            rows += f"<tr><td>{p['date']}</td><td>{p.get('product') or '-'}</td><td style='text-align:center'>{p.get('quantity') or 0}</td><td style='text-align:center'>{p.get('unit') or '-'}</td><td style='text-align:right;color:#1E40AF'>Rs {fmt(p.get('per_unit_price') or 0)}</td><td style='text-align:right;font-weight:600'>Rs {fmt(p.get('total_amount') or 0)}</td><td style='text-align:center'><span style='background:{badge_bg};padding:3px 9px;border-radius:10px;font-size:11px;font-weight:600'>{status}</span></td><td style='font-size:11px;color:#6B7280'>{p.get('notes') or ''}</td></tr>"
    else:
        rows = "<tr><td colspan='8' style='text-align:center;padding:20px;color:#6B7280'>Koi purchase nahi mili</td></tr>"

    unpaid_amt = float(summary["unpaid"] or 0)
    status_text = "Sab Clear" if unpaid_amt <= 0 else f"Rs {fmt(unpaid_amt)} Baaki"
    status_color = "#10B981" if unpaid_amt <= 0 else "#DC2626"

    body = f"""
    <a href="/purchases-summary" style="display:inline-block;background:white;padding:8px 16px;border-radius:8px;text-decoration:none;color:#374151;font-size:13px;font-weight:500;margin-bottom:14px;box-shadow:0 1px 2px rgba(0,0,0,0.05)">Wapis Vendor List Pe</a>

    <div style="background:linear-gradient(135deg,#1E40AF 0%,#3B82F6 100%);color:white;padding:22px 26px;border-radius:12px;margin-bottom:18px">
        <div style="font-size:24px;font-weight:700;margin-bottom:6px">{vendor_name}</div>
        <div style="font-size:13px;opacity:0.95">
            Pehli purchase: {summary['first_purchase'] or '-'} | Aakhri purchase: {summary['last_purchase'] or '-'} | Status: <strong style="color:{status_color};background:white;padding:2px 8px;border-radius:6px;margin-left:4px">{status_text}</strong>
        </div>
    </div>

    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:18px">
        <div class="met"><div class="ml">Total Purchases</div><div class="mv">{summary['count']}</div></div>
        <div class="met"><div class="ml">Total Amount</div><div class="mv b">Rs {fmt(summary['total'])}</div></div>
        <div class="met"><div class="ml">Paid</div><div class="mv g">Rs {fmt(summary['paid'])}</div></div>
        <div class="met"><div class="ml">Baaki</div><div class="mv r">Rs {fmt(summary['unpaid'])}</div></div>
    </div>

    <div class="card">
        <div class="ct">Saari Purchases ({summary['count']})</div>
        <div class="tw">
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Product</th>
                        <th style="text-align:center">Qty</th>
                        <th style="text-align:center">Unit</th>
                        <th style="text-align:right">Per Unit</th>
                        <th style="text-align:right">Total</th>
                        <th style="text-align:center">Status</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>
    """

    return layout(f"Vendor: {vendor_name}", "pur", body)
