def extract_features(url):
    """
    Takes a base URL and extracts features for both the ML model and the UI.
    """
    
    # --- 1. Calculate your features here ---
    # (These are dummy calculations for the template)
    dots_count = url.count('.')
    url_length = len(url)
    has_https = url.startswith("https")
    
    # --- 2. Build the UI Feature Array ---
    # This must match the exact shape required by the extension popup
    ui_features = [
        {
            "name": f"Dots in domain: {dots_count}",
            "flagged": dots_count > 3
        },
        {
            "name": f"URL length: {url_length} chars",
            "flagged": url_length > 75
        },
        {
            "name": "No HTTPS",
            "flagged": not has_https
        }
    ]
    
    # --- 3. Build the ML Vector ---
    # This is the raw numeric array your sklearn model expects (e.g., [4, 112, 0])
    # Make sure the order matches exactly how the model was trained!
    ml_vector = [dots_count, url_length, int(has_https)]
    
    return ml_vector, ui_features
