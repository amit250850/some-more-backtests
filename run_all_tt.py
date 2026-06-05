import pandas as pd
from backtester import VectorizedBacktester
from strategies import (
    Strategy1_SUVMomentum,
    Strategy2_VPIN,
    Strategy3_VolumeSpike,
    Strategy5_VolumeDivergence
)

df = pd.read_csv("/app/data/nifty_futures_5min_tt.csv", parse_dates=['date'])
print(f"Data: {len(df)} candles from {df['date'].min()} to {df['date'].max()}")

strategies = [
    (Strategy1_SUVMomentum, {'suv_threshold': 2.0, 'hold_bars': 6, 'stop_loss': 0.01}),
    (Strategy2_VPIN, {'vpin_threshold': 0.6, 'bucket_divisor': 50, 'stop_loss': 0.01}),
    (Strategy3_VolumeSpike, {'spike_sigma': 2.0, 'lookback': 20, 'atr_multiplier': 2.0}),
    (Strategy5_VolumeDivergence, {'lookback': 8, 'rsi_long': 30, 'rsi_short': 75, 'hold_bars': 6, 'stop_loss': 0.01})
]

print("\n=== RESULTS ON 2012-2014 DATA ===")
for strat_class, params in strategies:
    strat = strat_class(df, params, None)
    signals = strat.generate_signals()

    bt = VectorizedBacktester("NIFTY", strat_class.__name__, params)
    trades_df = bt.run_backtest(signals)
    metrics = bt.calculate_metrics()

    print(f"\n{strat_class.__name__}")
    print(f"  Trades: {metrics['Total Trades']}")
    print(f"  Win Rate: {metrics['Win Rate %']}%")
    print(f"  Sharpe: {metrics['Sharpe Ratio']}")
    print(f"  Return: {metrics['Total Return %']}%")
    print(f"  Max DD: {metrics['Max Drawdown %']}%")
