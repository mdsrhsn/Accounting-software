from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, tempfile
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.secret_key = "bizhisaab-mudassar-2025"

# Railway pe /tmp mein database banao — ye hamesha kaam karta hai
DB = os.path.join(tempfile.gettempdir(), "biz.db")

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
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
        u = db.execute("SELECT id FROM users WHERE username='admin'").fetchone()
        if not u:
            db.execute("INSERT INTO users (username,password,role,naam) VALUES (?,?,?,?)",
                ("admin", generate_password_hash("admin123"), "admin", "Mudassar"))
        default_heads = ["Rickshaw/Transport","Kiraya","Tankhwah","Marketing & Ads",
                         "Bijli/Utility","Packing","Shipping","Bank Charges","Aur Kharcha"]
        for h in default_heads:
            try:
                db.execute("INSERT INTO heads (naam) VALUES (?)", (h,))
            except:
                pass
        db.commit()
        db.close()
    except Exception as e:
        print(f"init_db error: {e}")

def pk(n):
    try:
        return f"Rs {int(float(n or 0)):,}"
    except:
        return "Rs 0"

def today():
    return str(date.today())

def login_req(f):
    @wraps(f)
    def dec(*a, **kw):
        if "uid" not in session:
            return redirect("/")
        return f(*a, **kw)
    return dec

def admin_req(f):
    @wraps(f)
    def dec(*a, **kw):
        if session.get("role") != "admin":
            flash("Sirf admin access hai", "danger")
            return redirect("/dashboard")
        return f(*a, **kw)
    return dec

# ── LOGIN ──────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET","POST"])
def login():
    if "uid" in session:
        return redirect("/dashboard")
    err = ""
    if request.method == "POST":
        un = request.form.get("username","")
        pw = request.form.get("password","")
        db = get_db()
        u = db.execute("SELECT * FROM users WHERE username=?", (un,)).fetchone()
        db.close()
        if u and check_password_hash(u["password"], pw):
            session["uid"]  = u["id"]
            session["un"]   = u["username"]
            session["naam"] = u["naam"] or u["username"]
            session["role"] = u["role"]
            return redirect("/dashboard")
        err = "Username ya password galat hai!"
    return render_template("login.html", err=err)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ── DASHBOARD ──────────────────────────────────────────────────────────────────
@app.route("/dashboard")
@login_req
def dashboard():
    db = get_db()
    pu   = db.execute("SELECT COALESCE(SUM(kul_rakam),0) FROM kharidari WHERE status!='Unpaid (Baqi)'").fetchone()[0]
    ex   = db.execute("SELECT COALESCE(SUM(rakam),0) FROM akhrajaat").fetchone()[0]
    co   = db.execute("SELECT COALESCE(SUM(net_rakam),0) FROM courier").fetchone()[0]
    inv  = db.execute("SELECT COALESCE(SUM(rakam),0) FROM investment").fetchone()[0]
    ln_l = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Liya'").fetchone()[0]
    ln_w = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Wapas'").fetchone()[0]
    net  = co - pu - ex
    rpu  = db.execute("SELECT * FROM kharidari ORDER BY created_at DESC LIMIT 5").fetchall()
    rco  = db.execute("SELECT * FROM courier ORDER BY created_at DESC LIMIT 5").fetchall()
    m    = datetime.now().strftime("%Y-%m")
    rex  = db.execute("SELECT * FROM akhrajaat WHERE tarikh LIKE ? ORDER BY created_at DESC LIMIT 5", (f"{m}%",)).fetchall()
    db.close()
    return render_template("dashboard.html",
        pu=pk(pu), ex=pk(ex), co=pk(co), inv=pk(inv),
        loan=pk(ln_l - ln_w), net=pk(net), net_val=net,
        rpu=rpu, rco=rco, rex=rex)

