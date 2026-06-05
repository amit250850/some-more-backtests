import os
import glob
import pandas as pd

search_path = "/app/data/tradingtuitions/NSE_Equity_Futures_iEOD/**/*NIFTY_F1.txt"
files = glob.glob(search_path, recursive=True)

all_dfs = []
for f in files:
    try:
        df = pd.read_csv(f, names=['ticker', 'date_str', 'time_str', 'open', 'high', 'low', 'close', 'volume', 'oi'])

        # Format is usually YYYYMMDD and HH:MM
        # We need to strip the colon if it exists or handle it dynamically
        df['date_str'] = df['date_str'].astype(str)
        df['time_str'] = df['time_str'].astype(str).str.replace(':', '')
        df['time_str'] = df['time_str'].str.zfill(6) # sometimes seconds are missing or it's just HHMM
        # Some are just HHMM, so if length is 4, pad with 00 for seconds
        df['time_str'] = df['time_str'].apply(lambda x: x + '00' if len(x) == 4 else x)

        df['date'] = pd.to_datetime(df['date_str'] + df['time_str'], format='%Y%m%d%H%M%S')
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        all_dfs.append(df)
    except Exception as e:
        print(f"Error parsing {f}: {e}")

if all_dfs:
    combined_df = pd.concat(all_dfs)
    combined_df = combined_df.sort_values('date').drop_duplicates(subset=['date']).reset_index(drop=True)

    combined_df.set_index('date', inplace=True)
    resampled = combined_df.resample('5min').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna().reset_index()

    print(f"Stitched {len(resampled)} 5-minute candles.")
    print(f"Date Range: {resampled['date'].min()} to {resampled['date'].max()}")

    resampled.to_csv("data/nifty_futures_5min_tt.csv", index=False)
    print("Saved to data/nifty_futures_5min_tt.csv")
else:
    print("No data extracted.")
