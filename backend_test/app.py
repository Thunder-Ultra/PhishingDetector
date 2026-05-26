from flask import Flask, request, jsonify
from flask_cors import CORS
import urllib.parse
import joblib
import os

# Import your feature extraction logic
import features 

app = Flask(__name__)
# Enable CORS for all origins as required by the extension
CORS(app, resources={r"/*": {"origins": "*"}})

# --- FOOLPROOF MODEL LOADING ---

# 1. Get the exact folder path where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Combine it with the model name
MODEL_PATH = os.path.join(BASE_DIR, 'rf_model.pkl')

print(f"Looking for model at: {MODEL_PATH}")

try:
    # 3. Load the model
    model = joblib.load(MODEL_PATH)
    print("✅ Model loaded successfully!")
except FileNotFoundError:
    print("❌ ERROR: Could not find rf_model.pkl!")
    print("Please make sure rf_model.pkl is inside the 'backend' folder.")
    exit() # Stops the server from running broken

# --- ROUTES ---

@app.route('/', methods=['GET'])
def health_check():
    """Health check route as defined in the API contract."""
    return jsonify({
        "status": "ok",
        "service": "PhishGuard Backend",
        "checks": ["dots", "slashes", "url_length", "domain_age", "html_keywords"],
        "keywords": ["login", "password", "verify", "account"],
        "note": "Query string (after ?) is ignored."
    }), 200

@app.route('/predict', methods=['POST'])
def predict():
    """Main prediction route called by the extension."""
    data = request.get_json(silent=True) or {}
    raw_url = data.get('url')

    if not raw_url:
        return jsonify({"error": "Missing 'url' field"}), 400

    # CRITICAL CONSTRAINT: Strip everything after ? and #
    parsed = urllib.parse.urlparse(raw_url)
    base_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

    try:
        # 1. Extract features
        # Your features.py should return the raw array for the model AND the formatted UI list
        ml_vector, ui_features = features.extract_features(base_url)

        # 2. Make prediction
        # predict_proba returns probabilities like [[prob_safe, prob_phishing]]
        probabilities = model.predict_proba([ml_vector])[0] 
        phish_prob = probabilities[1] * 100  # Assuming class 1 is phishing
        
        confidence = round(float(max(probabilities) * 100), 1)

        # 3. Determine result thresholds
        if phish_prob >= 75.0:
            result = "phishing"
        elif phish_prob >= 40.0:
            result = "suspicious"
        else:
            result = "safe"

        # 4. Return exact JSON shape required by the extension
        return jsonify({
            "result": result,
            "confidence": confidence,
            "features": ui_features
        }), 200

    except Exception as e:
        print(f"❌ Error processing {base_url}: {e}")
        # Any non-2xx response fails open, letting the user through
        return jsonify({"error": "Internal backend error"}), 500

if __name__ == '__main__':
    # Run on port 5000 as specified in the docs
    app.run(port=5000, debug=True)
