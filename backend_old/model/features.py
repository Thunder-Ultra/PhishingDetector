"""
features.py — Lexical feature extraction from URLs
Extracts numerical features used by the Random Forest classifier.
"""

import re
from urllib.parse import urlparse


# ── Feature definitions (name, extraction fn, flag threshold) ─────────────
# Each tuple: (display_name, extractor_fn, flag_if_value_above_or_true)


def extract_features(url: str) -> dict:
    """
    Extract lexical features from a URL string.

    Returns:
        dict with:
          - 'vector':   list[float]  — ordered numeric features for the model
          - 'metadata': list[dict]   — human-readable flags for the UI
    """
    try:
        parsed = urlparse(url)
    except Exception:
        parsed = urlparse("")

    hostname = parsed.hostname or ""
    path     = parsed.path or ""
    query    = parsed.query or ""
    full     = url

    # ── Raw measurements ──────────────────────────────────────────────────
    url_length          = len(full)
    hostname_length     = len(hostname)
    path_length         = len(path)

    num_dots            = full.count(".")
    num_hyphens         = hostname.count("-")
    num_underscores     = full.count("_")
    num_slashes         = full.count("/")
    num_at_signs        = full.count("@")
    num_query_params    = len(query.split("&")) if query else 0
    num_digits_in_host  = sum(c.isdigit() for c in hostname)
    num_subdomains      = max(0, hostname.count(".") - 1)   # rough count

    has_ip_address      = int(bool(re.match(
        r"^(\d{1,3}\.){3}\d{1,3}$", hostname
    )))
    has_https           = int(url.lower().startswith("https://"))
    has_at_sign         = int("@" in full)
    has_double_slash    = int("//" in path)   # // inside path (not protocol)
    has_hex_encoding    = int(bool(re.search(r"%[0-9a-fA-F]{2}", full)))
    has_suspicious_tld  = int(bool(re.search(
        r"\.(xyz|top|club|online|site|pw|tk|ml|ga|cf|gq|cc|icu)$",
        hostname, re.IGNORECASE
    )))
    has_brand_in_sub    = int(bool(re.search(
        r"(paypal|apple|google|amazon|microsoft|netflix|bank|secure|login|update)",
        hostname.lower()
    )))
    url_entropy         = _shannon_entropy(full)

    # ── Feature vector (must match training column order in train.py) ─────
    vector = [
        url_length,
        hostname_length,
        path_length,
        num_dots,
        num_hyphens,
        num_underscores,
        num_slashes,
        num_at_signs,
        num_query_params,
        num_digits_in_host,
        num_subdomains,
        has_ip_address,
        has_https,
        has_at_sign,
        has_double_slash,
        has_hex_encoding,
        has_suspicious_tld,
        has_brand_in_sub,
        url_entropy,
    ]

    # ── Human-readable flags for the popup UI ────────────────────────────
    metadata = [
        {"name": f"Length {url_length}",          "flagged": url_length > 75},
        {"name": f"{num_dots} dots",               "flagged": num_dots > 5},
        {"name": f"{num_subdomains} subdomains",   "flagged": num_subdomains > 2},
        {"name": "IP address",                     "flagged": bool(has_ip_address)},
        {"name": "HTTPS",                          "flagged": not bool(has_https)},
        {"name": "@ symbol",                       "flagged": bool(has_at_sign)},
        {"name": "Hex encoded",                    "flagged": bool(has_hex_encoding)},
        {"name": "Suspicious TLD",                 "flagged": bool(has_suspicious_tld)},
        {"name": "Brand in subdomain",             "flagged": bool(has_brand_in_sub)},
        {"name": f"Entropy {url_entropy:.1f}",     "flagged": url_entropy > 4.5},
    ]

    return {"vector": vector, "metadata": metadata}


def _shannon_entropy(s: str) -> float:
    """Calculate Shannon entropy of a string."""
    import math
    if not s:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    n = len(s)
    return -sum((f / n) * math.log2(f / n) for f in freq.values())


# ── Column names (must match vector order above) ──────────────────────────
FEATURE_NAMES = [
    "url_length",
    "hostname_length",
    "path_length",
    "num_dots",
    "num_hyphens",
    "num_underscores",
    "num_slashes",
    "num_at_signs",
    "num_query_params",
    "num_digits_in_host",
    "num_subdomains",
    "has_ip_address",
    "has_https",
    "has_at_sign",
    "has_double_slash",
    "has_hex_encoding",
    "has_suspicious_tld",
    "has_brand_in_sub",
    "url_entropy",
]
