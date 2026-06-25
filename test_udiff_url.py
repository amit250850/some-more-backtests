import requests

urls = [
    "https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_20240801_F_0000.csv.zip",
    "https://nsearchives.nseindia.com/content/historical/DERIVATIVES/2024/AUG/BhavCopy_NSE_FO_0_0_0_20240801_F_0000.csv.zip",
    "https://nsearchives.nseindia.com/content/historical/DERIVATIVES/2024/AUG/fo01AUG2024bhav.csv.zip"
]

for url in urls:
    r = requests.head(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
    print(f"{r.status_code} for {url}")
