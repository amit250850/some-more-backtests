import yfinance as yf
import pandas as pd

print("Downloading COMEX Silver data (SI=F)...")
si = yf.Ticker("SI=F")
df_comex = si.history(period="10y", interval="1d").reset_index()
df_comex.columns = [c.lower() for c in df_comex.columns]
df_comex['date'] = pd.to_datetime(df_comex['date']).dt.tz_localize(None)
df_comex = df_comex[['date', 'open', 'high', 'low', 'close', 'volume']]
df_comex.to_csv("data/COMEX_SILVER_day.csv", index=False)
print(f"Saved {len(df_comex)} rows to data/COMEX_SILVER_day.csv")

print("Downloading Dollar Index data (DX-Y.NYB)...")
dxy = yf.Ticker("DX-Y.NYB")
df_dxy = dxy.history(period="10y", interval="1d").reset_index()
df_dxy.columns = [c.lower() for c in df_dxy.columns]
df_dxy['date'] = pd.to_datetime(df_dxy['date']).dt.tz_localize(None)
df_dxy = df_dxy[['date', 'open', 'high', 'low', 'close']]
df_dxy.to_csv("data/DXY_day.csv", index=False)
print(f"Saved {len(df_dxy)} rows to data/DXY_day.csv")
