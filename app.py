from flask import Flask, request, jsonify
import sqlite3
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)
DB_PATH = 'hwid_auth.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS keys (
                    key TEXT PRIMARY KEY,
                    duration INTEGER,
                    created_at TEXT,
                    hwid TEXT,
                    activated INTEGER DEFAULT 0
                )''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return "HWID Auth Sistemi Çalışıyor"

@app.route('/generate_key', methods=['POST'])
def generate_key():
    duration = request.json.get('duration')
    if duration not in [1, 3, 30, -1]:
        return jsonify({'error': 'Invalid duration'}), 400

    key = str(uuid.uuid4()).replace('-', '').upper()
    created_at = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO keys (key, duration, created_at) VALUES (?, ?, ?)',
              (key, duration, created_at))
    conn.commit()
    conn.close()

    return jsonify({'key': key})

@app.route('/activate_key', methods=['POST'])
def activate_key():
    key = request.json.get('key')
    hwid = request.json.get('hwid')

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT duration, created_at, hwid, activated FROM keys WHERE key = ?', (key,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Invalid key'}), 400

    duration, created_at, stored_hwid, activated = row
    created_at_dt = datetime.fromisoformat(created_at)

    if duration != -1:
        expiry_date = created_at_dt + timedelta(days=duration)
        if datetime.utcnow() > expiry_date:
            conn.close()
            return jsonify({'error': 'Key expired'}), 400

    if activated == 0:
        # İlk aktivasyon
        c.execute('UPDATE keys SET hwid = ?, activated = 1 WHERE key = ?', (hwid, key))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Key activated successfully'})
    else:
        if stored_hwid != hwid:
            conn.close()
            return jsonify({'error': 'HWID mismatch'}), 400
        else:
            conn.close()
            return jsonify({'message': 'Key already activated with this HWID'})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000)
