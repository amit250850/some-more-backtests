import requests
import zipfile
import io
import pandas as pd

url = "https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_20240801_F_0000.csv.zip"
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        filename = z.namelist()[0]
        with z.open(filename) as f:
            df = pd.read_csv(f)
            print(f"Columns: {df.columns.tolist()}")

url2 = "https://nsearchives.nseindia.com/content/historical/DERIVATIVES/2023/JAN/fo02JAN2023bhav.csv.zip"
r2 = requests.get(url2, headers={'User-Agent': 'Mozilla/5.0'})
print(f"Status 2: {r2.status_code}")
if r2.status_code == 200:
    with zipfile.ZipFile(io.BytesIO(r2.content)) as z:
        filename = z.namelist()[0]
        with z.open(filename) as f:
            df2 = pd.read_csv(f)
            print(f"Columns 2: {df2.columns.tolist()}")
