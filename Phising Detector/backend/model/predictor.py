"""
predictor.py — PhishGuard Prediction Wrapper
=============================================
Loads the trained Random Forest model and exposes predict_url().
Uses predict_proba() to generate confidence scores.
"""

import os
import pickle
import numpy as np

from .features import extract_features

# ── Paths ─────────────────────────────────────────────
_DIR        = os.path.dirname(__file__)
_MODEL_PATH = os.path.join(_DIR, "rf_model.pkl")

# ── Lazy-load cache ───────────────────────────────────
_model         = None
_label_encoder = None


def _load_model():
    global _model, _label_encoder
    if _model is None:
        if not os.path.exists(_MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at {_MODEL_PATH}. "
                "Run 'python model/train.py' first."
            )
        with open(_MODEL_PATH, "rb") as f:
            bundle = pickle.load(f)
        _model         = bundle["model"]
        _label_encoder = bundle["label_encoder"]


# ── Public API ────────────────────────────────────────

def predict_url(url: str) -> dict:
    """
    Analyse a URL and return a prediction dict.

    Returns:
        {
            "result":     "phishing" | "suspicious" | "safe",
            "confidence": 92.5,          # 0-100 float (probability of predicted class)
            "features": [
                {"name": "Long URL",   "flagged": True},
                ...
            ]
        }
    """
    _load_model()

    # Extract features
    feat_result = extract_features(url)
    X = np.array([feat_result["vector"]], dtype=float)

    # Predict class + probability
    class_idx   = _model.predict(X)[0]                # integer class index
    proba       = _model.predict_proba(X)[0]          # probability per class
    confidence  = float(proba[class_idx]) * 100       # convert to 0-100

    # Decode label
    label = _label_encoder.inverse_transform([class_idx])[0]  # 'phishing'/'suspicious'/'safe'

    return {
        "result":     label,
        "confidence": round(confidence, 2),
        "features":   feat_result["metadata"],
    }
