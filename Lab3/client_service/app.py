# client_service/app.py
import logging
import requests
import threading
import time
from flask import Flask, jsonify, request
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type
import pybreaker

# Logging config
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

app = Flask(__name__)

# Use Kubernetes service DNS name: backendservice
BACKEND_URL = "http://backendservice:5000/data"
BACKEND_CONFIG = "http://backendservice:5000/config/get"

circuit_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=15
)

class CBListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        logging.info(f"Circuit Breaker state change: {old_state} -> {new_state}")

    def failure(self, cb, exc):
        logging.warning(f"BackendService failure. Failure count: {cb.fail_counter}/{cb.fail_max}")

    def success(self, cb):
        logging.info("Circuit Breaker observed successful call")

circuit_breaker.add_listener(CBListener())

def log_before_retry(retry_state):
    """Log before each retry attempt"""
    logging.warning(f"Call failed: {retry_state.outcome.exception()}. Retrying in {retry_state.next_action.sleep:.2f}s (Attempt {retry_state.attempt_number}/{stop_after_attempt(5).stop_max_attempt})")

# Retry policy: 5 attempts, exponential backoff with jitter, retry on RequestException
@retry(stop=stop_after_attempt(5),
       wait=wait_exponential_jitter(initial=1, max=8),
       retry=retry_if_exception_type(requests.exceptions.RequestException),
       before_sleep=log_before_retry,
       reraise=True)
def call_backend_once():
    logging.info(f"Calling backend at {BACKEND_URL}")
    resp = requests.get(BACKEND_URL, timeout=3)
    if resp.status_code != 200:
        logging.warning(f"Received non-200 from backend: {resp.status_code}")
        raise requests.exceptions.RequestException(f"Status {resp.status_code}")
    return resp.json()

@app.route('/fetch')
def fetch():
    try:
        # Circuit breaker wraps the retrying call so we still short-circuit when the backend is failing continuously
        data = circuit_breaker.call(call_backend_once)
        return jsonify({"status": "ok", "data": data})
    except pybreaker.CircuitBreakerError as cbe:
        logging.error("Circuit Breaker OPEN - failing fast")
        return jsonify({"status": "fallback", "message": "circuit-open"}), 503
    except Exception as e:
        logging.error(f"Call failed after retries: {e}")
        return jsonify({"status": "fallback", "message": str(e)}), 503

# Load generator: start/stop endpoints to run a background thread calling /fetch every second
_load_thread = None
_load_stop = threading.Event()

def load_loop():
    logging.info("Load generator started")
    while not _load_stop.is_set():
        try:
            r = requests.get("http://localhost:5000/fetch", timeout=5)
            logging.info(f"Load call result: {r.status_code} - {r.text[:160]}")
        except Exception as e:
            logging.warn(f"Load call exception: {e}")
        time.sleep(1)
    logging.info("Load generator stopped")

@app.route('/start-load', methods=['POST'])
def start_load():
    global _load_thread, _load_stop
    if _load_thread is not None and _load_thread.is_alive():
        return jsonify({"status": "already-running"})
    _load_stop.clear()
    _load_thread = threading.Thread(target=load_loop, daemon=True)
    _load_thread.start()
    return jsonify({"status": "started"})

@app.route('/stop-load', methods=['POST'])
def stop_load():
    global _load_thread, _load_stop
    if _load_thread is None:
        return jsonify({"status": "not-running"})
    _load_stop.set()
    _load_thread.join(timeout=5)
    _load_thread = None
    return jsonify({"status": "stopped"})

@app.route('/status')
def status():
    return jsonify({"circuit_state": str(circuit_breaker.current_state), "backend_url": BACKEND_URL})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
