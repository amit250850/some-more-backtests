import yfinance as yf
import pandas as pd

print("Downloading COMEX Silver data (SI=F)...")
si = yf.Ticker("SI=F")
df_comex = si.history(period="10y", interval="1d")
df_comex = df_comex.reset_index()

# Clean up column names and timezone
df_comex.columns = [c.lower() for c in df_comex.columns]
df_comex['date'] = pd.to_datetime(df_comex['date']).dt.tz_localize(None)

# Keep what we need
df_comex = df_comex[['date', 'open', 'high', 'low', 'close', 'volume']]

df_comex.to_csv("data/COMEX_SILVER_day.csv", index=False)
print(f"Saved {len(df_comex)} rows to data/COMEX_SILVER_day.csv")
