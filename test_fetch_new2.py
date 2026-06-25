import requests

urls = [
    "https://nsearchives.nseindia.com/content/historical/DERIVATIVES/2024/AUG/BhavCopy_NSE_FO_0_0_0_20240801_F_0000.csv.zip",
    "https://nsearchives.nseindia.com/content/historical/DERIVATIVES/2024/AUG/fo01AUG2024bhav.csv.zip",
    "https://archives.nseindia.com/content/historical/DERIVATIVES/2024/AUG/fo01AUG2024bhav.csv.zip",
    "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_FO_0_0_0_20240801_F_0000.csv.zip",
    "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20240801_F_0000.csv.zip"
]

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0'
})

for url in urls:
    try:
        r = session.head(url, timeout=5)
        print(f"{r.status_code} for {url}")
    except Exception as e:
        print(e)
