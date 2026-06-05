import os
import pandas as pd
from kite_auth import get_kite_session
from data_fetcher import DataFetcher
from strategies import (
    Strategy1_SUVMomentum,
    Strategy2_VPIN,
    Strategy3_VolumeSpike,
    Strategy4_OptionVolumeImbalance,
    Strategy5_VolumeDivergence
)
from optimizer import WalkForwardOptimizer
from report_generator import ReportGenerator
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_backtest_pipeline():
    logging.info("Starting Backtest Pipeline...")

    # 1. Authenticate
    try:
        kite = get_kite_session()
    except Exception as e:
        logging.error(f"Failed to authenticate: {e}")
        return

    # 2. Fetch Data
    fetcher = DataFetcher(kite)
    data_dict = fetcher.get_all_required_data()

    if not data_dict:
        logging.error("No data fetched. Check Kite connection or API limits.")
        return

    pcr_data = None
    if os.path.exists("data/NIFTY_PCR.csv"):
        pcr_data = pd.read_csv("data/NIFTY_PCR.csv")

    # 3. Define Strategy parameters grids
    param_grids = {
        Strategy1_SUVMomentum: {
            'suv_threshold': [1.5, 2.0, 2.5],
            'hold_bars': [3, 6, 10],
            'stop_loss': [0.005, 0.015, 0.025]
        },
        Strategy2_VPIN: {
            'vpin_threshold': [0.5, 0.6, 0.8],
            'bucket_divisor': [30, 50, 70],
            'stop_loss': [0.005, 0.015, 0.03]
        },
        Strategy3_VolumeSpike: {
            'spike_sigma': [1.5, 2.0, 3.0],
            'lookback': [15, 20, 25],
            'atr_multiplier': [1.5, 2.0, 3.0]
        },
        Strategy4_OptionVolumeImbalance: {
            'pcr_percentile': [90, 95, 99],
            'opt_exit_pct': [0.15, 0.25, 0.40]
        },
        Strategy5_VolumeDivergence: {
            'lookback': [8, 10, 15],
            'rsi_long': [25, 30, 35],
            'rsi_short': [65, 70, 75]
        }
    }

    instruments = ["SILVERMIC", "GOLDGUINEA", "NIFTY", "BANKNIFTY"]
    strategies = [
        Strategy1_SUVMomentum,
        Strategy2_VPIN,
        Strategy3_VolumeSpike,
        Strategy4_OptionVolumeImbalance,
        Strategy5_VolumeDivergence
    ]

    results = []
    all_oos_trades = []

    # 4. Optimization and Backtesting
    for inst in instruments:
        key_5m = f"{inst}_5minute"
        df_5m = data_dict.get(key_5m)

        if df_5m is None or df_5m.empty:
            logging.warning(f"Missing 5m data for {inst}. Skipping.")
            continue

        for StratClass in strategies:
            if StratClass == Strategy4_OptionVolumeImbalance and inst not in ["NIFTY", "BANKNIFTY"]:
                continue

            logging.info(f"Running {StratClass.__name__} on {inst}...")

            grid = param_grids[StratClass]
            extra_data = pcr_data if StratClass == Strategy4_OptionVolumeImbalance else None

            optimizer = WalkForwardOptimizer(
                data=df_5m,
                strategy_class=StratClass,
                param_grid=grid,
                instrument=inst,
                extra_data=extra_data
            )

            res = optimizer.optimize()

            res['instrument'] = inst
            res['strategy'] = StratClass.__name__

            results.append(res)

            if not res['oos_trades'].empty:
                all_oos_trades.append(res['oos_trades'])

    # 5. Generate Reports
    logging.info("Generating reports...")
    report_gen = ReportGenerator(results, all_oos_trades)
    report_gen.generate_all()

    logging.info("Pipeline Complete.")

if __name__ == "__main__":
    run_backtest_pipeline()
