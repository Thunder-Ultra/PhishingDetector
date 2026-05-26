"""
app.py — PhishGuard Flask API
Receives a URL from the Chrome extension, runs the ML model,
and returns a JSON prediction with confidence score.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

from model.predictor import predict_url   # our ML wrapper

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})   # allow Chrome extension origin


# ── Health Check ──────────────────────────────────────
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "PhishGuard API v1.0"})


# ── Prediction Endpoint ───────────────────────────────
@app.route("/predict", methods=["POST"])
def predict():
    """
    Expects JSON body: { "url": "https://example.com" }

    Returns JSON:
    {
        "result":     "phishing" | "suspicious" | "safe",
        "confidence": 92.5,          # 0-100 float
        "features": [
            {"name": "Long URL",     "flagged": true},
            {"name": "Has @",        "flagged": false},
            ...
        ]
    }
    """
    # ── Input Validation ──────────────────────────────
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "Missing 'url' field"}), 400

    # ── Inference ─────────────────────────────────────
    try:
        result = predict_url(url)
        return jsonify(result), 200

    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": "Prediction failed", "detail": str(exc)}), 500


# ── Entry Point ───────────────────────────────────────
if __name__ == "__main__":
    print("PhishGuard API running at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
