import pandas as pd
import numpy as np
import os
import yaml
from datetime import datetime
from data_fetch import fetch_bhavcopy
from chain_builder import build_chain
from black76_greeks import implied_volatility

def compute_daily_atm_iv():
    with open('/app/VRP_ShortVol_BT/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    start_date = pd.to_datetime(config['dates']['start'])
    end_date = pd.to_datetime(config['dates']['end'])

    date_range = pd.date_range(start=start_date, end=end_date, freq='B')

    iv_records = []

    print("Computing daily ATM IV...")
    for date_obj in date_range:
        # Avoid console spam
        df_day = fetch_bhavcopy(date_obj)
        if df_day is None:
            continue

        f, upcoming_expiry, chain = build_chain(df_day, date_obj)
        if chain is None or chain.empty:
            continue

        dte = chain['dte'].iloc[0]
        T = max(dte, 0.001) / 365.0
        r = config['pricing']['risk_free_rate']

        # Find ATM strike
        chain['dist'] = abs(chain['strike'] - f)
        atm_strike = chain.loc[chain['dist'].idxmin(), 'strike']

        atm_ce_opts = chain[(chain['strike'] == atm_strike) & (chain['opt_type'] == 'CE')]
        atm_pe_opts = chain[(chain['strike'] == atm_strike) & (chain['opt_type'] == 'PE')]

        iv_ce = np.nan
        iv_pe = np.nan

        if not atm_ce_opts.empty:
            iv_ce = implied_volatility(atm_ce_opts['settle_price'].iloc[0], f, atm_strike, T, r, 'CE')

        if not atm_pe_opts.empty:
            iv_pe = implied_volatility(atm_pe_opts['settle_price'].iloc[0], f, atm_strike, T, r, 'PE')

        avg_iv = np.nanmean([iv_ce, iv_pe])

        iv_records.append({'date': date_obj, 'f': f, 'atm_strike': atm_strike, 'atm_iv': avg_iv})

    df_iv = pd.DataFrame(iv_records)

    # Forward fill missing IVs (e.g. solver failed)
    df_iv['atm_iv'] = df_iv['atm_iv'].ffill()

    # Compute 252-day Rolling IV Percentile
    # To compute percentile: rank within window / count of window
    df_iv['ivp_252'] = df_iv['atm_iv'].rolling(window=252, min_periods=126).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100, raw=False
    )

    df_iv.to_csv('/app/VRP_ShortVol_BT/atm_iv.csv', index=False)
    print("Saved to atm_iv.csv. Head:")
    print(df_iv.head())
    print("Tail:")
    print(df_iv.tail())

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore')
    compute_daily_atm_iv()
