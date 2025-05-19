from flask import Flask, request, jsonify
import json
import hashlib

app = Flask(__name__)

def load_keys():
    with open("keys.json", "r") as f:
        return json.load(f)

def save_keys(data):
    with open("keys.json", "w") as f:
        json.dump(data, f, indent=4)

@app.route("/auth", methods=["POST"])
def auth():
    hwid = request.json.get("hwid")
    key = request.json.get("key")

    keys = load_keys()

    if key not in keys:
        return jsonify({"status": "invalid_key"}), 403

    data = keys[key]

    if not data["used"]:
        data["hwid"] = hwid
        data["used"] = True
        save_keys(keys)
        return jsonify({"status": "success", "message": "Key activated."})

    elif data["hwid"] == hwid:
        return jsonify({"status": "success", "message": "Key already activated."})

    else:
        return jsonify({"status": "denied", "message": "Key already used on another device."}), 403

@app.route("/")
def index():
    return "Key Auth System Running."

if __name__ == "__main__":
    app.run()