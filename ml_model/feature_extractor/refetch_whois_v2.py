import pandas as pd
import whoisdomain
import tldextract
import time
from datetime import datetime
from tqdm import tqdm

tqdm.pandas(desc="Refetching WHOIS")

print("1. Loading massive_dataset.csv...")
df = pd.read_csv("phishing_datasets/final/massive_dataset.csv")

# 2. Find missing domain ages
missing_mask = df["domain_age"] == -1
urls_to_fix = df[missing_mask]

print(f"2. Found {len(urls_to_fix)} URLs with missing Domain Age.")
print("   Starting the slow, sequential Retry Pipeline...")


def refetch_age(url):
    try:
        extracted = tldextract.extract(str(url))
        root_domain = f"{extracted.domain}.{extracted.suffix}"

        if not root_domain or root_domain == ".":
            return -1

        w = whoisdomain.query(root_domain)

        if w and w.creation_date:
            c_date = (
                w.creation_date[0] if type(w.creation_date) is list else w.creation_date
            )
            age = (datetime.now() - c_date).days

            # SUCCESS! Sleep for 1 second to avoid bans
            time.sleep(1)
            return age if age >= 0 else -1

        time.sleep(0.5)
        return -1
    except Exception:
        time.sleep(0.5)
        return -1


# 3. Apply the refetch function ONLY to the missing rows
if len(urls_to_fix) > 0:
    new_ages = urls_to_fix["url"].progress_apply(refetch_age)

    # Update the dataframe
    df.loc[missing_mask, "domain_age"] = new_ages

    recovered_count = (new_ages != -1).sum()
    print(
        f"\n✅ Recovery Complete! Successfully recovered {recovered_count} domain ages."
    )

# 4. Save the refined dataset
print("5. Saving to 'massive_dataset_refined.csv'...")
df.to_csv("phishing_datasets/final/massive_dataset_refined.csv", index=False)
print("Done! You can now use this refined CSV for XGBoost training.")
