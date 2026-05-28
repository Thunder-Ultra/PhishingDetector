from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# CORS is required so the Chrome Extension can talk to this local server
CORS(app) 

@app.route('/predict', methods=['POST'])
def predict():
    # 1. Receive the data from the Chrome Extension
    data = request.get_json()
    url = data.get('url', '')

    print(f"Received URL for scanning: {url}")

    # 2. SIMULATE THE AI LOGIC FOR TESTING THE FRONTEND
    
    # TIER 2 TEST: If the URL contains words like "paypal", "login", or "update"
    if any(word in url.lower() for word in ["paypal", "login", "update", "secure"]):
        response = {
            "url": url,
            "result": "phishing",
            "confidence": 98.5,
            "reason": "High URL entropy (randomness) and Domain Age is -1 (Hidden/Dead)."
        }
        
    # TIER 3 TEST: If the URL contains words like "test", "free", or "suspicious"
    elif any(word in url.lower() for word in ["test", "free", "suspicious"]):
        response = {
            "url": url,
            "result": "phishing",
            "confidence": 62.0,
            "reason": "Borderline entropy detected. Contains password fields but domain is known."
        }
        
    # TIER 1 TEST: Any other normal website (e.g., google.com, github.com)
    else:
        response = {
            "url": url,
            "result": "safe",
            "confidence": 15.2, # Low threat confidence
            "reason": "Features indicate a standard, safe website."
        }

    # 3. Send the JSON response back to the extension
    return jsonify(response)

if __name__ == '__main__':
    print("🚀 PhishGuard Mock API is running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)