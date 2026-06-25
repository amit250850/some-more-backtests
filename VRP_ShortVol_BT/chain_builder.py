import pandas as pd
import numpy as np

def build_chain(df_day, current_date):
    """
    Given a bhavcopy dataframe for a single day, extracts the NIFTY near-month FUTURES
    settlement price (to use as forward F) and builds a dataframe of NIFTY options
    for the upcoming weekly expiry.
    """
    if df_day is None or df_day.empty:
        return None, None, None

    # Get futures to find near month
    futs = df_day[(df_day['instrument'] == 'FUTIDX') | (df_day['instrument'] == 'FUT')]
    if futs.empty:
        # Sometimes instrument names differ in UDiFF vs Legacy, try getting all XX opts or where opt_type is XX
        futs = df_day[df_day['opt_type'] == 'XX']

    if futs.empty:
        return None, None, None

    # Find near-month expiry
    futs = futs[futs['expiry'] >= pd.to_datetime(current_date)]
    if futs.empty:
        return None, None, None

    near_fut = futs.loc[futs['expiry'].idxmin()]
    forward_price = near_fut['settle_price']

    # Get options
    opts = df_day[(df_day['opt_type'] == 'CE') | (df_day['opt_type'] == 'PE')]
    opts = opts[opts['expiry'] >= pd.to_datetime(current_date)]

    if opts.empty:
        return None, None, None

    # Find nearest weekly expiry
    upcoming_expiry = opts['expiry'].min()

    # Filter for this expiry
    chain = opts[opts['expiry'] == upcoming_expiry].copy()

    # Calculate days to expiry (DTE)
    dte = (upcoming_expiry - pd.to_datetime(current_date)).days

    # Sometimes DTE=0 on expiry day, handle this gracefully in pricing later
    chain['dte'] = dte

    return forward_price, upcoming_expiry, chain

if __name__ == "__main__":
    from data_fetch import fetch_bhavcopy
    from datetime import datetime

    date_obj = datetime(2023, 1, 2)
    df = fetch_bhavcopy(date_obj)

    f, exp, chain = build_chain(df, date_obj)
    print(f"Date: {date_obj.date()}, Forward: {f}, Expiry: {exp.date()}, DTE: {chain['dte'].iloc[0]}")
    print(f"Chain shape: {chain.shape}")
    print(chain[['strike', 'opt_type', 'settle_price']].head())
