import os
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

class DataFetcher:
    def __init__(self, kite):
        self.kite = kite
        self.data_dir = "data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def get_nearest_future(self, exchange, name):
        try:
            instruments = self.kite.instruments(exchange)
            futs = [i for i in instruments if i['name'] == name and i['instrument_type'] == 'FUT']
            futs.sort(key=lambda x: pd.to_datetime(x['expiry']))
            if futs:
                return futs[0]['instrument_token'], futs[0]['tradingsymbol']
        except Exception as e:
            logging.error(f"Error fetching futures for {name}: {e}")
        return None, None

    def fetch_historical_data(self, instrument_token, symbol, interval="5minute", start_date=None, continuous=False):
        filename = os.path.join(self.data_dir, f"{symbol}_continuous_{interval}.csv" if continuous else f"{symbol}_{interval}.csv")

        if os.path.exists(filename):
            logging.info(f"Loaded {symbol} {interval} data from cache ({filename}).")
            df = pd.read_csv(filename, parse_dates=['date'])
            return df

        to_date = datetime.now()
        from_date = start_date if start_date else (to_date - timedelta(days=60))

        logging.info(f"Fetching {symbol} {interval} data from {from_date.date()} to {to_date.date()} (continuous={continuous})...")

        all_data = []
        chunk = timedelta(days=100)
        current = from_date

        while current < to_date:
            end = min(current + chunk, to_date)
            logging.info(f"  -> Downloading chunk: {current.date()} to {end.date()}...")
            try:
                data = self.kite.historical_data(
                    instrument_token,
                    current.strftime("%Y-%m-%d %H:%M:%S"),
                    end.strftime("%Y-%m-%d %H:%M:%S"),
                    interval,
                    continuous=continuous
                )
                if data:
                    all_data.extend(data)
            except Exception as e:
                logging.error(f"Error fetching data for {symbol} chunk: {e}")
                # If continuous fails due to interval restrictions, break and return empty so caller can handle it
                if "invalid interval" in str(e).lower() and continuous:
                    logging.warning("Continuous flag not supported for this interval. Will fallback to standard fetch.")
                    return pd.DataFrame()
                break

            current = end
            time.sleep(0.5)

        if not all_data:
            return pd.DataFrame()

        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').drop_duplicates(subset=['date']).reset_index(drop=True)
        df['date'] = df['date'].dt.tz_localize(None)

        df.to_csv(filename, index=False)
        logging.info(f"Saved {len(df)} rows for {symbol} to {filename}.")
        return df

    def get_all_required_data(self):
        deep_start = datetime(2022, 1, 1)

        instruments = [
            {"exchange": "MCX", "name": "SILVERMIC", "interval": "5minute", "start": deep_start},
            {"exchange": "MCX", "name": "GOLDGUINEA", "interval": "5minute", "start": deep_start},
            {"exchange": "NFO", "name": "NIFTY", "interval": "5minute", "start": deep_start},
            {"exchange": "NFO", "name": "BANKNIFTY", "interval": "5minute", "start": deep_start},
        ]

        data_dict = {}

        for req in instruments:
            name = req["name"]
            token, tradingsymbol = self.get_nearest_future(req["exchange"], name)

            if token:
                logging.info(f"Found active nearest future for {name}: {tradingsymbol} (Token: {token})")

                key_5m = f"{name}_5minute"
                df_5m = self.fetch_historical_data(token, name, req["interval"], req["start"], continuous=True)

                # Fallback to standard 60-day fetch if continuous intraday fails
                if df_5m.empty:
                    logging.info(f"Fallback to 60-day standard fetch for {name} 5minute...")
                    # For non-continuous, we must use the standard non-continuous filename to avoid confusing cache
                    key_5m_std = f"{name}_{req['interval']}"
                    df_5m = self.fetch_historical_data(token, name, req["interval"], start_date=datetime.now() - timedelta(days=60), continuous=False)
                    data_dict[key_5m_std] = df_5m
                else:
                    data_dict[key_5m] = df_5m

                # Daily data usually supports continuous=True
                key_1d = f"{name}_day"
                df_1d = self.fetch_historical_data(token, name, "day", deep_start, continuous=True)
                data_dict[key_1d] = df_1d
            else:
                logging.error(f"Could not find futures token for {name} on {req['exchange']}")

        self._generate_synthetic_pcr_data()
        return data_dict

    def _generate_synthetic_pcr_data(self):
        for symbol in ["NIFTY", "BANKNIFTY"]:
            filename = os.path.join(self.data_dir, f"{symbol}_continuous_day.csv")
            pcr_filename = os.path.join(self.data_dir, f"{symbol}_PCR.csv")

            if os.path.exists(pcr_filename):
                continue

            if os.path.exists(filename):
                df = pd.read_csv(filename, parse_dates=['date'])
                np.random.seed(42 if symbol == "NIFTY" else 43)
                pcr_values = [1.0]
                for i in range(1, len(df)):
                    prev_pcr = pcr_values[-1]
                    new_pcr = prev_pcr + 0.1 * (1.0 - prev_pcr) + np.random.normal(0, 0.05)
                    new_pcr = max(0.4, min(1.6, new_pcr))
                    pcr_values.append(new_pcr)

                pcr_df = pd.DataFrame({'date': df['date'], 'PCR': pcr_values})
                pcr_df.to_csv(pcr_filename, index=False)
                logging.info(f"Generated synthetic PCR data for {symbol}.")
