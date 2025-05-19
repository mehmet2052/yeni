from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Admin paneli için, bunu değiştir!

DB = "database.db"

# Basit admin şifresi
ADMIN_PASSWORD = "admin123"

def init_db():
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                duration_days INTEGER,
                created_at TEXT,
                hwid TEXT,
                used INTEGER DEFAULT 0
            )
        ''')
        conn.commit()

@app.before_first_request
def setup():
    init_db()

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        key = request.form.get("key")
        hwid = request.form.get("hwid")
        if not key or not hwid:
            flash("Key ve HWID gerekli", "error")
            return redirect(url_for("index"))
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM keys WHERE key = ?", (key,))
        row = cur.fetchone()
        if not row:
            flash("Geçersiz key!", "error")
            return redirect(url_for("index"))
        # Check if HWID is assigned or matches
        if row["hwid"] is None or row["hwid"] == "":
            # İlk kullanımda HWID ata ve işaretle kullanıldı
            cur.execute("UPDATE keys SET hwid = ?, used = 1, created_at = ? WHERE key = ?",
                        (hwid, datetime.now().isoformat(), key))
            conn.commit()
            flash("HWID doğrulandı. Key aktifleştirildi.", "success")
            return redirect(url_for("index"))
        else:
            if row["hwid"] != hwid:
                flash("Bu key başka bilgisayarda kullanılıyor!", "error")
                return redirect(url_for("index"))
            # Süre kontrolü
            created = datetime.fromisoformat(row["created_at"])
            expire = created + timedelta(days=row["duration_days"])
            if datetime.now() > expire:
                flash("Key süresi doldu!", "error")
                return redirect(url_for("index"))
            flash("HWID doğrulandı. Key aktif.", "success")
            return redirect(url_for("index"))
    return render_template("index.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            new_key = request.form.get("new_key").strip()
            duration = int(request.form.get("duration_days"))
            if not new_key or duration <= 0:
                flash("Geçersiz key veya süre", "error")
            else:
                try:
                    cur.execute("INSERT INTO keys (key, duration_days, created_at) VALUES (?, ?, ?)",
                                (new_key, duration, ""))
                    conn.commit()
                    flash(f"{new_key} oluşturuldu.", "success")
                except sqlite3.IntegrityError:
                    flash("Bu key zaten var.", "error")

        elif action == "delete":
            del_key = request.form.get("del_key")
            cur.execute("DELETE FROM keys WHERE key = ?", (del_key,))
            conn.commit()
            flash(f"{del_key} silindi.", "success")

        elif action == "reset_hwid":
            reset_key = request.form.get("reset_key")
            cur.execute("UPDATE keys SET hwid = '', used = 0, created_at = '' WHERE key = ?", (reset_key,))
            conn.commit()
            flash(f"{reset_key} HWID sıfırlandı.", "success")

    cur.execute("SELECT * FROM keys")
    keys = cur.fetchall()
    return render_template("admin.html", keys=keys)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pwd = request.form.get("password")
        if pwd == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("admin"))
        else:
            flash("Şifre yanlış!", "error")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("Çıkış yapıldı.", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
