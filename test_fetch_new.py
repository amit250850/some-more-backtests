import requests
import zipfile
import io
import pandas as pd
from datetime import datetime
import time

def fetch_bhavcopy_new(date_str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    session = requests.Session()
    session.headers.update(headers)

    dt = datetime.strptime(date_str, '%Y-%m-%d')
    date_fmt = dt.strftime('%Y%m%d')
    # Let's try regular nseindia.com
    url = f"https://nsearchives.nseindia.com/content/historical/DERIVATIVES/2024/AUG/BhavCopy_NSE_FO_0_0_0_{date_fmt}_F_0000.csv.zip"
    print(f"Trying {url}")
    try:
        response = session.get(url, timeout=10)
        print(response.status_code)
    except Exception as e:
        print(f"Exception: {e}")

fetch_bhavcopy_new('2024-08-01')
