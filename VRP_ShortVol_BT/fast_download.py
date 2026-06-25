import pandas as pd
from datetime import datetime
import concurrent.futures
from data_fetch import fetch_bhavcopy
import os

start_date = pd.to_datetime('2019-01-01')
end_date = pd.to_datetime('2024-09-01')
date_range = pd.date_range(start=start_date, end=end_date, freq='B')

# Filter out dates that are already cached
dates_to_fetch = []
for d in date_range:
    date_str = d.strftime("%Y-%m-%d")
    cache_path = f"/app/VRP_ShortVol_BT/data/bhavcopy_{date_str}.parquet"
    if not os.path.exists(cache_path):
        dates_to_fetch.append(d)

print(f"Need to fetch {len(dates_to_fetch)} dates.")

def fetch(d):
    fetch_bhavcopy(d)

# Use 10 threads
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    executor.map(fetch, dates_to_fetch)

print("Done fast downloading.")
