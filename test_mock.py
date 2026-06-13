"""
test_mock.py — Simulate ESP32-CAM nodes sending data to Flask server
Run this while app.py is running to test without hardware.

Usage:
    python test_mock.py
"""

import requests
import time
import random
import json

SERVER = "http://localhost:5000"

NODES = [
    {"node_id": "node_1", "zone": "Front Gate"},
    {"node_id": "node_2", "zone": "Back Entrance"},
    {"node_id": "node_3", "zone": "Side Corridor"},
]

def send_detection(node, person_detected=True, confidence=None, tamper=False):
    conf = confidence if confidence else random.randint(30, 95)
    payload = {
        "node_id"         : node["node_id"],
        "zone"            : node["zone"],
        "confidence"      : conf,
        "person_detected" : person_detected,
        "tamper"          : tamper,
        "image"           : None   # no image in mock
    }
    try:
        res = requests.post(f"{SERVER}/detection", json=payload, timeout=3)
        data = res.json()
        print(f"  → Sent from {node['zone']} | conf={conf}% | Alert: {data['alert_level']}")
    except Exception as e:
        print(f"  ✗ Error: {e} — is app.py running?")

def run_scenarios():
    print("\n── Scenario 1: Single node, low confidence (expect YELLOW) ──")
    send_detection(NODES[0], person_detected=False, confidence=30)
    time.sleep(2)

    print("\n── Scenario 2: Single node, high confidence (expect ORANGE) ──")
    send_detection(NODES[1], person_detected=True, confidence=78)
    time.sleep(2)

    print("\n── Scenario 3: Two nodes within 60s (expect RED) ──")
    send_detection(NODES[0], person_detected=True, confidence=60)
    time.sleep(1)
    send_detection(NODES[2], person_detected=True, confidence=55)
    time.sleep(2)

    print("\n── Scenario 4: Loitering — 3 triggers on same node (expect RED) ──")
    for i in range(3):
        send_detection(NODES[0], person_detected=True, confidence=50)
        time.sleep(1)

    print("\n── Scenario 5: Tamper detected (expect TAMPER) ──")
    send_detection(NODES[1], tamper=True)
    time.sleep(2)

    print("\n✓ All scenarios done. Check dashboard at http://localhost:5000\n")

if __name__ == "__main__":
    print("SmartSurv Mock Test")
    print(f"Sending to: {SERVER}")
    print("Make sure app.py is running first!\n")
    run_scenarios()
