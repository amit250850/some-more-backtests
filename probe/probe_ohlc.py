import datetime
import pandas as pd
import time
from Derivatives import NSE
import os

os.makedirs('probe/results', exist_ok=True)

nse = None
try:
    nse = NSE()
except Exception as e:
    print(f"Init error: {e}")

output = []

def test_ohlc():
    print("Testing OHLC Data...")

    # We will test NIFTY index, an option symbol, and a future symbol
    instruments = [
        ('NIFTY 50', True, 'Index'),
        ('NIFTY', True, 'Index_fallback'),
        ('BANKNIFTY', True, 'Index'),
        ('RELIANCE', False, 'Equity')
    ]
    label = "Various_historical"

    for ticker, is_index, inst_type in instruments:
        try:
            df = nse.get_ohlc_data(ticker_or_idx=ticker, timeframe='1D', is_index=is_index)
            if df is None or df.empty:
                output.append({"function": "get_ohlc_data", "instrument": ticker, "time": label, "result": "EMPTY", "oldest_date": None, "granularity": None})
            else:
                oldest = df.index.min().strftime('%Y-%m-%d') if hasattr(df, 'index') and not df.empty else None
                output.append({"function": "get_ohlc_data", "instrument": ticker, "time": label, "result": "OK", "oldest_date": oldest, "granularity": "Daily"})
                df.to_csv(f'probe/results/get_ohlc_data_{ticker}_sample.csv', index=False)
        except Exception as e:
            msg = str(e)
            if "403" in msg or "Max retries" in msg:
                output.append({"function": "get_ohlc_data", "instrument": ticker, "time": label, "result": "BLOCKED", "oldest_date": None, "granularity": None})
            else:
                output.append({"function": "get_ohlc_data", "instrument": ticker, "time": label, "result": "ERROR", "oldest_date": None, "granularity": None})
        time.sleep(1)

def test_futures_ohlc():
    print("Testing Futures OHLC Data...")
    try:
        futures_df = nse.get_index_futures_data('nse50_fut')
        if not futures_df.empty:
            ticker = futures_df.iloc[0]['identifier']
            df = nse.get_ohlc_data(ticker_or_idx=ticker, timeframe='1D', is_index=True)
            if df is None or df.empty:
                output.append({"function": "get_ohlc_data (Futures)", "instrument": ticker, "time": "Various_historical", "result": "EMPTY", "oldest_date": None, "granularity": None})
            else:
                oldest = df.index.min().strftime('%Y-%m-%d') if hasattr(df, 'index') and not df.empty else None
                output.append({"function": "get_ohlc_data (Futures)", "instrument": ticker, "time": "Various_historical", "result": "OK", "oldest_date": oldest, "granularity": "Daily"})
                df.to_csv(f'probe/results/get_ohlc_data_future_sample.csv', index=False)
        else:
             output.append({"function": "get_index_futures_data", "instrument": 'nse50_fut', "time": "current", "result": "EMPTY", "oldest_date": None, "granularity": None})
    except Exception as e:
        msg = str(e)
        if "403" in msg or "Max retries" in msg:
            output.append({"function": "get_ohlc_data (Futures)", "instrument": 'NIFTY_FUT', "time": "Various_historical", "result": "BLOCKED", "oldest_date": None, "granularity": None})
        else:
            output.append({"function": "get_ohlc_data (Futures)", "instrument": 'NIFTY_FUT', "time": "Various_historical", "result": "ERROR", "oldest_date": None, "granularity": None})
    time.sleep(1)

def test_options_ohlc():
    print("Testing Options OHLC Data...")
    try:
        # Get current expiries
        expiries = nse.get_options_expiry('NIFTY', is_index=True)
        if expiries:
            # get chain
            chain_df = nse.get_option_chain(ticker='NIFTY', expiry=expiries[0], is_index=True)
            if not chain_df.empty and 'CE_identifier' in chain_df.columns:
                ticker = chain_df.iloc[0]['CE_identifier']
                df = nse.get_ohlc_data(ticker_or_idx=ticker, timeframe='1D', is_index=True)
                if df is None or df.empty:
                    output.append({"function": "get_ohlc_data (Options)", "instrument": ticker, "time": "Various_historical", "result": "EMPTY", "oldest_date": None, "granularity": None})
                else:
                    oldest = df.index.min().strftime('%Y-%m-%d') if hasattr(df, 'index') and not df.empty else None
                    output.append({"function": "get_ohlc_data (Options)", "instrument": ticker, "time": "Various_historical", "result": "OK", "oldest_date": oldest, "granularity": "Daily"})
                    df.to_csv(f'probe/results/get_ohlc_data_option_sample.csv', index=False)
            else:
                 output.append({"function": "get_option_chain (for OHLC)", "instrument": 'NIFTY', "time": "current", "result": "EMPTY", "oldest_date": None, "granularity": None})
    except Exception as e:
        msg = str(e)
        if "403" in msg or "Max retries" in msg:
            output.append({"function": "get_ohlc_data (Options)", "instrument": 'NIFTY_OPT', "time": "Various_historical", "result": "BLOCKED", "oldest_date": None, "granularity": None})
        else:
            output.append({"function": "get_ohlc_data (Options)", "instrument": 'NIFTY_OPT', "time": "Various_historical", "result": "ERROR", "oldest_date": None, "granularity": None})
    time.sleep(1)


test_ohlc()
test_futures_ohlc()
test_options_ohlc()

pd.DataFrame(output).to_csv('probe/ohlc_results.csv', index=False)
