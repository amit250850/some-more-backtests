import glob
import pandas as pd

files = glob.glob("/app/data/tt_raw/*.csv")
print(f"Found {len(files)} extracted CSVs.")

all_dfs = []
for f in files:
    try:
        df = pd.read_csv(f, names=['ticker', 'date_str', 'time_str', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['date_str'] = df['date_str'].astype(str)
        df['time_str'] = df['time_str'].astype(str).str.replace(':', '')
        df['time_str'] = df['time_str'].str.zfill(6)
        df['time_str'] = df['time_str'].apply(lambda x: x + '00' if len(x) == 4 else x)

        df['date'] = pd.to_datetime(df['date_str'] + df['time_str'], format='%Y%m%d%H%M%S', errors='coerce')
        df = df.dropna(subset=['date'])

        # Keep only NIFTY futures
        if 'NIFTY' in df['ticker'].iloc[0].upper() and 'BANK' not in df['ticker'].iloc[0].upper():
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
            all_dfs.append(df)
    except Exception as e:
        pass

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

    resampled.to_csv("/app/data/nifty_futures_5min_tt_full.csv", index=False)
    print("Saved to /app/data/nifty_futures_5min_tt_full.csv")
