import urllib.parse
import whois
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import math
from collections import Counter
import ipaddress


def calculate_entropy(text):
    """Calculates Shannon Entropy (randomness) of a string."""
    if not text:
        return 0
    entropy = 0
    for x in Counter(text).values():
        p_x = float(x) / len(text)
        entropy += -p_x * math.log2(p_x)
    return round(entropy, 3)


def extract_live_features(url):
    """
    Extracts the 10 V2 features for the XGBoost model and generates a UI reason.
    """
    parsed_url = urllib.parse.urlparse(url)
    domain = parsed_url.netloc
    path = parsed_url.path

    # --- 1. length ---
    length = len(url)

    # --- 2. dots ---
    dots = domain.count(".")

    # --- 3. slashes ---
    slashes = max(0, path.count("/") - 1)

    # --- 4. at_symbol ---
    at_symbol = url.count("@")

    # --- 5. entropy ---
    entropy = calculate_entropy(url)

    # --- 6. subdomain_depth ---
    clean_domain = domain.replace("www.", "")
    subdomain_depth = max(0, clean_domain.count(".") - 1)

    # --- 7. has_hyphen ---
    has_hyphen = 1 if "-" in domain else 0

    # --- 8. is_ip ---
    is_ip = 0
    try:
        # Strip port numbers if present (e.g., 192.168.1.1:8080)
        ip_str = domain.split(":")[0]
        ipaddress.ip_address(ip_str)
        is_ip = 1
    except ValueError:
        pass

    # --- 9. domain_age ---
    domain_age = -1
    try:
        w = whois.whois(domain)
        creation_date = w.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        if creation_date:
            domain_age = (datetime.now() - creation_date).days
    except Exception:
        pass  # Hidden or dead

    # --- 10. keyword_count ---
    keywords = ["login", "password", "verify", "account", "update", "secure"]
    keyword_count = -1  # Default to -1 (dead) as requested
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            keyword_count = 0  # Site is alive, reset to 0
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text().lower()
            for kw in keywords:
                keyword_count += text.count(kw)
    except Exception:
        pass

    # --- BUILD THE ML VECTOR (Strict Order!) ---
    ml_vector = [
        length,
        dots,
        slashes,
        at_symbol,
        entropy,
        subdomain_depth,
        has_hyphen,
        is_ip,
        domain_age,
        keyword_count,
    ]

    # --- GENERATE EXPLAINABLE AI REASON ---
    reasons = []
    if entropy > 4.5:
        reasons.append("High URL entropy (randomness)")
    if domain_age == -1:
        reasons.append("Domain Age is -1 (Hidden/Dead)")
    elif domain_age < 30:
        reasons.append(f"Domain is very new ({domain_age} days)")
    if is_ip == 1:
        reasons.append("URL uses a raw IP address instead of a domain name")
    if keyword_count > 0:
        reasons.append("Suspicious login keywords found on page")
    if at_symbol > 0:
        reasons.append("Contains '@' symbol to hide true destination")

    if reasons:
        reason_str = " and ".join(reasons) + "."
        # Capitalize first letter
        reason_str = reason_str[0].upper() + reason_str[1:]
    else:
        reason_str = "This site appears to be legitimate based on current metrics."

    return ml_vector, reason_str
