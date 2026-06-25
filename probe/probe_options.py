import datetime
import pandas as pd
import time
from Derivatives import NSE, Sensibull
import os

os.makedirs('probe/results', exist_ok=True)

nse = None
sb = None
try:
    nse = NSE()
    sb = Sensibull()
except Exception as e:
    print(f"Init error: {e}")

output = []

# Base date assuming today is June 25, 2026
base_date = datetime.datetime(2026, 6, 25)

def test_option_chain():
    print("Testing option chain...")
    instruments = [('NIFTY', True), ('BANKNIFTY', True), ('RELIANCE', False)]

    time_points = [
        ("1_week_ago", base_date - datetime.timedelta(days=7)),
        ("1_month_ago", base_date - datetime.timedelta(days=30)),
        ("6_months_ago", base_date - datetime.timedelta(days=180)),
        ("1_year_ago", datetime.datetime(2025, 6, 1)),
        ("2_years_ago", datetime.datetime(2024, 6, 1)),
        ("4_years_ago", datetime.datetime(2022, 6, 1)),
        ("6_years_ago", datetime.datetime(2020, 6, 1)),
        ("Past_Weekly_2025", datetime.datetime(2025, 5, 29)), # Thursday
        ("Past_Weekly_2023", datetime.datetime(2023, 6, 29)), # Thursday
        ("Past_Weekly_2020", datetime.datetime(2020, 6, 25)), # Thursday
    ]

    for ticker, is_index in instruments:
        for label, dt in time_points:
            try:
                df = nse.get_option_chain(ticker=ticker, expiry=dt, is_index=is_index)
                if df is None or df.empty:
                    output.append({"function": "get_option_chain", "instrument": ticker, "time": label, "result": "EMPTY", "oldest_date": None, "granularity": None})
                else:
                    output.append({"function": "get_option_chain", "instrument": ticker, "time": label, "result": "OK", "oldest_date": dt.strftime('%Y-%m-%d'), "granularity": "EOD"})
                    df.to_csv(f'probe/results/get_option_chain_{ticker}_{label}_sample.csv', index=False)
            except Exception as e:
                msg = str(e)
                if "403" in msg or "Max retries" in msg:
                    output.append({"function": "get_option_chain", "instrument": ticker, "time": label, "result": "BLOCKED", "oldest_date": None, "granularity": None})
                elif "strikePrice" in msg:
                    output.append({"function": "get_option_chain", "instrument": ticker, "time": label, "result": "EMPTY", "oldest_date": None, "granularity": None})
                else:
                    output.append({"function": "get_option_chain", "instrument": ticker, "time": label, "result": "ERROR", "oldest_date": None, "granularity": None})
            time.sleep(1)

def test_sensibull_greeks():
    print("Testing Sensibull greeks...")
    instruments = ['NIFTY', 'BANKNIFTY', 'RELIANCE']

    time_points = [
        ("1_week_ago", base_date - datetime.timedelta(days=7)),
        ("1_month_ago", base_date - datetime.timedelta(days=30)),
        ("6_months_ago", base_date - datetime.timedelta(days=180)),
        ("1_year_ago", datetime.datetime(2025, 6, 1)),
        ("2_years_ago", datetime.datetime(2024, 6, 1)),
        ("4_years_ago", datetime.datetime(2022, 6, 1)),
        ("6_years_ago", datetime.datetime(2020, 6, 1)),
        ("Past_Weekly_2025", datetime.datetime(2025, 5, 29)),
        ("Past_Weekly_2023", datetime.datetime(2023, 6, 29)),
        ("Past_Weekly_2020", datetime.datetime(2020, 6, 25)),
    ]

    for ticker in instruments:
        for label, dt in time_points:
            try:
                sb_token = sb.search_token(ticker)
                if sb_token and 'instrument_token' in sb_token:
                    greeks_df, atm_strike = sb.get_options_data_with_greeks(sb_token, num_look_ups_from_atm=5, expiry_date=dt)
                    if greeks_df is None or greeks_df.empty:
                        output.append({"function": "get_options_data_with_greeks", "instrument": ticker, "time": label, "result": "EMPTY", "oldest_date": None, "granularity": None})
                    else:
                        output.append({"function": "get_options_data_with_greeks", "instrument": ticker, "time": label, "result": "OK", "oldest_date": dt.strftime('%Y-%m-%d'), "granularity": "EOD"})
                        greeks_df.to_csv(f'probe/results/get_options_data_with_greeks_{ticker}_{label}_sample.csv', index=False)
                else:
                    output.append({"function": "get_options_data_with_greeks", "instrument": ticker, "time": label, "result": "ERROR", "oldest_date": None, "granularity": None})
            except Exception as e:
                msg = str(e)
                if "403" in msg or "Max retries" in msg:
                    output.append({"function": "get_options_data_with_greeks", "instrument": ticker, "time": label, "result": "BLOCKED", "oldest_date": None, "granularity": None})
                else:
                    output.append({"function": "get_options_data_with_greeks", "instrument": ticker, "time": label, "result": "ERROR", "oldest_date": None, "granularity": None})
            time.sleep(1)

def test_expiry_dates():
    print("Testing expiry dates...")
    instruments = [('NIFTY', True), ('BANKNIFTY', True), ('RELIANCE', False)]
    for ticker, is_index in instruments:
        try:
            expiries = nse.get_options_expiry(ticker=ticker, is_index=is_index)
            if not expiries:
                output.append({"function": "get_options_expiry", "instrument": ticker, "time": "current", "result": "EMPTY", "oldest_date": None, "granularity": None})
            else:
                oldest_date = expiries[0].strftime('%Y-%m-%d')
                output.append({"function": "get_options_expiry", "instrument": ticker, "time": "current", "result": "OK", "oldest_date": oldest_date, "granularity": "List of dates"})
                # We save a dummy sample with the list of dates
                pd.DataFrame({"expiries": expiries}).to_csv(f'probe/results/get_options_expiry_{ticker}_sample.csv', index=False)
        except Exception as e:
            msg = str(e)
            if "403" in msg or "Max retries" in msg:
                output.append({"function": "get_options_expiry", "instrument": ticker, "time": "current", "result": "BLOCKED", "oldest_date": None, "granularity": None})
            else:
                output.append({"function": "get_options_expiry", "instrument": ticker, "time": "current", "result": "ERROR", "oldest_date": None, "granularity": None})
        time.sleep(1)

test_option_chain()
test_sensibull_greeks()
test_expiry_dates()
pd.DataFrame(output).to_csv('probe/options_results.csv', index=False)
