from flask import Flask, request, jsonify
from flask_cors import CORS
import urllib.parse
import joblib
import os
import json
import warnings

# Import the new V2 extraction logic
import features

warnings.filterwarnings("ignore", message="X does not have valid feature names")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- FOOLPROOF MODEL LOADING (V2: XGBoost) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "xgboost_model.pkl")

print(f"Looking for V2 model at: {MODEL_PATH}")

try:
    model = joblib.load(MODEL_PATH)
    print("✅ XGBoost Model loaded successfully!")
except FileNotFoundError:
    print("❌ ERROR: Could not find xgboost_model.pkl!")
    print("Please make sure xgboost_model.pkl is inside the 'backend' folder.")
    exit()


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True) or {}
    raw_url = data.get("url")

    if not raw_url:
        return jsonify({"error": "Missing 'url' field"}), 400

    parsed = urllib.parse.urlparse(raw_url)
    base_url = urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, "", "", "")
    )

    try:
        # 1. Extract 10 features and the reason string
        ml_vector, reason_str = features.extract_live_features(base_url)

        # --- DEBUG PRINT ---
        print(f"\n[DEBUG] V2 Features extracted for: {base_url}")
        feature_names = [
            "length",
            "dots",
            "slashes",
            "at_symbol",
            "entropy",
            "subdomain_depth",
            "has_hyphen",
            "is_ip",
            "domain_age",
            "keyword_count",
        ]
        for name, value in zip(feature_names, ml_vector):
            print(f"   ➤ {name}: {value}")
        # -------------------

        # 2. Make prediction
        # XGBoost via scikit-learn API uses predict_proba just like RandomForest
        probabilities = model.predict_proba([ml_vector])[0]
        phish_prob = probabilities[1] * 100
        confidence = round(float(max(probabilities) * 100), 1)

        # 3. Determine result (Frontend handles the "suspicious" tier now)
        if phish_prob >= 50.0:
            result = "phishing"
        else:
            result = "safe"

        # 4. PREPARE THE V2 RESPONSE DATA
        response_data = {
            "url": raw_url,
            "result": result,
            "confidence": confidence,
            "reason": reason_str,
        }

        print(f"\n--- V2 RESPONSE ---")
        print(json.dumps(response_data, indent=2))
        print("-------------------\n")

        return jsonify(response_data), 200

    except Exception as e:
        print(f"❌ Error processing {base_url}: {e}")
        return jsonify({"error": "Internal backend error"}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)
