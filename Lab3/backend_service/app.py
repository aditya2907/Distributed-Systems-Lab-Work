# backend_service/app.py
import time
import logging
from flask import Flask, jsonify, request
import threading
from typing import Dict
import random

app = Flask(__name__)

# Logger
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# Controllable config (thread-safe)
_cfg_lock = threading.Lock()
_config = {
    "failure_rate": 0.0,
    "status_code": 500,
    "delay_ms": 0,
    "delay_rate": 0.0
}

def get_config() -> Dict:
    with _cfg_lock:
        return dict(_config)

def set_config(updates: Dict):
    with _cfg_lock:
        _config.update(updates)

@app.route('/data')
def get_data():
    cfg = get_config()

    # Simulate latency
    if cfg.get("delay_ms", 0) > 0 and random.random() < cfg.get("delay_rate", 0):
        delay_s = cfg["delay_ms"] / 1000.0
        logging.warn(f"Injecting delay: {delay_s:.3f}s (rate={cfg['delay_rate']})")
        time.sleep(delay_s)

    # Simulate failure
    if cfg.get("failure_rate", 0) > 0 and random.random() < cfg.get("failure_rate", 0):
        logging.warn(f"Injecting failure: status={cfg.get('status_code')} (rate={cfg['failure_rate']})")
        return jsonify({"error": "Injected failure"}), cfg.get("status_code", 500)

    return jsonify({"message": "OK", "note": "BackendService healthy"}), 200

@app.route('/config/failure', methods=['POST'])
def config_failure():
    body = request.get_json(force=True)
    if body is None:
        return jsonify({"error": "Missing JSON body"}), 400
    allowed = {}
    if "failure_rate" in body:
        allowed["failure_rate"] = float(body["failure_rate"])
    if "status_code" in body:
        allowed["status_code"] = int(body["status_code"])
    set_config(allowed)
    logging.info(f"Updated failure config: {allowed}")
    return jsonify({"result": "ok", "config": get_config()})

@app.route('/config/latency', methods=['POST'])
def config_latency():
    body = request.get_json(force=True)
    if body is None:
        return jsonify({"error": "Missing JSON body"}), 400
    allowed = {}
    if "delay_ms" in body:
        allowed["delay_ms"] = int(body["delay_ms"])
    if "delay_rate" in body:
        allowed["delay_rate"] = float(body["delay_rate"])
    set_config(allowed)
    logging.info(f"Updated latency config: {allowed}")
    return jsonify({"result": "ok", "config": get_config()})

@app.route('/config/get', methods=['GET'])
def config_get():
    return jsonify(get_config()), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
