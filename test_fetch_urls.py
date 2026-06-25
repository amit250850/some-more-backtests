import requests
import zipfile
import io
import pandas as pd
from datetime import datetime

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

# legacy
dt = datetime(2023, 1, 2)
year = dt.strftime('%Y')
month = dt.strftime('%b').upper()
day = dt.strftime('%d')
legacy_url1 = f"https://archives.nseindia.com/content/historical/DERIVATIVES/{year}/{month}/fo{day}{month}{year}bhav.csv.zip"
legacy_url2 = f"https://nsearchives.nseindia.com/content/historical/DERIVATIVES/{year}/{month}/fo{day}{month}{year}bhav.csv.zip"

print(f"Legacy 1 ({legacy_url1}): {session.head(legacy_url1).status_code}")
print(f"Legacy 2 ({legacy_url2}): {session.head(legacy_url2).status_code}")

# udiff
dt2 = datetime(2024, 8, 1)
date_fmt = dt2.strftime('%Y%m%d')
udiff_url1 = f"https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{date_fmt}_F_0000.csv.zip"
udiff_url2 = f"https://archives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{date_fmt}_F_0000.csv.zip"
udiff_url3 = f"https://nsearchives.nseindia.com/content/historical/DERIVATIVES/{dt2.strftime('%Y')}/{dt2.strftime('%b').upper()}/BhavCopy_NSE_FO_0_0_0_{date_fmt}_F_0000.csv.zip"

print(f"UDIFF 1 ({udiff_url1}): {session.head(udiff_url1).status_code}")
print(f"UDIFF 2 ({udiff_url2}): {session.head(udiff_url2).status_code}")
print(f"UDIFF 3 ({udiff_url3}): {session.head(udiff_url3).status_code}")
