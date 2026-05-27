import joblib
import tldextract
import whoisdomain
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import warnings

# Ignore annoying warnings from BeautifulSoup or Scikit-Learn
warnings.filterwarnings("ignore")

print("Loading AI Model (rf_model.pkl)...")
try:
    model = joblib.load("rf_model.pkl")
    print("✅ Model loaded successfully!\n")
except FileNotFoundError:
    print(
        "❌ ERROR: 'rf_model.pkl' not found. Make sure it is in the same folder as this script."
    )
    exit()


def extract_live_features(url):
    print(f"🔍 Scanning URL: {url}")

    # --- THE FIX: Clean the URL to match Tranco training data format ---
    clean_url = (
        str(url)
        .lower()
        .replace("https://", "")
        .replace("http://", "")
        # .replace("www.", "")
    )

    # 1-4: Lexical Features (Calculated on the CLEAN URL)
    dots = clean_url.count(".")
    slashes = clean_url.count("/")
    at_symbol = clean_url.count("@")
    length = len(clean_url)

    # 5: Domain Age Feature
    print("   -> Checking WHOIS Domain Age...")
    domain_age = -1
    try:
        extracted = tldextract.extract(str(url))
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

    # 6: HTML Keyword Count Feature
    print("   -> Scraping HTML Content...")
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

    features = [dots, slashes, at_symbol, length, domain_age, keyword_count]
    print(f"   -> Extracted Feature Vector: {features}")
    return [features]


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    while True:
        target_url = input(
            "\n🌐 Enter a URL to test (or type 'exit' to quit): "
        ).strip()

        if target_url.lower() == "exit":
            print("Exiting scanner...")
            break

        if not target_url.startswith("http"):
            target_url = "http://" + target_url

        # Extract features
        features_2d = extract_live_features(target_url)

        # Ask the AI
        prediction = model.predict(features_2d)[0]
        confidence = model.predict_proba(features_2d)[0].max() * 100

        # Print Results
        print("\n" + "=" * 40)
        if prediction == True or prediction == 1:
            print("🚨 VERDICT: PHISHING / MALICIOUS")
        else:
            print("✅ VERDICT: SAFE / LEGITIMATE")

        print(f"📊 CONFIDENCE: {confidence:.2f}%")
        print("=" * 40 + "\n")
