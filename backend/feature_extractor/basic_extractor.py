import pandas as pd  # For Data Operationss
import whoisdomain  # Extract Domain information from a domain
import tldextract  # Extract the domain name from an url
from datetime import datetime  # dependancy to calculate the domain age
import requests  # Simulate a browser to recieve an html page from a link
from bs4 import BeautifulSoup  # HTML parser
from concurrent.futures import ThreadPoolExecutor  # For Threading
from time import sleep
from tqdm import tqdm  # Progress bar library

tqdm.pandas()

THREADING = False
SAMPLE_SIZE = 4000


# pd.Series().to_di
df_phishtank = pd.read_csv("phishing_datasets/original/phishtank.csv")
df_tranco = pd.read_csv(
    "phishing_datasets/original/tranco_top_1M.csv", names=["Sl", "url"]
)

# df_phishtank["verified"].iloc[0] = "No"

# print(df_phishtank.iloc[0])

# df_phishtank[["verified", "online"]] = df_phishtank[["verified", "online"]].replace(
#     {"yes": "Y"}
# )

# print(df_phishtank.size)

print("Sampling data...")
df_phishtank_temp = pd.DataFrame(
    {
        "url": df_phishtank["url"].sample(n=SAMPLE_SIZE // 2, random_state=42),
        "phishing": [True] * (SAMPLE_SIZE // 2),
    }
)
# print(df_phishtank_temp)
# print(df_phishtank_temp.size)
# exit(1)

df_tranco_temp = pd.DataFrame(
    {
        "url": df_tranco["url"].sample(n=SAMPLE_SIZE // 2, random_state=42),
        "phishing": [False] * (SAMPLE_SIZE // 2),
    }
)

df_combined = pd.concat([df_phishtank_temp, df_tranco_temp], ignore_index=True)
# print(df_combined)
# print(df_combined.size)

# print(df_phishtank_temp)
# print(df_tranco_temp)

# print(df_combined)

# Basic Feature Extraction


def count_in_string(item):
    def count_internal(x):
        return x.count(item)

    # t = (item) lambda (x.count(item))
    return count_internal


# def get_domain_age(domain):
#     clean_domain_name = domain.split("://")[-1]
#     # print(clean_domain_name)
#     # exit()
#     # print(vars(datetime))
#     # exit()
#     try:
#         w = whoisdomain.query(clean_domain_name)
#         domain_age_days = (datetime.now() - w.__dict__["creation_date"]).days
#         return domain_age_days
#     except whoisdomain.exceptions.UnknownTld:
#         return "UnknownTld"
#     except AttributeError:
#         return "AttributeError"
#     except:
#         print(vars())
#         return "Error"


def get_domain_age(url):
    # print(url)
    try:
        # 1. Perfectly extract the ROOT domain (e.g., ignores subdomains and /paths)
        extracted = tldextract.extract(url)
        root_domain = f"{extracted.domain}.{extracted.suffix}"

        if not root_domain or root_domain == ".":
            print("Invalid Domain Format")
            return -1  # Invalid domain format

        # 2. Query WHOIS
        w = whoisdomain.query(root_domain)

        # 3. Handle missing creation dates
        if w is None or w.creation_date is None:
            sleep(0.5)
            print("No Creation Date")
            return -1

        # 4. Handle lists (Sometimes WHOIS returns multiple dates as a list)
        creation_date = w.creation_date
        if type(creation_date) is list:
            creation_date = creation_date[0]  # Just grab the first one

        # 5. Calculate age
        domain_age_days = (datetime.now() - creation_date).days
        # print(domain_age_days)
        if domain_age_days < 0:
            print("Invalid Domain age days")
        return domain_age_days if domain_age_days >= 0 else -1

    except:
        # If the TLD is unknown, or WHOIS connection drops, return -1.
        # -1 becomes our "Suspicious / Hidden" numeric flag for the AI.
        # # print(-1)
        # print("Exception Occured :", e)
        # print(vars(e))
        return -1


def run_in_threads(base_funciton):
    def single_thread(item):
        # sleep(5)
        return (item[0], base_funciton([item[1]]))

    def output_function(column):
        with ThreadPoolExecutor(max_workers=1) as executor:
            results = dict(
                executor.map(
                    single_thread,
                    column.to_dict().items(),
                )
            )
        # print(results)
        return results

    return output_function


def get_keyword_count(url):
    # These are the classic words used in Phishing attacks
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
        # 1. Fake a normal browser (User-Agent) so security systems don't block us immediately
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        # 2. Fetch the webpage. TIMEOUT IS CRITICAL (3 seconds max!)
        # If you don't use timeout=3, 20,000 URLs will take 3 days to finish.
        response = requests.get(url, headers=headers, timeout=3)

        # 3. If the site is dead (404 Not Found, 500 Error), return -1
        if response.status_code != 200:
            return -1

        # 4. Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # 5. Extract all visible text and convert to lowercase
        page_text = soup.get_text().lower()

        # 6. Count how many times our suspicious keywords appear
        total_suspicious_words = sum(page_text.count(word) for word in keywords)

        return total_suspicious_words

    except Exception as e:
        # If the site is completely offline, connection refused, or times out
        return -1


# df_combined = df_combined.sample(10)
# df_combined = df_combined.iloc[:10]


## BASIC Features
print("Extracting Basic Features...")
try:
    df_combined["Dots"] = df_combined["url"].map(count_in_string("."))
except:
    print(df_combined["url"])
    exit(1)
df_combined["Forward Slash"] = df_combined["url"].map(count_in_string("/"))
df_combined["@"] = df_combined["url"].map(count_in_string("@"))
df_combined["Length"] = df_combined["url"].str.len()
# df_combined["Forward Slash"] = df_combined["url"].map(count_in_string("/"))


## ADVANCED FEATURES
print("Extracting Domain Age (This will take time)...")
if THREADING:
    df_combined["Domain Age"] = df_combined["url"].pipe(run_in_threads(get_domain_age))
else:
    df_combined["Domain Age"] = df_combined["url"].progress_map(get_domain_age)

print("Extracting Domain Age DONE")

print("Extracting HTML Keywords (This requires downloading pages)...")
if THREADING:
    df_combined["Keyword Count"] = df_combined["url"].pipe(
        run_in_threads(get_keyword_count)
    )
else:
    df_combined["Keyword Count"] = df_combined["url"].progress_map(get_keyword_count)
print("Extracting HTML Keywords DONE...")

print(df_combined)

df_combined.to_csv("phishing_datasets/final/result.csv", index=False)
print("Data saved successfully to result.csv!")


# print(df_combined.max(numeric_only=True))
# print(df_combined[df_combined["@"] > 1]["url"])
# print(df_combined[["Dots", "Forward Slash"]].max())
