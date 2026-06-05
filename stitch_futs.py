import pandas as pd
import time
import os
from kite_auth import get_kite_session
from datetime import timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def stitch_historical_nifty_5m():
    if not os.path.exists("instruments_nfo.csv"):
        logging.error("instruments_nfo.csv not found.")
        return

    # 1. Load instruments
    df = pd.read_csv("instruments_nfo.csv")

    # 2. Filter: name == "NIFTY", instrument_type == "FUT"
    nifty_futs = df[(df['name'] == 'NIFTY') & (df['instrument_type'] == 'FUT')].copy()

    if nifty_futs.empty:
        logging.error("No NIFTY FUT instruments found in the CSV.")
        return

    nifty_futs['expiry'] = pd.to_datetime(nifty_futs['expiry']).dt.tz_localize(None)

    # 3. Sort by expiry ascending, keep near-month
    nifty_futs['expiry_month'] = nifty_futs['expiry'].dt.to_period('M')
    nifty_futs = nifty_futs.sort_values('expiry')

    # Keep only the earliest expiry per month (near-month contract)
    nifty_futs = nifty_futs.drop_duplicates(subset=['expiry_month'], keep='first')

    logging.info(f"Found {len(nifty_futs)} unique monthly contracts to stitch.")

    kite = get_kite_session()
    all_data = []

    # 4. Fetch 5m data from (expiry - 28 days) to expiry
    for _, row in nifty_futs.iterrows():
        token = row['instrument_token']
        symbol = row['tradingsymbol']
        expiry = row['expiry']
        start_date = expiry - timedelta(days=28)

        # Don't fetch into the future if the contract hasn't expired yet
        current_time = pd.Timestamp.now()
        fetch_end = min(expiry, current_time)

        # If the start_date is in the future, skip
        if start_date > current_time:
            continue

        # We also need to restrict fetching to max 60 days from now due to Kite's limit for 5minute
        # BUT since we are stitching, if the token is old, kite API will reject 5m request
        # unless it's a special historical API subscription. We will try fetching anyway.

        logging.info(f"Fetching {symbol} (Token: {token}) from {start_date.date()} to {fetch_end.date()}")

        try:
            data = kite.historical_data(
                token,
                start_date.strftime("%Y-%m-%d %H:%M:%S"),
                fetch_end.strftime("%Y-%m-%d %H:%M:%S"),
                "5minute",
                continuous=False
            )
            if data:
                all_data.extend(data)
                logging.info(f"  -> Downloaded {len(data)} candles.")
            else:
                logging.warning(f"  -> No data returned for {symbol}.")
        except Exception as e:
            logging.error(f"  -> API Error for {symbol}: {e}")

        # 5. Sleep 0.5 seconds
        time.sleep(0.5)

    if not all_data:
        logging.error("No data could be fetched. Aborting.")
        return

    # 6. Stitch, drop duplicates, sort
    final_df = pd.DataFrame(all_data)
    final_df['date'] = pd.to_datetime(final_df['date']).dt.tz_localize(None)
    final_df = final_df.sort_values('date').drop_duplicates(subset=['date'], keep='last').reset_index(drop=True)

    # 7. Save
    os.makedirs("data", exist_ok=True)
    out_path = "data/nifty_futures_5min_3years.csv"
    final_df.to_csv(out_path, index=False)

    # 8. Print rows and date range
    total_rows = len(final_df)
    start_dt = final_df['date'].min()
    end_dt = final_df['date'].max()

    logging.info("=====================================")
    logging.info(f"Stitching Complete!")
    logging.info(f"Saved to: {out_path}")
    logging.info(f"Total Rows Fetched: {total_rows}")
    logging.info(f"Date Range: {start_dt} to {end_dt}")
    logging.info("=====================================")

if __name__ == "__main__":
    stitch_historical_nifty_5m()
