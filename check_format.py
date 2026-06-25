import requests
import zipfile
import io
import pandas as pd

def check_url(url):
    print(f"Fetching {url}")
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
    if r.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            filename = z.namelist()[0]
            with z.open(filename) as f:
                df = pd.read_csv(f)
                print(f"Columns: {df.columns.tolist()[:10]}...")
                print(df.head(2))
    else:
        print(f"Status {r.status_code}")

check_url("https://nsearchives.nseindia.com/content/historical/DERIVATIVES/2024/AUG/BhavCopy_NSE_FO_0_0_0_20240801_F_0000.csv.zip")
check_url("https://nsearchives.nseindia.com/content/historical/DERIVATIVES/2023/JAN/fo02JAN2023bhav.csv.zip")
