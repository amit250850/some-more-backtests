import pandas as pd
import matplotlib.pyplot as plt
from strategies import Strategy7_COMEXGapFill
from backtester import VectorizedBacktester
from optimizer import WalkForwardOptimizer

df_mcx = pd.read_csv("data/SILVERMIC_continuous_day.csv", parse_dates=['date'])
df_comex = pd.read_csv("data/COMEX_SILVER_day.csv", parse_dates=['date'])

param_grid = {
    'divergence_threshold': [0.003, 0.005, 0.008],
    'stop_loss': [0.01, 0.02],
    'hold_bars': [1, 2] # Exit same day or next day
}

optimizer = WalkForwardOptimizer(
    data=df_mcx,
    strategy_class=Strategy7_COMEXGapFill,
    param_grid=param_grid,
    instrument="SILVERMIC",
    extra_data=df_comex
)

res = optimizer.optimize()

print("\n=== FINAL BACKTEST RESULTS (SILVERMIC-COMEX GAP FADE) ===")
print("Best Parameters:", res['best_params'])
print("\nMetrics:")
for k, v in res['oos_metrics'].items():
    print(f"  {k}: {v}")

trades_df = res['oos_trades']
if not trades_df.empty:
    print("\n=== OOS TRADE LOG (Last 5 trades) ===")
    print(trades_df.tail(5).to_string())

    trades_df['date'] = pd.to_datetime(trades_df['exit_date'])
    trades_df = trades_df.sort_values('date')
    trades_df['cum_pnl'] = trades_df['pnl'].cumsum()

    plt.figure(figsize=(10, 5))
    plt.plot(trades_df['date'], trades_df['cum_pnl'], marker='o', linestyle='-')
    plt.title("OOS Equity Curve: Strategy 7 (MCX-COMEX Gap Fade) on SILVERMIC")
    plt.xlabel("Date")
    plt.ylabel("Cumulative PnL (INR)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("reports/mcx_comex_gap_equity.png")
    print("\nEquity curve saved to reports/mcx_comex_gap_equity.png")
else:
    print("\nNo OOS trades generated.")
