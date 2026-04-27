from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.secret_key = "mudassar-biz-secret-2025-change-this"

DB = "business.db"

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
        status TEXT, notes TEXT,
        darj_kiya TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS akhrajaat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarikh TEXT, head TEXT, tafseel TEXT,
        kise_diya TEXT, rakam REAL, tariqa TEXT,
        darj_kiya TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS courier (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarikh TEXT, courier TEXT, qism TEXT,
        parcel_tadaad REAL, mila REAL, charges REAL, net_rakam REAL,
        reference TEXT, darj_kiya TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
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
    CREATE TABLE IF NOT EXISTS expense_heads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        naam TEXT UNIQUE NOT NULL
    );
    """)
    # default admin
    existing = db.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if not existing:
        db.execute("INSERT INTO users (username,password,role,naam) VALUES (?,?,?,?)",
                   ("admin", generate_password_hash("admin123"), "admin", "Mudassar"))
    # default heads
    heads = ["Rickshaw/Transport","Kiraya (Rent)","Tankhwah (Salary)",
             "Marketing & Ads","Bijli/Utility","Packing Material","Shipping",
             "Bank Charges","Aur Kharcha"]
    for h in heads:
        try: db.execute("INSERT INTO expense_heads (naam) VALUES (?)", (h,))
        except: pass
    db.commit(); db.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Sirf admin ye kar sakta hai","danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated

def pk(n):
    try: return f"Rs {int(float(n)):,}"
    except: return "Rs 0"

# ── AUTH ──────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET","POST"])
def login():
    if "user_id" in session: return redirect(url_for("dashboard"))
    if request.method == "POST":
        db = get_db()
        u = db.execute("SELECT * FROM users WHERE username=?",
                       (request.form["username"],)).fetchone()
        db.close()
        if u and check_password_hash(u["password"], request.form["password"]):
            session["user_id"] = u["id"]
            session["username"] = u["username"]
            session["naam"] = u["naam"] or u["username"]
            session["role"] = u["role"]
            return redirect(url_for("dashboard"))
        flash("Username ya password galat hai","danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    total_pu  = db.execute("SELECT COALESCE(SUM(kul_rakam),0) FROM kharidari WHERE status!='Unpaid (Baqi)'").fetchone()[0]
    total_ex  = db.execute("SELECT COALESCE(SUM(rakam),0) FROM akhrajaat").fetchone()[0]
    net_co    = db.execute("SELECT COALESCE(SUM(net_rakam),0) FROM courier").fetchone()[0]
    total_inv = db.execute("SELECT COALESCE(SUM(rakam),0) FROM investment").fetchone()[0]
    ln_taken  = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Liya'").fetchone()[0]
    ln_wapas  = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Wapas'").fetchone()[0]
    net_p     = net_co - total_pu - total_ex

    recent_pu = db.execute("SELECT * FROM kharidari ORDER BY created_at DESC LIMIT 6").fetchall()
    recent_co = db.execute("SELECT * FROM courier ORDER BY created_at DESC LIMIT 6").fetchall()
    m = datetime.now().strftime("%Y-%m")
    month_ex  = db.execute("SELECT * FROM akhrajaat WHERE tarikh LIKE ? ORDER BY created_at DESC LIMIT 6", (f"{m}%",)).fetchall()
    db.close()

    return render_template("dashboard.html",
        total_pu=pk(total_pu), total_ex=pk(total_ex),
        net_co=pk(net_co), total_inv=pk(total_inv),
        baqi_loan=pk(ln_taken - ln_wapas),
        net_p=pk(net_p), net_p_val=net_p,
        recent_pu=recent_pu, recent_co=recent_co, month_ex=month_ex)

# ── KHARIDARI ────────────────────────────────────────────────────────────────
@app.route("/kharidari", methods=["GET","POST"])
@login_required
def kharidari():
    db = get_db()
    if request.method == "POST":
        f = request.form
        qty  = float(f.get("qty",1) or 1)
        daam = float(f.get("daam",0) or 0)
        db.execute("""INSERT INTO kharidari
            (tarikh,vendor,maal,qty,unit,daam,kul_rakam,status,notes,darj_kiya)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (f.get("tarikh") or str(date.today()),
             f["vendor"], f["maal"], qty,
             f.get("unit","Dozen"), daam, round(qty*daam,2),
             f.get("status","Paid (Ada)"), f.get("notes",""),
             session["naam"]))
        db.commit()
        flash("Kharidari save ho gayi!","success")
        return redirect(url_for("kharidari"))
    rows = db.execute("SELECT * FROM kharidari ORDER BY created_at DESC").fetchall()
    total     = db.execute("SELECT COALESCE(SUM(kul_rakam),0) FROM kharidari").fetchone()[0]
    ada       = db.execute("SELECT COALESCE(SUM(kul_rakam),0) FROM kharidari WHERE status='Paid (Ada)'").fetchone()[0]
    baqi      = db.execute("SELECT COALESCE(SUM(kul_rakam),0) FROM kharidari WHERE status='Unpaid (Baqi)'").fetchone()[0]
    db.close()
    return render_template("kharidari.html", rows=rows,
                           total=pk(total), ada=pk(ada), baqi=pk(baqi))

