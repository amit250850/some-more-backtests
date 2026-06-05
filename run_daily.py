import pandas as pd
from strategies import Strategy5_VolumeDivergence
from backtester import VectorizedBacktester
from optimizer import WalkForwardOptimizer

# We only need NIFTY day data
df = pd.read_csv("data/NIFTY_continuous_day.csv", parse_dates=['date'])

param_grid = {
    'lookback': [8, 10, 15],
    'rsi_long': [25, 30, 35],
    'rsi_short': [65, 70, 75]
}

optimizer = WalkForwardOptimizer(
    data=df,
    strategy_class=Strategy5_VolumeDivergence,
    param_grid=param_grid,
    instrument="NIFTY",
    extra_data=None
)

res = optimizer.optimize()

print("\n--- RESULTS ---")
print("Best Parameters:", res['best_params'])
print("\nIn-Sample Metrics:")
for k, v in res['is_metrics'].items():
    print(f"  {k}: {v}")

print("\nOut-of-Sample Metrics:")
for k, v in res['oos_metrics'].items():
    print(f"  {k}: {v}")

print("\nWarning Flag:", res['warning'])

print("\n--- OUT-OF-SAMPLE TRADE LOG ---")
print(res['oos_trades'].to_string())

# Save equity curve
import matplotlib.pyplot as plt
trades = res['oos_trades'].copy()
if not trades.empty:
    trades['date'] = pd.to_datetime(trades['exit_date'])
    trades = trades.sort_values('date')
    trades['cum_pnl'] = trades['pnl'].cumsum()

    plt.figure(figsize=(10, 5))
    plt.plot(trades['date'], trades['cum_pnl'], marker='o', linestyle='-')
    plt.title("OOS Equity Curve: Strategy 5 (Volume Divergence) on NIFTY (Daily)")
    plt.xlabel("Date")
    plt.ylabel("Cumulative PnL (INR)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("reports/nifty_strategy5_daily_equity.png")
    print("\nEquity curve saved to reports/nifty_strategy5_daily_equity.png")
