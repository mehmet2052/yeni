from flask import Flask, render_template, request, redirect, url_for, session, flash
import json, random, string
from datetime import datetime, timedelta
from functools import wraps
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey123!")

# .env üzerinden data dosyası yolu ayarlanabilir
DATA_FILE = os.getenv("DATA_FILE", "data.json")

USERS = {
    "admin": os.getenv("ADMIN_PASSWORD", "Yaren2052.")
}

# Süresi dolmuş key'leri güncelle
def clean_expired_keys(data):
    now = datetime.now()
    for key, info in data.get("keys", {}).items():
        expires = info.get("expires", "lifetime")
        if expires == "lifetime":
            info["status"] = info.get("status", "unused")
        else:
            try:
                expire_time = datetime.fromisoformat(expires)
                info["status"] = "expired" if expire_time < now else info.get("status", "unused")
            except Exception as e:
                print(f"[HATA - Tarih dönüşüm]: {key}: {e}")
                info["status"] = "expired"
    return data

def load_data():
    try:
        if not os.path.exists(DATA_FILE):
            return {"keys": {}}
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            data = clean_expired_keys(data)
            save_data(data)
            return data
    except Exception as e:
        print(f"[HATA - load_data]: {e}")
        return {"keys": {}}

def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[HATA - save_data]: {e}")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Lütfen giriş yapınız.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in USERS and USERS[username] == password:
            session['username'] = username
            flash("Giriş yapıldı, lütfen bekleyin!", "success")
            return redirect(url_for("home"))
        else:
            flash("Kullanıcı adı veya şifre hatalı.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    session.pop('username', None)
    flash("Çıkış yapıldı.", "info")
    return redirect(url_for('login'))

@app.route("/")
@login_required
def home():
    data = load_data()
    return render_template("index.html", keys=data.get("keys", {}))

@app.route("/generate", methods=["POST"])
@login_required
def generate_key():
    prefix = request.form.get("prefix", "KEY-")
    duration = request.form.get("duration")
    hwid = request.form.get("hwid") or None

    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
    key = f"{prefix}{random_part}"

    if duration == "1d":
        expire_date = (datetime.now() + timedelta(days=1)).isoformat()
    elif duration == "3d":
        expire_date = (datetime.now() + timedelta(days=3)).isoformat()
    elif duration == "1m":
        expire_date = (datetime.now() + timedelta(days=30)).isoformat()
    elif duration == "lifetime":
        expire_date = "lifetime"
    else:
        expire_date = (datetime.now() + timedelta(days=1)).isoformat()

    data = load_data()
    data["keys"][key] = {
        "hwid": hwid,
        "expires": expire_date,
        "status": "unused"
    }
    save_data(data)
    flash(f"Key oluşturuldu: {key}", "success")
    return redirect(url_for("home"))

@app.route("/delete/<key>")
@login_required
def delete_key(key):
    data = load_data()
    if key in data.get("keys", {}):
        del data["keys"][key]
        save_data(data)
        flash(f"{key} silindi.", "info")
    else:
        flash(f"{key} bulunamadı.", "warning")
    return redirect(url_for("home"))

@app.route("/reset_hwid/<key>")
@login_required
def reset_hwid(key):
    data = load_data()
    if key in data.get("keys", {}):
        data["keys"][key]["hwid"] = None
        data["keys"][key]["status"] = "unused"
        save_data(data)
        flash(f"{key} için HWID sıfırlandı.", "success")
    else:
        flash(f"{key} bulunamadı.", "warning")
    return redirect(url_for("home"))

@app.route("/auth", methods=["POST"])
def auth():
    key = request.form.get("key")
    hwid = request.form.get("hwid")
    data = load_data()

    if key not in data.get("keys", {}):
        return "INVALID_KEY"

    record = data["keys"][key]

    # Süre kontrolü
    if record["expires"] != "lifetime":
        try:
            if datetime.now() > datetime.fromisoformat(record["expires"]):
                record["status"] = "expired"
                save_data(data)
                return "KEY_EXPIRED"
        except:
            record["status"] = "expired"
            save_data(data)
            return "KEY_EXPIRED"

    # HWID kontrolü
    if record["hwid"] is None:
        record["hwid"] = hwid
        record["status"] = "used"
    elif record["hwid"] != hwid:
        return "HWID_MISMATCH"

    save_data(data)
    return "AUTH_SUCCESS"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
