import os
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

# Basit veri tabanı simülasyonu (bunu gerçek db ile değiştir)
keys_db = {
    # key: { "duration": timedelta, "hwid": None, "expires": None }
    "1DAY-EXAMPLE-KEY": {"duration": timedelta(days=1), "hwid": None, "expires": None},
    "3DAY-EXAMPLE-KEY": {"duration": timedelta(days=3), "hwid": None, "expires": None},
    "1MONTH-EXAMPLE-KEY": {"duration": timedelta(days=30), "hwid": None, "expires": None},
    "LIFETIME-EXAMPLE": {"duration": None, "hwid": None, "expires": None},
}

@app.route("/activate", methods=["POST"])
def activate():
    data = request.json
    key = data.get("key")
    hwid = data.get("hwid")

    if not key or not hwid:
        return jsonify({"success": False, "message": "Key ve HWID gereklidir."}), 400

    key_data = keys_db.get(key)
    if not key_data:
        return jsonify({"success": False, "message": "Geçersiz key."}), 400

    if key_data["hwid"] and key_data["hwid"] != hwid:
        return jsonify({"success": False, "message": "Bu key başka bir cihazda aktif."}), 403

    # Lifetime key kontrolü
    if key_data["duration"] is None:
        key_data["hwid"] = hwid
        key_data["expires"] = None
        return jsonify({"success": True, "message": "Lifetime key başarıyla aktif edildi."})

    # Süre dolduysa yenile
    if key_data["expires"] and datetime.utcnow() > key_data["expires"]:
        key_data["hwid"] = None
        key_data["expires"] = None

    if not key_data["hwid"]:
        key_data["hwid"] = hwid
        key_data["expires"] = datetime.utcnow() + key_data["duration"]
        return jsonify({"success": True, "message": f"Key başarıyla {key_data['duration']} süreyle aktif edildi."})

    # Key zaten aktif ve süresi geçmemiş
    if datetime.utcnow() <= key_data["expires"]:
        return jsonify({"success": True, "message": "Key zaten aktif ve süresi geçerli."})

    return jsonify({"success": False, "message": "Key süresi doldu."}), 403

@app.route("/check", methods=["POST"])
def check():
    data = request.json
    key = data.get("key")
    hwid = data.get("hwid")

    if not key or not hwid:
        return jsonify({"success": False, "message": "Key ve HWID gereklidir."}), 400

    key_data = keys_db.get(key)
    if not key_data:
        return jsonify({"success": False, "message": "Geçersiz key."}), 400

    if key_data["hwid"] != hwid:
        return jsonify({"success": False, "message": "HWID uyuşmuyor."}), 403

    if key_data["duration"] is None:
        # Lifetime key, süresiz
        return jsonify({"success": True, "message": "Key geçerli (lifetime)."})

    if key_data["expires"] and datetime.utcnow() > key_data["expires"]:
        return jsonify({"success": False, "message": "Key süresi dolmuş."}), 403

    return jsonify({"success": True, "message": "Key geçerli."})

@app.route("/")
def index():
    return "HWID Auth Sistemi Çalışıyor"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
