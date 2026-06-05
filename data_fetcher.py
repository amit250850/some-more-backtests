import os
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

    def get_instrument_token(self, exchange, tradingsymbol_like):
        try:
            instruments = self.kite.instruments(exchange)
            for instr in instruments:
                if tradingsymbol_like in instr['tradingsymbol']:
                    return instr['instrument_token']
        except Exception as e:
            logging.error(f"Error fetching instruments for {exchange}: {e}")
        return None

    def fetch_historical_data(self, instrument_token, symbol, interval="5minute", days_back=60):
        filename = os.path.join(self.data_dir, f"{symbol}_{interval}.csv")

        if os.path.exists(filename):
            logging.info(f"Loaded {symbol} {interval} data from cache.")
            df = pd.read_csv(filename, parse_dates=['date'])
            return df

        logging.info(f"Fetching {symbol} {interval} data from Kite API for last {days_back} days...")

        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)

        all_data = []
        chunk_size = 30
        current_to_date = to_date

        while current_to_date > from_date:
            current_from_date = max(current_to_date - timedelta(days=chunk_size), from_date)
            try:
                data = self.kite.historical_data(
                    instrument_token,
                    current_from_date.strftime("%Y-%m-%d %H:%M:%S"),
                    current_to_date.strftime("%Y-%m-%d %H:%M:%S"),
                    interval
                )
                if data:
                    all_data.extend(data)
            except Exception as e:
                logging.error(f"Error fetching data for {symbol}: {e}")

            current_to_date = current_from_date - timedelta(days=1)

        if not all_data:
            logging.warning(f"No data found for {symbol}.")
            return pd.DataFrame()

        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').drop_duplicates(subset=['date']).reset_index(drop=True)
        df['date'] = df['date'].dt.tz_localize(None)

        df.to_csv(filename, index=False)
        logging.info(f"Saved {len(df)} rows for {symbol} to {filename}.")
        return df

    def get_all_required_data(self):
        instruments = [
            {"exchange": "MCX", "symbol": "SILVERMIC", "interval": "5minute", "days": 60},
            {"exchange": "MCX", "symbol": "GOLDGUINEA", "interval": "5minute", "days": 60},
            {"exchange": "NFO", "symbol": "NIFTY", "interval": "5minute", "days": 60},
            {"exchange": "NFO", "symbol": "BANKNIFTY", "interval": "5minute", "days": 60},
        ]

        instruments_daily = [
            {"exchange": "MCX", "symbol": "SILVERMIC", "interval": "day", "days": 400},
            {"exchange": "MCX", "symbol": "GOLDGUINEA", "interval": "day", "days": 400},
            {"exchange": "NFO", "symbol": "NIFTY", "interval": "day", "days": 400},
            {"exchange": "NFO", "symbol": "BANKNIFTY", "interval": "day", "days": 400},
        ]

        data_dict = {}

        for req in instruments + instruments_daily:
            symbol = req["symbol"]
            token = self.get_instrument_token(req["exchange"], symbol)

            if token:
                key = f"{symbol}_{req['interval']}"
                df = self.fetch_historical_data(token, symbol, req["interval"], req["days"])
                data_dict[key] = df
            else:
                logging.error(f"Could not find token for {symbol} on {req['exchange']}")

        self._generate_synthetic_pcr_data()
        return data_dict

    def _generate_synthetic_pcr_data(self):
        for symbol in ["NIFTY", "BANKNIFTY"]:
            filename = os.path.join(self.data_dir, f"{symbol}_day.csv")
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
