import urllib.parse
import whois
import requests
from bs4 import BeautifulSoup
from datetime import datetime


def extract_features(url):
    parsed_url = urllib.parse.urlparse(url)
    domain = parsed_url.netloc
    path = parsed_url.path
    print("PATH USED FOR CHECKING :", path)

    # --- 1. Dots ---
    dots_count = domain.count(".")
    dots_flagged = dots_count >= 3
    dots_name = f"Dots in domain: {dots_count}" + (" (high)" if dots_flagged else "")

    # --- 2. Forward Slash ---
    slashes_count = max(0, path.count("/") - 1)
    slashes_flagged = slashes_count >= 4
    slashes_name = f"Path depth: {slashes_count} slashes" + (
        " (deep)" if slashes_flagged else ""
    )

    # --- 3. '@' Symbol (NEW) ---
    # Phishers use @ to hide the real domain (e.g., https://paypal.com@evil.xyz)
    at_count = url.count("@")
    at_flagged = at_count > 0
    at_name = f"'@' symbols: {at_count}" + (" (suspicious)" if at_flagged else "")

    # --- 4. Length ---
    url_length = len(url)
    length_flagged = url_length > 75
    length_name = f"URL length: {url_length} chars" + (
        " (long)" if length_flagged else ""
    )

    # --- 5. Domain Age ---
    domain_age_days = -1
    try:
        w = whois.whois(domain)
        creation_date = w.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        if creation_date:
            domain_age_days = (datetime.now() - creation_date).days
    except Exception:
        pass  # Silently fail and leave as -1

    if domain_age_days == -1:
        age_name = "Domain age: Unknown (hidden)"
        age_flagged = True
    else:
        age_flagged = domain_age_days < 30
        age_name = f"Domain age: {domain_age_days} days" + (
            " (new)" if age_flagged else ""
        )

    # --- 6. Keyword Count ---
    keywords = ["login", "password", "verify", "account"]
    keyword_count = 0
    try:
        response = requests.get(url, timeout=3)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text().lower()
        for kw in keywords:
            keyword_count += text.count(kw)
    except Exception:
        pass  # Silently fail and leave as 0

    kw_flagged = keyword_count > 0
    kw_name = (
        f"Keywords found x{keyword_count}" if kw_flagged else "No suspicious keywords"
    )

    # --- BUILD THE UI ARRAY ---
    # The frontend will dynamically render these 6 chips
    ui_features = [
        {"name": dots_name, "flagged": dots_flagged},
        {"name": slashes_name, "flagged": slashes_flagged},
        {"name": at_name, "flagged": at_flagged},
        {"name": length_name, "flagged": length_flagged},
        {"name": age_name, "flagged": age_flagged},
        {"name": kw_name, "flagged": kw_flagged},
    ]

    # --- BUILD THE ML VECTOR ---
    # STRICT ORDER: Dots, Forward Slash, @, Length, Domain Age, Keyword Count
    ml_vector = [
        dots_count,
        slashes_count,
        at_count,
        url_length,
        domain_age_days,
        keyword_count,
    ]

    return ml_vector, ui_features
