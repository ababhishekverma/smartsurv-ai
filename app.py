from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from datetime import datetime
import base64, os, json, time, threading, io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smartsurv-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# ── YOLO Setup ─────────────────────────────────────────────────────────────
yolo_model = None

def load_yolo():
    global yolo_model
    try:
        from ultralytics import YOLO
        yolo_model = YOLO("yolov8n.pt")  # auto-downloads on first run
        print("[YOLO] Model loaded — yolov8n ready!")
    except Exception as e:
        print(f"[YOLO] Could not load model: {e} — running without YOLO")

threading.Thread(target=load_yolo, daemon=True).start()

# ── Storage ────────────────────────────────────────────────────────────────
detections       = []
node_last_trigger = {}
alert_counts     = {}

DETECTIONS_DIR = os.path.join("static", "detections")
os.makedirs(DETECTIONS_DIR, exist_ok=True)

# ── YOLO Inference ─────────────────────────────────────────────────────────
def run_yolo(image_bytes):
    """Returns (person_detected: bool, confidence: float)"""
    if yolo_model is None:
        return False, 0.0
    try:
        from PIL import Image
        import numpy as np
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        results = yolo_model(img, verbose=False)[0]
        best_conf = 0.0
        person_found = False
        for box in results.boxes:
            cls  = int(box.cls[0])
            conf = float(box.conf[0])
            if cls == 0 and conf > best_conf:   # class 0 = person
                person_found = True
                best_conf    = conf
        return person_found, round(best_conf * 100, 1)
    except Exception as e:
        print(f"[YOLO] Inference error: {e}")
        return False, 0.0

# ── Alert Level Logic ──────────────────────────────────────────────────────
def compute_alert_level(node_id, confidence, person_detected, tamper=False):
    now = time.time()
    if tamper:
        return "TAMPER"
    if node_id not in alert_counts:
        alert_counts[node_id] = []
    alert_counts[node_id].append(now)
    alert_counts[node_id] = [t for t in alert_counts[node_id] if now - t < 600]
    if len(alert_counts[node_id]) >= 3:
        return "RED"
    recent_nodes = {nid for nid, ts in node_last_trigger.items() if now - ts < 60}
    recent_nodes.add(node_id)
    if len(recent_nodes) >= 2:
        return "RED"
    if person_detected and confidence >= 45:
        return "ORANGE"
    return "YELLOW"

# ── Main Detection Endpoint ────────────────────────────────────────────────
@app.route('/detection', methods=['POST'])
def receive_detection():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    node_id    = data.get("node_id", "unknown")
    zone       = data.get("zone", "Unknown Zone")
    tamper     = data.get("tamper", False)
    image_b64  = data.get("image", None)

    # Save image
    image_path = None
    image_bytes = None
    if image_b64:
        try:
            image_bytes = base64.b64decode(image_b64)
            filename    = f"{node_id}_{int(time.time())}.jpg"
            filepath    = os.path.join(DETECTIONS_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            image_path = f"/static/detections/{filename}"
        except Exception as e:
            print(f"[Image] Save error: {e}")

    # YOLO inference
    if image_bytes and not tamper:
        person_detected, confidence = run_yolo(image_bytes)
        print(f"[YOLO] person={person_detected}, conf={confidence}%")
    else:
        person_detected = data.get("person_detected", False)
        confidence      = float(data.get("confidence", 0))

    alert_level = compute_alert_level(node_id, confidence, person_detected, tamper)
    node_last_trigger[node_id] = time.time()

    event = {
        "id"             : len(detections) + 1,
        "node_id"        : node_id,
        "zone"           : zone,
        "confidence"     : confidence,
        "person_detected": person_detected,
        "tamper"         : tamper,
        "alert_level"    : alert_level,
        "image_path"     : image_path,
        "timestamp"      : datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
    }

    detections.insert(0, event)
    if len(detections) > 100:
        detections.pop()

    socketio.emit('new_detection', event)
    print(f"[{event['timestamp']}] {alert_level} | {zone} | conf={confidence}%")
    return jsonify({"status": "ok", "alert_level": alert_level}), 200

# ── Alert Endpoint (Hub Arduino code ke liye) ─────────────────────────────
@app.route('/alert', methods=['POST'])
def receive_alert():
    """Alias for /detection — Hub ka existing code /alert use karta hai"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    # Hub se aane wala format map karo
    mapped = {
        "node_id"         : f"node_{data.get('node_id', 1)}",
        "zone"            : data.get("zone", "Unknown"),
        "confidence"      : float(data.get("confidence", 0)),
        "person_detected" : data.get("pir", False),
        "tamper"          : data.get("tamper", False),
        "image"           : data.get("image", None)
    }
    # Reuse detection logic
    request._cached_json = (mapped, mapped)
    return receive_detection()

# ── Status ─────────────────────────────────────────────────────────────────
@app.route('/status', methods=['GET'])
def status():
    now = time.time()
    nodes_online = {nid: (now - ts) < 120  # 30 se 120 karo
        for nid, ts in node_last_trigger.items()
    }
    return jsonify({
        "total_detections": len(detections),
        "nodes_online"    : nodes_online,
        "last_alert"      : detections[0]["alert_level"] if detections else None,
        "yolo_ready"      : yolo_model is not None
    })

@app.route('/detections', methods=['GET'])
def get_detections():
    return jsonify(detections[:20])

@app.route('/')
def dashboard():
    return render_template('index.html')

@socketio.on('connect')
def on_connect():
    emit('history', detections[:20])

if __name__ == '__main__':
    print("=" * 50)
    print("  SmartSurv AI — Flask Server")
    print("  http://localhost:5000")
    print("  POST /alert      ← Hub Arduino code")
    print("  POST /detection  ← Direct / mock")
    print("=" * 50)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