@app.route("/kharidari/delete/<int:rid>")
@login_required
@admin_required
def del_kharidari(rid):
    db = get_db()
    db.execute("DELETE FROM kharidari WHERE id=?", (rid,))
    db.commit(); db.close()
    flash("Record delete ho gaya","info")
    return redirect(url_for("kharidari"))

# ── AKHRAJAAT ────────────────────────────────────────────────────────────────
@app.route("/akhrajaat", methods=["GET","POST"])
@login_required
def akhrajaat():
    db = get_db()
    heads = [r[0] for r in db.execute("SELECT naam FROM expense_heads ORDER BY naam").fetchall()]
    if request.method == "POST":
        f = request.form
        db.execute("""INSERT INTO akhrajaat
            (tarikh,head,tafseel,kise_diya,rakam,tariqa,darj_kiya)
            VALUES (?,?,?,?,?,?,?)""",
            (f.get("tarikh") or str(date.today()),
             f.get("head",""), f["tafseel"],
             f.get("kise_diya",""), float(f.get("rakam",0) or 0),
             f.get("tariqa","Naqd (Cash)"), session["naam"]))
        db.commit()
        flash("Kharcha save ho gaya!","success")
        return redirect(url_for("akhrajaat"))
    rows = db.execute("SELECT * FROM akhrajaat ORDER BY created_at DESC").fetchall()
    total = db.execute("SELECT COALESCE(SUM(rakam),0) FROM akhrajaat").fetchone()[0]
    head_rows = db.execute("""SELECT head, SUM(rakam) as tot FROM akhrajaat
                              GROUP BY head ORDER BY tot DESC""").fetchall()
    db.close()
    return render_template("akhrajaat.html", rows=rows, heads=heads,
                           total=pk(total), head_rows=head_rows)

@app.route("/akhrajaat/delete/<int:rid>")
@login_required
@admin_required
def del_akhrajaat(rid):
    db = get_db()
    db.execute("DELETE FROM akhrajaat WHERE id=?", (rid,))
    db.commit(); db.close()
    flash("Record delete ho gaya","info")
    return redirect(url_for("akhrajaat"))

