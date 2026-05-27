import urllib.parse
import whois
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def extract_features(url):
    """
    Extracts all 6 features expected by the frontend and the ML model.
    """
    parsed_url = urllib.parse.urlparse(url)
    domain = parsed_url.netloc
    path = parsed_url.path

    # --- 1. Dots in domain ---
    dots_count = domain.count('.')
    dots_flagged = dots_count >= 3
    dots_name = f"Dots in domain: {dots_count}" + (" (high)" if dots_flagged else "")

    # --- 2. Path depth (slashes) ---
    # Ignore the first slash which just represents the root
    slashes_count = max(0, path.count('/') - 1) 
    slashes_flagged = slashes_count >= 4
    slashes_name = f"Path depth: {slashes_count} slashes" + (" (deep)" if slashes_flagged else "")

    # --- 3. URL length ---
    url_length = len(url)
    length_flagged = url_length > 75
    length_name = f"URL length: {url_length} chars" + (" (long)" if length_flagged else "")

    # --- 4. HTTPS Check ---
    has_https = parsed_url.scheme == 'https'
    https_flagged = not has_https
    https_name = "No HTTPS" if https_flagged else "HTTPS secure"

    # --- 5. Domain Age (WHOIS) ---
    domain_age_days = -1
    try:
        # WHOIS lookups can hang, so we catch exceptions
        w = whois.whois(domain)
        creation_date = w.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0] # Sometimes returns a list of dates
        
        if creation_date:
            domain_age_days = (datetime.now() - creation_date).days
    except Exception as e:
        print(f"WHOIS lookup failed for {domain}: {e}")

    if domain_age_days == -1:
        age_name = "Domain age: Unknown (hidden)"
        age_flagged = True
    else:
        age_flagged = domain_age_days < 30
        age_name = f"Domain age: {domain_age_days} days" + (" (new)" if age_flagged else "")

    # --- 6. HTML Keywords ---
    keywords = ["login", "password", "verify", "account"]
    keyword_count = 0
    try:
        # CRITICAL: 3-second timeout! 
        # The extension aborts after 8s total, so we can't wait forever for a slow site.
        response = requests.get(url, timeout=3)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text().lower()
        
        for kw in keywords:
            keyword_count += text.count(kw)
    except Exception as e:
        print(f"HTML fetch failed for {url}: {e}")

    kw_flagged = keyword_count > 0
    if kw_flagged:
        kw_name = f"Keywords found x{keyword_count}"
    else:
        kw_name = "No suspicious keywords"


    # --- BUILD THE UI ARRAY ---
    # This matches the exact JSON shape from your image
    ui_features = [
        {"name": dots_name, "flagged": dots_flagged},
        {"name": slashes_name, "flagged": slashes_flagged},
        {"name": length_name, "flagged": length_flagged},
        {"name": age_name, "flagged": age_flagged},
        {"name": kw_name, "flagged": kw_flagged},
        {"name": https_name, "flagged": https_flagged}
    ]

    # --- BUILD THE ML VECTOR ---
    # Your teammate's model MUST be trained on these exact 6 features in this exact order!
    ml_vector = [
        dots_count, 
        slashes_count, 
        url_length, 
        domain_age_days, 
        keyword_count, 
        int(has_https)
    ]

    return ml_vector, ui_features
