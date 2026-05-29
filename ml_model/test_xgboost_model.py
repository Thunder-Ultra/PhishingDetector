import joblib
import tldextract
import whoisdomain
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import math
from collections import Counter
import re
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

print("Loading XGBoost Model...")
try:
    model = joblib.load("xgboost_model.pkl")
    print("✅ Model loaded successfully!\n")
except FileNotFoundError:
    print("❌ ERROR: 'xgboost_model.pkl' not found.")
    exit()


def calculate_entropy(text):
    if not text:
        return 0
    p, lns = Counter(text), float(len(text))
    return -sum(count / lns * math.log2(count / lns) for count in p.values())


def extract_live_features(url):
    print(f"🔍 Scanning URL: {url}")

    # Clean URL
    clean_url = (
        str(url)
        .lower()
        .replace("https://", "")
        .replace("http://", "")
        .replace("www.", "")
    )

    # Lexical Features
    length = len(clean_url)
    dots = clean_url.count(".")
    slashes = clean_url.count("/")
    at_symbol = clean_url.count("@")
    entropy = calculate_entropy(clean_url)

    extracted = tldextract.extract(str(url))
    subdomain_depth = len(extracted.subdomain.split(".")) if extracted.subdomain else 0
    has_hyphen = 1 if "-" in extracted.domain else 0
    is_ip = 1 if re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", str(url)) else 0

    # Domain Age
    print("   -> Checking WHOIS...")
    domain_age = -1
    try:
        root_domain = f"{extracted.domain}.{extracted.suffix}"
        if root_domain and root_domain != ".":
            w = whoisdomain.query(root_domain)
            if w and w.creation_date:
                c_date = (
                    w.creation_date[0]
                    if type(w.creation_date) is list
                    else w.creation_date
                )
                age = (datetime.now() - c_date).days
                domain_age = age if age >= 0 else -1
    except Exception:
        domain_age = -1

    # HTML Keywords
    print("   -> Scraping HTML...")
    keyword_count = -1
    keywords = [
        "login",
        "password",
        "verify",
        "bank",
        "secure",
        "account",
        "update",
        "suspended",
    ]
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=3)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            page_text = soup.get_text().lower()
            keyword_count = sum(page_text.count(word) for word in keywords)
    except Exception:
        keyword_count = -1

    # Create a DataFrame with the EXACT column names from training
    feature_dict = {
        "length": [length],
        "dots": [dots],
        "slashes": [slashes],
        "at_symbol": [at_symbol],
        "entropy": [entropy],
        "subdomain_depth": [subdomain_depth],
        "has_hyphen": [has_hyphen],
        "is_ip": [is_ip],
        "domain_age": [domain_age],
        "keyword_count": [keyword_count],
    }

    df_features = pd.DataFrame(feature_dict)
    print(f"   -> Extracted Features:\n{df_features.to_string(index=False)}")
    return df_features


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    while True:
        target_url = input("\n🌐 Enter a URL to test (or type 'exit'): ").strip()
        if target_url.lower() == "exit":
            break
        if not target_url.startswith("http"):
            target_url = "http://" + target_url

        df_features = extract_live_features(target_url)

        # Ask XGBoost
        prediction = model.predict(df_features)[0]
        confidence = model.predict_proba(df_features)[0].max() * 100

        print("\n" + "=" * 40)
        if prediction == 1 or prediction == True:
            print("🚨 VERDICT: PHISHING / MALICIOUS")
        else:
            print("✅ VERDICT: SAFE / LEGITIMATE")

        print(f"📊 CONFIDENCE: {confidence:.2f}%")
        print("=" * 40 + "\n")