# ── COURIER ──────────────────────────────────────────────────────────────────
@app.route("/courier", methods=["GET","POST"])
@login_required
def courier():
    db = get_db()
    if request.method == "POST":
        f = request.form
        mila = float(f.get("mila",0) or 0)
        chg  = float(f.get("charges",0) or 0)
        db.execute("""INSERT INTO courier
            (tarikh,courier,qism,parcel_tadaad,mila,charges,net_rakam,reference,darj_kiya)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (f.get("tarikh") or str(date.today()),
             f.get("courier","TCS"), f.get("qism","COD"),
             float(f.get("parcel_tadaad",0) or 0),
             mila, chg, round(mila-chg,2),
             f.get("reference",""), session["naam"]))
        db.commit()
        flash("Courier payment save ho gayi!","success")
        return redirect(url_for("courier"))
    rows     = db.execute("SELECT * FROM courier ORDER BY created_at DESC").fetchall()
    tot_mila = db.execute("SELECT COALESCE(SUM(mila),0) FROM courier").fetchone()[0]
    tot_chg  = db.execute("SELECT COALESCE(SUM(charges),0) FROM courier").fetchone()[0]
    db.close()
    return render_template("courier.html", rows=rows,
                           tot_mila=pk(tot_mila), tot_chg=pk(tot_chg),
                           net=pk(tot_mila - tot_chg))

@app.route("/courier/delete/<int:rid>")
@login_required
@admin_required
def del_courier(rid):
    db = get_db()
    db.execute("DELETE FROM courier WHERE id=?", (rid,))
    db.commit(); db.close()
    flash("Record delete ho gaya","info")
    return redirect(url_for("courier"))

# ── INVESTMENT ───────────────────────────────────────────────────────────────
@app.route("/investment", methods=["GET","POST"])
@login_required
@admin_required
def investment():
    db = get_db()
    if request.method == "POST":
        f = request.form
        db.execute("INSERT INTO investment (tarikh,tafseel,rakam,darj_kiya) VALUES (?,?,?,?)",
                   (f.get("tarikh") or str(date.today()),
                    f["tafseel"], float(f.get("rakam",0) or 0), session["naam"]))
        db.commit()
        flash("Investment save ho gayi!","success")
        return redirect(url_for("investment"))
    rows  = db.execute("SELECT * FROM investment ORDER BY created_at DESC").fetchall()
    total = db.execute("SELECT COALESCE(SUM(rakam),0) FROM investment").fetchone()[0]
    db.close()
    return render_template("investment.html", rows=rows, total=pk(total))

@app.route("/investment/delete/<int:rid>")
@login_required
@admin_required
def del_investment(rid):
    db = get_db()
    db.execute("DELETE FROM investment WHERE id=?", (rid,))
    db.commit(); db.close()
    flash("Record delete ho gaya","info")
    return redirect(url_for("investment"))

# ── LOAN ─────────────────────────────────────────────────────────────────────
@app.route("/loan", methods=["GET","POST"])
@login_required
@admin_required
def loan():
    db = get_db()
    if request.method == "POST":
        f = request.form
        db.execute("INSERT INTO loan (tarikh,shakhs,qism,rakam,darj_kiya) VALUES (?,?,?,?,?)",
                   (f.get("tarikh") or str(date.today()),
                    f["shakhs"], f.get("qism","Loan Liya"),
                    float(f.get("rakam",0) or 0), session["naam"]))
        db.commit()
        flash("Loan record save ho gaya!","success")
        return redirect(url_for("loan"))
    rows  = db.execute("SELECT * FROM loan ORDER BY created_at DESC").fetchall()
    liya  = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Liya'").fetchone()[0]
    wapas = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Wapas'").fetchone()[0]
    db.close()
    return render_template("loan.html", rows=rows,
                           liya=pk(liya), wapas=pk(wapas), baqi=pk(liya-wapas))

@app.route("/loan/delete/<int:rid>")
@login_required
@admin_required
def del_loan(rid):
    db = get_db()
    db.execute("DELETE FROM loan WHERE id=?", (rid,))
    db.commit(); db.close()
    flash("Record delete ho gaya","info")
    return redirect(url_for("loan"))

# ── P&L ──────────────────────────────────────────────────────────────────────
@app.route("/pnl")
@login_required
@admin_required
def pnl():
    db = get_db()
    tot_rec  = db.execute("SELECT COALESCE(SUM(mila),0) FROM courier").fetchone()[0]
    tot_chg  = db.execute("SELECT COALESCE(SUM(charges),0) FROM courier").fetchone()[0]
    net_co   = tot_rec - tot_chg
    tot_pu   = db.execute("SELECT COALESCE(SUM(kul_rakam),0) FROM kharidari WHERE status!='Unpaid (Baqi)'").fetchone()[0]
    tot_ex   = db.execute("SELECT COALESCE(SUM(rakam),0) FROM akhrajaat").fetchone()[0]
    gross_p  = tot_rec - tot_pu
    net_p    = gross_p - tot_chg - tot_ex
    tot_inv  = db.execute("SELECT COALESCE(SUM(rakam),0) FROM investment").fetchone()[0]
    liya     = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Liya'").fetchone()[0]
    wapas    = db.execute("SELECT COALESCE(SUM(rakam),0) FROM loan WHERE qism='Loan Wapas'").fetchone()[0]
    head_rows= db.execute("SELECT head, SUM(rakam) as tot FROM akhrajaat GROUP BY head ORDER BY tot DESC").fetchall()
    db.close()
    return render_template("pnl.html",
        tot_rec=pk(tot_rec), tot_chg=pk(tot_chg), net_co=pk(net_co),
        tot_pu=pk(tot_pu), gross_p=pk(gross_p), gross_p_val=gross_p,
        tot_ex=pk(tot_ex), net_p=pk(net_p), net_p_val=net_p,
        tot_inv=pk(tot_inv), liya=pk(liya), wapas=pk(wapas),
        baqi=pk(liya-wapas), head_rows=head_rows)

# ── USERS (admin only) ───────────────────────────────────────────────────────
@app.route("/users", methods=["GET","POST"])
@login_required
@admin_required
def users():
    db = get_db()
    if request.method == "POST":
        f = request.form
        try:
            db.execute("INSERT INTO users (username,password,role,naam) VALUES (?,?,?,?)",
                       (f["username"], generate_password_hash(f["password"]),
                        f.get("role","employee"), f.get("naam","")))
            db.commit()
            flash(f"{f['username']} add ho gaya!","success")
        except:
            flash("Username already exists","danger")
        return redirect(url_for("users"))
    rows = db.execute("SELECT id,username,naam,role FROM users ORDER BY id").fetchall()
    db.close()
    return render_template("users.html", rows=rows)

@app.route("/users/delete/<int:uid>")
@login_required
@admin_required
def del_user(uid):
    if uid == session["user_id"]:
        flash("Aap khud ko delete nahi kar sakte","danger")
        return redirect(url_for("users"))
    db = get_db()
    db.execute("DELETE FROM users WHERE id=?", (uid,))
    db.commit(); db.close()
    flash("User delete ho gaya","info")
    return redirect(url_for("users"))

@app.route("/heads", methods=["POST"])
@login_required
@admin_required
def add_head():
    naam = request.form.get("naam","").strip()
    if naam:
        db = get_db()
        try: db.execute("INSERT INTO expense_heads (naam) VALUES (?)", (naam,))
        except: flash("Head already exists","danger")
        db.commit(); db.close()
    return redirect(url_for("akhrajaat"))

init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
