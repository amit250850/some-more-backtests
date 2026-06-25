import requests
import zipfile
import io
import pandas as pd
from datetime import datetime
import time

def fetch_bhavcopy(date_str, format_type='legacy'):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br'
    }

    session = requests.Session()
    session.headers.update(headers)

    dt = datetime.strptime(date_str, '%Y-%m-%d')
    year = dt.strftime('%Y')
    month = dt.strftime('%b').upper()
    day = dt.strftime('%d')

    if format_type == 'legacy':
        url = f"https://archives.nseindia.com/content/historical/DERIVATIVES/{year}/{month}/fo{day}{month}{year}bhav.csv.zip"
    else:
        # e.g., BhavCopy_NSE_FO_0_0_0_20240801_F_0000.csv.zip
        date_fmt = dt.strftime('%Y%m%d')
        url = f"https://nsearchives.nseindia.com/content/historical/DERIVATIVES/{year}/{month}/BhavCopy_NSE_FO_0_0_0_{date_fmt}_F_0000.csv.zip"

    print(f"Fetching {url}...")
    # First, get the main page to get cookies
    try:
        session.get('https://www.nseindia.com', timeout=10)
        time.sleep(1)
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                filename = z.namelist()[0]
                with z.open(filename) as f:
                    df = pd.read_csv(f)
                    print(f"Success! Columns: {df.columns.tolist()[:10]}...")
                    return df
        else:
            print(f"Failed with status code {response.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

df_old = fetch_bhavcopy('2023-01-02', 'legacy')
df_new = fetch_bhavcopy('2024-08-01', 'udiff')
