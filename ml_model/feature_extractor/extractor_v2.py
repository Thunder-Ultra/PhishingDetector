import pandas as pd
import whoisdomain
import tldextract
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import math
from collections import Counter
import re
import time
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import warnings

# Ignore warnings to keep the terminal clean
warnings.filterwarnings("ignore")

# ==========================================
# 1. FEATURE EXTRACTION FUNCTIONS
# ==========================================


def calculate_entropy(text):
    """Calculates Shannon Entropy (randomness) of a string."""
    if not text:
        return 0
    p, lns = Counter(text), float(len(text))
    return -sum(count / lns * math.log2(count / lns) for count in p.values())


def get_subdomain_depth(url):
    """Counts how many subdomains exist (e.g., a.b.c.com = 2)"""
    extracted = tldextract.extract(str(url))
    subdomain = extracted.subdomain
    if not subdomain:
        return 0
    return len(subdomain.split("."))


def has_hyphen_in_domain(url):
    """Checks if the root domain contains a hyphen"""
    extracted = tldextract.extract(str(url))
    return 1 if "-" in extracted.domain else 0


def has_ip_address(url):
    """Checks if the URL is an IP address instead of a domain name"""
    match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", str(url))
    return 1 if match else 0


def get_domain_age(url):
    """Fetches WHOIS domain age. Returns -1 if dead, hidden, or timed out."""
    try:
        extracted = tldextract.extract(str(url))
        root_domain = f"{extracted.domain}.{extracted.suffix}"

        if not root_domain or root_domain == ".":
            return -1

        w = whoisdomain.query(root_domain)
        if w is None or w.creation_date is None:
            return -1

        c_date = (
            w.creation_date[0] if type(w.creation_date) is list else w.creation_date
        )
        age = (datetime.now() - c_date).days
        return age if age >= 0 else -1
    except Exception:
        return -1


def get_keyword_count(url):
    """Scrapes HTML for phishing keywords. Returns -1 if site is dead."""
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
        # Fake a browser to bypass basic bot protection
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        # 3-second timeout is critical so threads don't hang forever
        response = requests.get(url, headers=headers, timeout=3)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            page_text = soup.get_text().lower()
            return sum(page_text.count(word) for word in keywords)
        return -1
    except Exception:
        return -1


# ==========================================
# 2. THE MASTER PROCESSOR (For Threading)
# ==========================================


def process_single_url(item):
    """Processes a single URL and returns a dictionary of features."""
    url, label = item

    try:
        # Clean URL for lexical checks (removes http://www.)
        clean_url = (
            str(url)
            .lower()
            .replace("https://", "")
            .replace("http://", "")
            .replace("www.", "")
        )

        # Build the feature dictionary
        features = {
            "url": url,
            "length": len(clean_url),
            "dots": clean_url.count("."),
            "slashes": clean_url.count("/"),
            "at_symbol": clean_url.count("@"),
            "entropy": calculate_entropy(clean_url),
            "subdomain_depth": get_subdomain_depth(url),
            "has_hyphen": has_hyphen_in_domain(url),
            "is_ip": has_ip_address(url),
            "domain_age": get_domain_age(url),
            "keyword_count": get_keyword_count(url),
            "phishing": label,  # 1 for Phishing, 0 for Safe
        }
        return features
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None


# ==========================================
# 3. MAIN EXECUTION
# ==========================================

if __name__ == "__main__":
    print("1. Loading Datasets...")
    df_phishtank = pd.read_csv("phishing_datasets/original/phishtank.csv")
    df_tranco = pd.read_csv(
        "phishing_datasets/original/tranco_top_1M.csv", names=["Sl", "url"]
    )

    # Ensure Tranco URLs have http:// so requests.get() works
    df_tranco["url"] = df_tranco["url"].apply(
        lambda x: x if str(x).startswith("http") else "http://" + str(x)
    )

    TOTAL_SAMPLES = 50_000  # 25k Phishing, 25k Safe

    print(f"2. Randomly sampling {TOTAL_SAMPLES} URLs...")
    phish_urls = (
        df_phishtank["url"].sample(n=TOTAL_SAMPLES // 2, random_state=42).tolist()
    )
    safe_urls = df_tranco["url"].sample(n=TOTAL_SAMPLES // 2, random_state=42).tolist()

    # Create a list of tuples: (url, label) -> 1 is Phishing, 0 is Safe
    tasks = [(url, 1) for url in phish_urls] + [(url, 0) for url in safe_urls]

    print("3. Starting Multi-Threaded Feature Extraction...")
    print("   (This will take a while. Go grab a coffee!)")

    results = []
    # max_workers=20 means 20 URLs are processed at the exact same time!
    with ThreadPoolExecutor(max_workers=20) as executor:
        # tqdm creates the progress bar
        for res in tqdm(executor.map(process_single_url, tasks), total=len(tasks)):
            if res is not None:
                results.append(res)

    print("\n4. Saving to CSV...")
    df_final = pd.DataFrame(results)
    df_final.to_csv("phishing_datasets/final/massive_dataset.csv", index=False)

    print(f"✅ DONE! Successfully extracted features for {len(df_final)} URLs.")
    print("Saved as 'massive_dataset.csv'. Ready for XGBoost Training!")
