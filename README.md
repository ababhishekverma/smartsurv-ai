Here it is:

```markdown
# SmartSurv AI 🔒

> AI-powered multi-zone intrusion detection system using ESP32-CAM nodes, ESP-NOW mesh communication, and YOLOv8 real-time person detection.

---

## 🧠 What It Does

SmartSurv AI is a low-cost, wireless security surveillance system built for small businesses and local establishments. It detects intruders across multiple zones, classifies threats using computer vision, and alerts security personnel in real time through a live web dashboard.

---

## 🏗️ System Architecture

```
[Zone 1]              [Zone 2]              [Zone 3]
ESP32-CAM             ESP32-CAM             ESP32-CAM
+ RCWL Radar          + RCWL Radar          + RCWL Radar
+ IR LED              + IR LED              + IR LED
     │                     │                     │
     └──────── ESP-NOW (2.4GHz Mesh) ────────────┘
                           │
                    [HUB — ESP32 Dev]
                    + OLED Display
                    + Buzzer Alerts
                           │
                      WiFi (HTTP)
                           │
                   [Laptop — Flask Server]
                   + YOLOv8n Inference
                   + WebSocket Dashboard
                           │
                   [Live Web Dashboard]
                   localhost:5000

```

---

## ✨ Features

- **3-Zone Coverage** — Independent ESP32-CAM nodes per zone
- **Radar Motion Detection** — RCWL-0516 microwave radar (5-7m range, 360°, works through walls)
- **IR Night Vision** — 850nm IR LED for low-light capture
- **YOLOv8 Person Detection** — Real-time AI inference on captured images
- **3-Tier Alert System** — Yellow → Orange → Red based on threat level
- **Tamper Detection** — SW-420 vibration sensor alerts on physical interference
- **ESP-NOW Communication** — Fast, WiFi-independent mesh between nodes and hub
- **Live Dashboard** — Real-time WebSocket updates, image thumbnails, node status
- **OLED Status Display** — Hub shows live alert level and node info
- **Buzzer Alerts** — Distinct audio patterns per alert level

---

## 🚨 Alert Levels

| Level | Trigger | Buzzer |
|-------|---------|--------|
| 🟡 YELLOW | Motion detected, no person confirmed | 1 beep |
| 🟠 ORANGE | Person detected by YOLO (≥45% confidence) | 3 beeps |
| 🔴 RED | Multiple zones triggered / repeated alerts | 6 rapid beeps |
| 🟣 TAMPER | Physical vibration on node | Continuous |

---

## 🛠️ Hardware (Per Node)

| Component | Purpose |
|-----------|---------|
| ESP32-CAM (AI Thinker) | Camera + WiFi/ESP-NOW |
| RCWL-0516 | Microwave radar motion sensor |
| IR LED 850nm + 220Ω | Night vision illumination |
| RGB LED | Visual status indicator |
| SW-420 | Vibration/tamper sensor |
| MT3608 + 18650 Battery | Portable power supply |

**Hub:** ESP32 Dev Board + SSD1306 OLED + Passive Buzzer

---

## 💻 Software Setup

### Prerequisites
```bash
pip install flask flask-socketio ultralytics opencv-python-headless Pillow
```

### Run Server
```bash
git clone https://github.com/YOUR_USERNAME/smartsurv-ai.git
cd smartsurv-ai
python app.py
```

Open browser: `http://localhost:5000`

---

## 📁 Project Structure

```
smartsurv-ai/
├── app.py                  # Flask server + YOLOv8 integration
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html          # Live dashboard (WebSocket)
├── static/
│   └── detections/         # Captured images saved here
└── README.md
```

---

## 👥 Team

Built as part of **BRAVE 2026** — NIAT Entrepreneurship Program  
Vivekananda Global University, Jaipur

---

## 📄 License

MIT License
```
