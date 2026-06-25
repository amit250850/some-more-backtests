import requests
import zipfile
import io
import pandas as pd
import os
from datetime import datetime, timedelta
import time
import yfinance as yf

# Common headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

DATA_DIR = "/app/VRP_ShortVol_BT/data"
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_bhavcopy(date_obj):
    """
    Fetches the bhavcopy for a given date. Handles both legacy and new UDiFF formats.
    Returns a DataFrame if successful, else None.
    """
    # 1. Check local cache (parquet)
    date_str = date_obj.strftime("%Y-%m-%d")
    cache_path = os.path.join(DATA_DIR, f"bhavcopy_{date_str}.parquet")
    if not os.path.exists(cache_path):
        return None
    if os.path.exists(cache_path):
        pass # print(f"[{date_str}] Loading from cache")
        return pd.read_parquet(cache_path)

    session = requests.Session()
    session.headers.update(HEADERS)

    # Sometimes getting main page sets cookies
    try:
        session.get('https://www.nseindia.com', timeout=5)
    except:
        pass

    year = date_obj.strftime('%Y')
    month = date_obj.strftime('%b').upper()
    day = date_obj.strftime('%d')
    date_fmt = date_obj.strftime('%Y%m%d')

    # Trying UDiFF format first (for dates post ~July 2024, but sometimes works earlier)
    # The current working url we found for 2024 is content/fo/...
    udiff_url = f"https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{date_fmt}_F_0000.csv.zip"

    # Legacy URL
    legacy_url = f"https://nsearchives.nseindia.com/content/historical/DERIVATIVES/{year}/{month}/fo{day}{month}{year}bhav.csv.zip"

    urls_to_try = [
        ("UDiFF", udiff_url),
        ("Legacy", legacy_url)
    ]

    for fmt, url in urls_to_try:
        # pass # print(f"[{date_str}] Trying {fmt} format: {url}")
        try:
            r = session.get(url, timeout=10)
            if r.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    filename = z.namelist()[0]
                    with z.open(filename) as f:
                        df = pd.read_csv(f)

                        # Normalize columns between legacy and new
                        # Legacy: 'INSTRUMENT', 'SYMBOL', 'EXPIRY_DT', 'STRIKE_PR', 'OPTION_TYP', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'SETTLE_PR', 'CONTRACTS', 'OPEN_INT'
                        # New: 'TradDt', 'FinInstrmTp', 'TckrSymb', 'FininstrmActlXpryDt', 'StrkPric', 'OptnTp', 'OpnPric', 'HghPric', 'LwPric', 'ClsPric', 'SttlmPric', 'TtlNbOfTxsExctd'/'TtlTradgVol', 'OpnIntrst'

                        normalized_df = pd.DataFrame()

                        if fmt == "Legacy":
                            # Filter NIFTY
                            df = df[df['SYMBOL'] == 'NIFTY']
                            normalized_df['date'] = pd.to_datetime(df['TIMESTAMP'], format='%d-%b-%Y')
                            normalized_df['instrument'] = df['INSTRUMENT']
                            normalized_df['symbol'] = df['SYMBOL']
                            normalized_df['expiry'] = pd.to_datetime(df['EXPIRY_DT'], format='%d-%b-%Y')
                            normalized_df['strike'] = df['STRIKE_PR']
                            normalized_df['opt_type'] = df['OPTION_TYP'] # CE, PE, XX (Futures)
                            normalized_df['open'] = df['OPEN']
                            normalized_df['high'] = df['HIGH']
                            normalized_df['low'] = df['LOW']
                            normalized_df['close'] = df['CLOSE']
                            normalized_df['settle_price'] = df['SETTLE_PR']
                            normalized_df['volume'] = df['CONTRACTS']
                            normalized_df['oi'] = df['OPEN_INT']

                        else: # UDiFF
                            df = df[df['TckrSymb'] == 'NIFTY']
                            normalized_df['date'] = pd.to_datetime(df['TradDt'])

                            # FinInstrmTp mapping (FUTIDX, OPTIDX, etc)
                            def map_inst(x):
                                if x == 'FUTIDX': return 'FUTIDX'
                                if x == 'OPTIDX': return 'OPTIDX'
                                return x

                            normalized_df['instrument'] = df['FinInstrmTp'].apply(map_inst)
                            normalized_df['symbol'] = df['TckrSymb']
                            normalized_df['expiry'] = pd.to_datetime(df['FininstrmActlXpryDt'])
                            normalized_df['strike'] = df['StrkPric']
                            normalized_df['opt_type'] = df['OptnTp'] # CE, PE, XX
                            normalized_df['open'] = df['OpnPric']
                            normalized_df['high'] = df['HghPric']
                            normalized_df['low'] = df['LwPric']
                            normalized_df['close'] = df['ClsPric']
                            normalized_df['settle_price'] = df['SttlmPric']
                            normalized_df['volume'] = df['TtlTradgVol']
                            normalized_df['oi'] = df['OpnIntrst']

                        # Ensure numeric
                        for col in ['strike', 'open', 'high', 'low', 'close', 'settle_price', 'volume', 'oi']:
                            normalized_df[col] = pd.to_numeric(normalized_df[col], errors='coerce')

                        # Save to cache
                        normalized_df.to_parquet(cache_path)
                        pass # print(f"[{date_str}] Downloaded and cached successfully ({fmt})")
                        return normalized_df
            elif r.status_code == 404:
                # Normal for missing dates, try next format
                pass
            else:
                pass
                # print(f"  Got status {r.status_code}")
        except Exception as e:
            # print(f"  Exception: {e}")
            pass

        time.sleep(0.5) # Polite delay

    pass # print(f"[{date_str}] Could not fetch data (might be a holiday)")
    return None

def fetch_nifty_spot(start_date, end_date):
    """
    Fetches NIFTY spot data from yfinance.
    """
    cache_path = os.path.join(DATA_DIR, "nifty_spot.parquet")

    # We always download up to current if possible, but let's cache it
    # For simplicity, if cache exists we can just load it and append, but let's just redownload
    # as yfinance is fast.
    print(f"Fetching NIFTY spot from {start_date} to {end_date}...")
    df = yf.download('^NSEI', start=start_date, end=end_date)
    if df.empty:
        if os.path.exists(cache_path):
            print("yfinance failed, loading spot from cache.")
            return pd.read_parquet(cache_path)
        else:
            raise Exception("Could not fetch spot data and no cache exists.")

    # Normalize yfinance output
    # Ticker ^NSEI creates MultiIndex columns in recent versions if we pass string but sometimes not
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    df = df.reset_index()
    df.columns = [c.lower() for c in df.columns]

    df.to_parquet(cache_path)
    return df

if __name__ == "__main__":
    # Test fetch for one recent day and one old day
    df_old = fetch_bhavcopy(datetime(2023, 1, 2))
    if df_old is not None:
        print("Old data sample:")
        print(df_old.head(2))

    df_new = fetch_bhavcopy(datetime(2024, 8, 1))
    if df_new is not None:
        print("New data sample:")
        print(df_new.head(2))

    spot = fetch_nifty_spot("2019-01-01", "2024-09-01")
    print("Spot data sample:")
    print(spot.head(2))