# ── KHARIDARI ──────────────────────────────────────────────────────────────────
@app.route("/kharidari", methods=["GET","POST"])
@login_req
def kharidari():
    db = get_db()
    if request.method == "POST":
        f   = request.form
        qty = float(f.get("qty") or 1)
        dm  = float(f.get("daam") or 0)
        db.execute("""INSERT INTO kharidari
            (tarikh,vendor,maal,qty,unit,daam,kul_rakam,status,notes,darj_kiya)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (f.get("tarikh") or today(), f.get("vendor",""), f.get("maal",""),
             qty, f.get("unit","Dozen"), dm, round(qty*dm,2),
             f.get("status","Paid (Ada)"), f.get("notes",""), session["naam"]))
        db.commit()
        flash("Kharidari save ho gayi!", "success")
        return redirect("/kharidari")
    rows  = db.execute("SELECT * FROM kharidari ORDER BY created_at DESC").fetchall()
    total = db.execute("SELECT COALESCE(SUM(kul_rakam),0) FROM kharidari").fetchone()[0]
    ada   = db.execute("SELECT COALESCE(SUM(kul_rakam),0) FROM kharidari WHERE status='Paid (Ada)'").fetchone()[0]
    baqi  = db.execute("SELECT COALESCE(SUM(kul_rakam),0) FROM kharidari WHERE status='Unpaid (Baqi)'").fetchone()[0]
    db.close()
    return render_template("kharidari.html", rows=rows,
        total=pk(total), ada=pk(ada), baqi=pk(baqi))

@app.route("/kharidari/del/<int:i>")
@login_req
@admin_req
def del_kh(i):
    db = get_db()
    db.execute("DELETE FROM kharidari WHERE id=?", (i,))
    db.commit(); db.close()
    flash("Delete ho gaya", "info")
    return redirect("/kharidari")

# ── AKHRAJAAT ──────────────────────────────────────────────────────────────────
@app.route("/akhrajaat", methods=["GET","POST"])
@login_req
def akhrajaat():
    db = get_db()
    hds = [r[0] for r in db.execute("SELECT naam FROM heads ORDER BY naam").fetchall()]
    if request.method == "POST":
        f = request.form
        db.execute("""INSERT INTO akhrajaat
            (tarikh,head,tafseel,kise_diya,rakam,tariqa,darj_kiya)
            VALUES (?,?,?,?,?,?,?)""",
            (f.get("tarikh") or today(), f.get("head",""), f.get("tafseel",""),
             f.get("kise_diya",""), float(f.get("rakam") or 0),
             f.get("tariqa","Cash"), session["naam"]))
        db.commit()
        flash("Kharcha save ho gaya!", "success")
        return redirect("/akhrajaat")
    rows  = db.execute("SELECT * FROM akhrajaat ORDER BY created_at DESC").fetchall()
    total = db.execute("SELECT COALESCE(SUM(rakam),0) FROM akhrajaat").fetchone()[0]
    by_hd = db.execute("SELECT head, SUM(rakam) t FROM akhrajaat GROUP BY head ORDER BY t DESC").fetchall()
    db.close()
    return render_template("akhrajaat.html", rows=rows, hds=hds,
        total=pk(total), by_hd=by_hd)

@app.route("/akhrajaat/del/<int:i>")
@login_req
@admin_req
def del_ex(i):
    db = get_db()
    db.execute("DELETE FROM akhrajaat WHERE id=?", (i,))
    db.commit(); db.close()
    flash("Delete ho gaya", "info")
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
            flash(f"{naam} add ho gaya!", "success")
        except:
            flash("Head already exists", "danger")
        db.close()
    return redirect("/akhrajaat")

# ── COURIER ────────────────────────────────────────────────────────────────────
@app.route("/courier", methods=["GET","POST"])
@login_req
def courier():
    db = get_db()
    if request.method == "POST":
        f    = request.form
        mila = float(f.get("mila") or 0)
        chg  = float(f.get("charges") or 0)
        db.execute("""INSERT INTO courier
            (tarikh,courier_naam,qism,parcel_tadaad,mila,charges,net_rakam,reference,darj_kiya)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (f.get("tarikh") or today(), f.get("courier_naam","TCS"), f.get("qism","COD"),
             float(f.get("parcel_tadaad") or 0), mila, chg, round(mila-chg,2),
             f.get("reference",""), session["naam"]))
        db.commit()
        flash("Courier payment save ho gayi!", "success")
        return redirect("/courier")
    rows = db.execute("SELECT * FROM courier ORDER BY created_at DESC").fetchall()
    tm   = db.execute("SELECT COALESCE(SUM(mila),0) FROM courier").fetchone()[0]
    tc   = db.execute("SELECT COALESCE(SUM(charges),0) FROM courier").fetchone()[0]
    db.close()
    return render_template("courier.html", rows=rows,
        tm=pk(tm), tc=pk(tc), net=pk(tm-tc))

