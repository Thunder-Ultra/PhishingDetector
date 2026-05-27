from flask import Flask, request, jsonify
from flask_cors import CORS
import urllib.parse
import joblib
import os
import json
import warnings

# Import your feature extraction logic
import features

# Hide the scikit-learn feature names warning
warnings.filterwarnings("ignore", message="X does not have valid feature names")

app = Flask(__name__)
# Enable CORS for all origins as required by the extension
CORS(app, resources={r"/*": {"origins": "*"}})

# --- FOOLPROOF MODEL LOADING ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "rf_model.pkl")

print(f"Looking for model at: {MODEL_PATH}")

try:
    model = joblib.load(MODEL_PATH)
    print("✅ Model loaded successfully!")
except FileNotFoundError:
    print("❌ ERROR: Could not find rf_model.pkl!")
    print("Please make sure rf_model.pkl is inside the 'backend' folder.")
    exit()


# --- ROUTES ---
@app.route("/", methods=["GET"])
def health_check():
    return (
        jsonify(
            {
                "status": "ok",
                "service": "PhishGuard Backend",
                "checks": [
                    "dots",
                    "slashes",
                    "url_length",
                    "domain_age",
                    "html_keywords",
                ],
                "keywords": ["login", "password", "verify", "account"],
                "note": "Query string (after ?) is ignored.",
            }
        ),
        200,
    )


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True) or {}
    raw_url = data.get("url")

    if not raw_url:
        return jsonify({"error": "Missing 'url' field"}), 400

    # Strip everything after ? and #
    parsed = urllib.parse.urlparse(raw_url)
    base_url = urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, "", "", "")
    )

    try:
        # 1. Extract features
        ml_vector, ui_features = features.extract_features(base_url)

        # --- NEW: PRINT FEATURES BEFORE FEEDING TO AI ---
        print(f"\n[DEBUG] Features extracted for: {base_url}")
        feature_names = [
            "Dots",
            "Forward Slash",
            "@",
            "Length",
            "Domain Age",
            "Keyword Count",
        ]
        for name, value in zip(feature_names, ml_vector):
            print(f"   ➤ {name}: {value}")
        print(f"   ➤ Raw ML Vector: {ml_vector}\n")
        # ------------------------------------------------

        # 2. Make prediction
        probabilities = model.predict_proba([ml_vector])[0]
        phish_prob = probabilities[1] * 100

        confidence = round(float(max(probabilities) * 100), 1)

        # 3. Determine result thresholds
        if phish_prob >= 75.0:
            result = "phishing"
        elif phish_prob >= 40.0:
            result = "suspicious"
        else:
            result = "safe"

        # 4. PREPARE THE RESPONSE DATA
        response_data = {
            "result": result,
            "confidence": confidence,
            "features": ui_features,
        }

        # 5. PRINT FINAL RESPONSE TO TERMINAL
        print(f"--- RESPONSE FOR: {base_url} ---")
        print(json.dumps(response_data, indent=2))
        print("--------------------------------------------------\n")

        # 6. SEND TO BROWSER
        return jsonify(response_data), 200

    except Exception as e:
        print(f"❌ Error processing {base_url}: {e}")
        return jsonify({"error": "Internal backend error"}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)
