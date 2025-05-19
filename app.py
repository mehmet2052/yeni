
from flask import Flask, render_template, request, redirect, url_for
import json, uuid, hashlib
from datetime import datetime, timedelta

app = Flask(__name__)
DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"keys": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/")
def home():
    data = load_data()
    return render_template("index.html", keys=data["keys"])

@app.route("/generate", methods=["POST"])
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
def delete_key(key):
    data = load_data()
    if key in data["keys"]:
        del data["keys"][key]
    save_data(data)
    return redirect(url_for("home"))

@app.route("/reset_hwid/<key>")
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
