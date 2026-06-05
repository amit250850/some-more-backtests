import pandas as pd
from datetime import datetime, timedelta
from kite_auth import get_kite_session
from data_fetcher import DataFetcher
import os

kite = get_kite_session()
fetcher = DataFetcher(kite)

token, symbol = fetcher.get_nearest_future("MCX", "SILVERMIC")

# Kite allows 60 days for 15-minute intervals.
start = datetime.now() - timedelta(days=60)
df = fetcher.fetch_historical_data(token, "SILVERMIC", "15minute", start, continuous=False)

if not df.empty:
    df.to_csv("data/SILVERMIC_15minute.csv", index=False)
    print(f"Saved {len(df)} 15-minute candles to data/SILVERMIC_15minute.csv")
else:
    print("Failed to fetch.")
