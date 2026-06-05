import pandas as pd
import matplotlib.pyplot as plt
from strategies import Strategy6_SilverCOMEXBreakout
from backtester import VectorizedBacktester

df = pd.read_csv("data/SILVERMIC_15minute.csv", parse_dates=['date'])

# Hardcoded params as per user spec (no optimization needed for the structural rules)
params = {}

strat = Strategy6_SilverCOMEXBreakout(df, params, None)
signals = strat.generate_signals()

bt = VectorizedBacktester("SILVERMIC", "Strategy6_SilverCOMEXBreakout", params)
trades_df = bt.run_backtest(signals)
metrics = bt.calculate_metrics()

print("\n=== FINAL BACKTEST RESULTS (SILVERMIC COMEX BREAKOUT) ===")
print("Metrics:")
for k, v in metrics.items():
    print(f"  {k}: {v}")

if not trades_df.empty:
    print("\n=== TRADE LOG ===")
    print(trades_df.to_string())

    # Save equity curve
    trades_df['date'] = pd.to_datetime(trades_df['exit_date'])
    trades_df = trades_df.sort_values('date')
    trades_df['cum_pnl'] = trades_df['pnl'].cumsum()

    plt.figure(figsize=(10, 5))
    plt.plot(trades_df['date'], trades_df['cum_pnl'], marker='o', linestyle='-')
    plt.title("Equity Curve: Strategy 6 (Silver COMEX Breakout) on SILVERMIC 15m")
    plt.xlabel("Date")
    plt.ylabel("Cumulative PnL (INR)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("reports/silver_comex_equity.png")
    print("\nEquity curve saved to reports/silver_comex_equity.png")
else:
    print("\nNo trades generated.")