@app.route("/courier/del/<int:i>")
@login_req
@admin_req
def del_co(i):
    db = get_db()
    db.execute("DELETE FROM courier WHERE id=?", (i,))
    db.commit(); db.close()
    flash("Delete ho gaya", "info")
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
            (f.get("tarikh") or today(), f.get("tafseel",""),
             float(f.get("rakam") or 0), session["naam"]))
        db.commit()
        flash("Investment save ho gayi!", "success")
        return redirect("/investment")
    rows  = db.execute("SELECT * FROM investment ORDER BY created_at DESC").fetchall()
    total = db.execute("SELECT COALESCE(SUM(rakam),0) FROM investment").fetchone()[0]
    db.close()
    return render_template("investment.html", rows=rows, total=pk(total))

@app.route("/investment/del/<int:i>")
@login_req
@admin_req
def del_inv(i):
    db = get_db()
    db.execute("DELETE FROM investment WHERE id=?", (i,))
    db.commit(); db.close()
    flash("Delete ho gaya", "info")
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
            (f.get("tarikh") or today(), f.get("shakhs",""),
             f.get("qism","Loan Liya"), float(f.get("rakam") or 0), session["naam"]))
        db.commit()
        flash("Loan save ho gaya!", "success")
        return redirect("/loan")
    rows  = db.execute("SELECT * FROM loan ORDER BY created_at DESC").fetchall()
    liya  = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Liya'").fetchone()[0]
    wapas = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Wapas'").fetchone()[0]
    db.close()
    return render_template("loan.html", rows=rows,
        liya=pk(liya), wapas=pk(wapas), baqi=pk(liya-wapas))

@app.route("/loan/del/<int:i>")
@login_req
@admin_req
def del_loan(i):
    db = get_db()
    db.execute("DELETE FROM loan WHERE id=?", (i,))
    db.commit(); db.close()
    flash("Delete ho gaya", "info")
    return redirect("/loan")

# ── P&L ────────────────────────────────────────────────────────────────────────
@app.route("/pnl")
@login_req
@admin_req
def pnl():
    db = get_db()
    tr   = db.execute("SELECT COALESCE(SUM(mila),0) FROM courier").fetchone()[0]
    tc   = db.execute("SELECT COALESCE(SUM(charges),0) FROM courier").fetchone()[0]
    nc   = tr - tc
    tp   = db.execute("SELECT COALESCE(SUM(kul_rakam),0) FROM kharidari WHERE status!='Unpaid (Baqi)'").fetchone()[0]
    te   = db.execute("SELECT COALESCE(SUM(rakam),0) FROM akhrajaat").fetchone()[0]
    gp   = tr - tp
    np   = gp - tc - te
    ti   = db.execute("SELECT COALESCE(SUM(rakam),0) FROM investment").fetchone()[0]
    ll   = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Liya'").fetchone()[0]
    lw   = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Wapas'").fetchone()[0]
    hds  = db.execute("SELECT head, SUM(rakam) t FROM akhrajaat GROUP BY head ORDER BY t DESC").fetchall()
    db.close()
    return render_template("pnl.html",
        tr=pk(tr), tc=pk(tc), nc=pk(nc),
        tp=pk(tp), gp=pk(gp), gp_val=gp,
        te=pk(te), np=pk(np), np_val=np,
        ti=pk(ti), ll=pk(ll), lw=pk(lw),
        baqi=pk(ll-lw), hds=hds)

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
            flash(f"{f.get('username')} add ho gaya!", "success")
        except:
            flash("Username already exists!", "danger")
        return redirect("/users")
    rows = db.execute("SELECT id,username,naam,role FROM users ORDER BY id").fetchall()
    db.close()
    return render_template("users.html", rows=rows)

@app.route("/users/del/<int:i>")
@login_req
@admin_req
def del_user(i):
    if i == session["uid"]:
        flash("Aap khud ko delete nahi kar sakte", "danger")
        return redirect("/users")
    db = get_db()
    db.execute("DELETE FROM users WHERE id=?", (i,))
    db.commit(); db.close()
    flash("User delete ho gaya", "info")
    return redirect("/users")

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
