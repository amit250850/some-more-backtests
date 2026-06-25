import datetime
import pandas as pd
import time
from Technical import NSE
import os

os.makedirs('probe/results', exist_ok=True)

nse = None
try:
    nse = NSE()
except Exception as e:
    print(f"Init error: {e}")

output = []

def test_vix():
    print("Testing India VIX...")
    ticker = "INDIA VIX"
    label = "Various_historical"

    try:
        df = nse.get_india_vix(interval='1D')
        if df is None or df.empty:
            output.append({"function": "get_india_vix", "instrument": ticker, "time": label, "result": "EMPTY", "oldest_date": None, "granularity": None})
        else:
            oldest = df.index.min().strftime('%Y-%m-%d') if not df.empty and hasattr(df, 'index') else None
            output.append({"function": "get_india_vix", "instrument": ticker, "time": label, "result": "OK", "oldest_date": oldest, "granularity": "Daily"})
            df.to_csv(f'probe/results/get_india_vix_sample.csv', index=False)
    except Exception as e:
        msg = str(e)
        if "403" in msg or "Max retries" in msg:
            output.append({"function": "get_india_vix", "instrument": ticker, "time": label, "result": "BLOCKED", "oldest_date": None, "granularity": None})
        else:
            output.append({"function": "get_india_vix", "instrument": ticker, "time": label, "result": "ERROR", "oldest_date": None, "granularity": None})

test_vix()
pd.DataFrame(output).to_csv('probe/vix_results.csv', index=False)
