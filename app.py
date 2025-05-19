from flask import Flask, render_template, request, redirect, url_for, session, flash
import json, uuid
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = "supersecretkey123!"
DATA_FILE = "data.json"

USERS = {
    "admin": "Yaren2052."
}

# Süresi dolmuş key'leri sil
def clean_expired_keys(data):
    now = datetime.now()
    updated_keys = {}
    for key, info in data.get("keys", {}).items():
        if info["expires"] == "lifetime":
            updated_keys[key] = info
        else:
            try:
                if datetime.fromisoformat(info["expires"]) > now:
                    updated_keys[key] = info
            except:
                pass  # Tarih hatası varsa atla
    data["keys"] = updated_keys
    return data

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            data = clean_expired_keys(data)
            save_data(data)  # Temizlenmiş veriyi kaydet
            return data
    except:
        return {"keys": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

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
            flash("Başarıyla giriş yaptınız.", "success")
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
    return render_template("index.html", keys=data["keys"])

@app.route("/generate", methods=["POST"])
@login_required
def generate_key():
    duration = request.form.get("duration")
    key = str(uuid.uuid4())
    expire_date = None

    if duration == "1d":
        expire_date = (datetime.now() + timedelta(days=1)).isoformat()
    elif duration == "3d":
        expire_date = (datetime.now() + timedelta(days=3)).isoformat()
    elif duration == "1m":
        expire_date = (datetime.now() + timedelta(days=30)).isoformat()
    elif duration == "lifetime":
        expire_date = "lifetime"

    data = load_data()
    data["keys"][key] = {"hwid": None, "expires": expire_date, "status": "unused"}
    save_data(data)
    return redirect(url_for("home"))

@app.route("/delete/<key>")
@login_required
def delete_key(key):
    data = load_data()
    if key in data["keys"]:
        del data["keys"][key]
    save_data(data)
    return redirect(url_for("home"))

@app.route("/reset_hwid/<key>")
@login_required
def reset_hwid(key):
    data = load_data()
    if key in data["keys"]:
        data["keys"][key]["hwid"] = None
        data["keys"][key]["status"] = "unused"
    save_data(data)
    return redirect(url_for("home"))

@app.route("/auth", methods=["POST"])
def auth():
    key = request.form.get("key")
    hwid = request.form.get("hwid")
    data = load_data()

    if key not in data["keys"]:
        return "INVALID_KEY"

    record = data["keys"][key]

    if record["expires"] != "lifetime" and datetime.now() > datetime.fromisoformat(record["expires"]):
        return "KEY_EXPIRED"

    if record["hwid"] is None:
        record["hwid"] = hwid
        record["status"] = "used"
    elif record["hwid"] != hwid:
        return "HWID_MISMATCH"

    save_data(data)
    return "AUTH_SUCCESS"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
