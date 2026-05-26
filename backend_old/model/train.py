"""
train.py — PhishGuard Random Forest Trainer
============================================
Trains a Random Forest classifier on lexical URL features.
Saves the model to model/rf_model.pkl for use by the prediction API.

Usage:
    python train.py                     # train on built-in synthetic dataset
    python train.py --data urls.csv     # train on your own CSV (url, label columns)

Dataset format (CSV):
    url,label
    https://google.com,safe
    http://paypa1-secure.xyz/login,phishing
    ...
"""

import argparse
import os
import pickle
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

from features import extract_features, FEATURE_NAMES


# ── Constants ────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), "rf_model.pkl")
RANDOM_STATE = 42


# ── Synthetic Dataset (fallback for demo/testing) ────────────────────────
def _build_synthetic_dataset() -> pd.DataFrame:
    """
    Creates a small synthetic dataset for demonstration.
    In production, replace with a real labeled dataset such as:
      - PhishTank (https://www.phishtank.com/developer_info.php)
      - UCI Phishing Websites dataset
      - ISCX-URL-2016
    """
    safe_urls = [
        "https://www.google.com",
        "https://github.com/openai/openai-python",
        "https://stackoverflow.com/questions/tagged/python",
        "https://www.amazon.com/dp/B09V3KXJPB",
        "https://en.wikipedia.org/wiki/Machine_learning",
        "https://www.bbc.com/news/technology",
        "https://docs.python.org/3/library/urllib.html",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://news.ycombinator.com",
        "https://www.reddit.com/r/MachineLearning",
        "https://flask.palletsprojects.com/en/3.0.x/",
        "https://scikit-learn.org/stable/modules/ensemble.html",
        "https://www.nytimes.com/section/technology",
        "https://medium.com/towards-data-science",
        "https://arxiv.org/abs/2303.08774",
    ]

    suspicious_urls = [
        "http://google-secure-login.com/verify",
        "https://amazon-order-confirm.net/account/login",
        "http://apple-id-verify.info/signin",
        "https://paypal-security-update.com/login?token=abc",
        "http://microsoft-support-1234.online/fix",
    ]

    phishing_urls = [
        "http://192.168.1.1/login/paypal/secure",
        "http://paypa1.com@evil.ru/login",
        "http://www.secure-login-verify.xyz/account/update?user=victim",
        "http://amazon-account-suspended.tk/recover%20account/login",
        "http://apple-id-locked-secure-verify.ml/apple/id/signin",
        "http://bankofamerica-secureverify.club/online/banking/login",
        "https://netflix-billing-suspended.online/account/billing/update",
        "http://facebook.com.secure-login.xyz/checkpoint",
        "http://verify-account-suspended.pw/paypal/login?ref=secure",
        "http://login-secure-update.ga/boa/account?token=a1b2c3d4e5",
        "http://support-microsoft.top/windows/validate?session=xyz",
        "http://www.google.com.phishing-example.com/login",
        "http://192.0.2.1/~secure/banking/login.php",
        "http://bit.ly/2xABCDE",
        "http://tinyurl.com/phish1234",
    ]

    rows = (
        [(u, "safe")       for u in safe_urls] +
        [(u, "suspicious") for u in suspicious_urls] +
        [(u, "phishing")   for u in phishing_urls]
    )

    df = pd.DataFrame(rows, columns=["url", "label"])
    print(f"[synthetic dataset] {len(df)} samples  "
          f"({df.label.value_counts().to_dict()})")
    return df


# ── Feature Extraction ────────────────────────────────────────────────────
def build_feature_matrix(urls: pd.Series) -> np.ndarray:
    print(f"Extracting features from {len(urls)} URLs…")
    vectors = []
    for url in urls:
        feat = extract_features(url)
        vectors.append(feat["vector"])
    return np.array(vectors, dtype=float)


# ── Training ──────────────────────────────────────────────────────────────
def train(data_path: str | None = None):
    # 1. Load data
    if data_path and os.path.exists(data_path):
        df = pd.read_csv(data_path)
        assert "url" in df.columns and "label" in df.columns, \
            "CSV must have 'url' and 'label' columns"
        print(f"Loaded {len(df)} rows from {data_path}")
    else:
        print("No dataset provided — using synthetic demo data.")
        df = _build_synthetic_dataset()

    # 2. Encode labels
    le = LabelEncoder()
    y  = le.fit_transform(df["label"])
    print(f"Classes: {list(le.classes_)}")   # e.g. ['phishing', 'safe', 'suspicious']

    # 3. Build features
    X = build_feature_matrix(df["url"])

    # 4. Train / test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    # 5. Train Random Forest
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features="sqrt",
        class_weight="balanced",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )
    clf.fit(X_train, y_train)

    # 6. Evaluate
    y_pred = clf.predict(X_test)
    print("\n── Classification Report ────────────────────────")
    print(classification_report(y_test, y_pred, target_names=le.classes_))
    print("── Confusion Matrix ─────────────────────────────")
    print(confusion_matrix(y_test, y_pred))

    # Cross-validation
    if len(df) >= 10:
        cv_scores = cross_val_score(clf, X, y, cv=min(5, len(df)//3), scoring="f1_macro")
        print(f"\nCross-val F1 (macro): {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    # 7. Feature importance
    importances = sorted(
        zip(FEATURE_NAMES, clf.feature_importances_),
        key=lambda x: x[1], reverse=True
    )
    print("\n── Top Feature Importances ──────────────────────")
    for name, imp in importances[:10]:
        bar = "█" * int(imp * 40)
        print(f"  {name:<25} {bar} {imp:.4f}")

    # 8. Save model + label encoder
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"model": clf, "label_encoder": le}, f)
    print(f"\n✓ Model saved → {MODEL_PATH}")

    return clf, le


# ── CLI ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train PhishGuard Random Forest")
    parser.add_argument("--data", type=str, default=None,
                        help="Path to CSV dataset (url, label columns)")
    args = parser.parse_args()
    train(data_path=args.data)
