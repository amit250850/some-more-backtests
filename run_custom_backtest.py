import pandas as pd
import matplotlib.pyplot as plt
from strategies import Strategy5_VolumeDivergence
from backtester import VectorizedBacktester

df = pd.read_csv("data/nifty_futures_5min_tt.csv", parse_dates=['date'])

params = {
    'lookback': 8,
    'rsi_long': 30,
    'rsi_short': 75,
    'hold_bars': 6,
    'stop_loss': 0.01
}

strat = Strategy5_VolumeDivergence(df, params, None)
signals = strat.generate_signals()

bt = VectorizedBacktester("NIFTY", "Strategy5_VolumeDivergence", params)
trades_df = bt.run_backtest(signals)
metrics = bt.calculate_metrics()

print("\n=== FINAL BACKTEST RESULTS (TradingTuitions Historical Data) ===")
print("Metrics:")
for k, v in metrics.items():
    print(f"  {k}: {v}")

if not trades_df.empty:
    # Save equity curve
    trades_df['date'] = pd.to_datetime(trades_df['exit_date'])
    trades_df = trades_df.sort_values('date')
    trades_df['cum_pnl'] = trades_df['pnl'].cumsum()

    plt.figure(figsize=(10, 5))
    plt.plot(trades_df['date'], trades_df['cum_pnl'], marker='o', linestyle='-')
    plt.title("Equity Curve: Strategy 5 on NIFTY (TradingTuitions 2012-2014)")
    plt.xlabel("Date")
    plt.ylabel("Cumulative PnL (INR)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("reports/tt_equity.png")
    print("\nEquity curve saved to reports/tt_equity.png")
