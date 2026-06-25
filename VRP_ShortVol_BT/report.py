import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yaml
from tabulate import tabulate

def get_max_losing_streak(pnl_series):
    streak = 0
    max_streak = 0
    for pnl in pnl_series:
        if pnl < 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    return max_streak

def generate_report(trades_df, config_path='/app/VRP_ShortVol_BT/config.yaml'):
    if trades_df.empty:
        print("No trades to report.")
        return

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    capital = config['capital']

    trades = trades_df.copy()
    trades['cum_net_pnl_close'] = trades['net_pnl_close'].cumsum()
    trades['cum_gross_pnl_close'] = trades['gross_pnl_close'].cumsum()
    trades['cum_net_pnl_high'] = trades['net_pnl_high'].cumsum()

    trades['equity'] = capital + trades['cum_net_pnl_close']

    total_trades = len(trades)
    wins = trades[trades['net_pnl_close'] > 0]
    losses = trades[trades['net_pnl_close'] <= 0]

    win_pct = len(wins) / total_trades if total_trades > 0 else 0
    avg_win = wins['net_pnl_close'].mean() if not wins.empty else 0
    avg_loss = losses['net_pnl_close'].mean() if not losses.empty else 0

    reward_risk = abs(avg_win / avg_loss) if avg_loss != 0 else np.inf
    expectancy = (win_pct * avg_win) - ((1 - win_pct) * abs(avg_loss))

    max_losing_streak = get_max_losing_streak(trades['net_pnl_close'])

    # Max Drawdown
    trades['peak'] = trades['equity'].cummax()
    trades['drawdown'] = trades['equity'] - trades['peak']
    max_dd_rupee = trades['drawdown'].min()
    max_dd_pct = (max_dd_rupee / capital) * 100

    # CAGR
    days = (trades['exit_date'].max() - trades['entry_date'].min()).days
    years = days / 365.25 if days > 0 else 0
    total_return = trades['cum_net_pnl_close'].iloc[-1] / capital
    cagr = ((1 + total_return) ** (1 / years) - 1) * 100 if years > 0 else 0

    calmar = cagr / abs(max_dd_pct) if max_dd_pct != 0 else np.inf

    worst_expiry = trades.loc[trades['net_pnl_close'].idxmin()]

    print("\n" + "="*40)
    print("VRP SHORT VOLATILITY BACKTEST REPORT")
    print("="*40)
    print(f"Total Trades: {total_trades}")
    print(f"Net P&L (Close): ₹{trades['cum_net_pnl_close'].iloc[-1]:.2f}")
    print(f"Net P&L (High):  ₹{trades['cum_net_pnl_high'].iloc[-1]:.2f}")
    print(f"CAGR: {cagr:.2f}%")
    print(f"Win Rate: {win_pct*100:.2f}%")
    print(f"Avg Win: ₹{avg_win:.2f} | Avg Loss: ₹{avg_loss:.2f}")
    print(f"Reward:Risk: {reward_risk:.2f}")
    print(f"Expectancy: ₹{expectancy:.2f}")
    print(f"Max Drawdown: ₹{max_dd_rupee:.2f} ({max_dd_pct:.2f}%)")
    print(f"Calmar Ratio: {calmar:.2f}")
    print(f"Max Losing Streak: {max_losing_streak}")
    print(f"Worst Single Trade: ₹{worst_expiry['net_pnl_close']:.2f} on expiry {worst_expiry['expiry'].date()}")

    # Year-wise metrics
    trades['year'] = trades['exit_date'].dt.year
    year_wise = []

    for year, group in trades.groupby('year'):
        y_net_pnl = group['net_pnl_close'].sum()

        # approximate year max DD using absolute peak-to-trough within the year
        # A more precise way would reset equity to start-of-year capital, but standard is just within the series
        g_equity = capital + group['net_pnl_close'].cumsum()
        g_peak = g_equity.cummax()
        g_dd = g_equity - g_peak
        y_max_dd = g_dd.min()

        year_wise.append({
            'Year': year,
            'Net P&L': round(y_net_pnl, 2),
            'Max DD (₹)': round(y_max_dd, 2)
        })

    print("\n--- YEAR-WISE PERFORMANCE ---")
    print(tabulate(year_wise, headers="keys", tablefmt="pretty"))

    print("\n--- VERDICT ---")
    gates_passed = True
    if calmar < 1.0:
        print("FAIL: Calmar < 1.0")
        gates_passed = False
    if max_dd_pct < -25.0: # max_dd_pct is negative
        print("FAIL: MaxDD > 25%")
        gates_passed = False
    if expectancy <= 0:
        print("FAIL: Expectancy <= 0")
        gates_passed = False

    if gates_passed:
        print("PASS: Strategy meets all defined risk gates.")
    else:
        print("FAIL: Strategy failed one or more risk gates.")

    # Plotting
    plt.figure(figsize=(12, 6))
    plt.plot(trades['exit_date'], trades['cum_gross_pnl_close'], label='Gross P&L', color='blue', alpha=0.5)
    plt.plot(trades['exit_date'], trades['cum_net_pnl_close'], label='Net P&L (SL Close)', color='red')
    plt.plot(trades['exit_date'], trades['cum_net_pnl_high'], label='Net P&L (SL High Proxy)', color='orange', linestyle='--')
    plt.title('VRP Short Volatility Equity Curve')
    plt.xlabel('Date')
    plt.ylabel('P&L (₹)')
    plt.legend()
    plt.grid(True)
    plt.savefig('/app/VRP_ShortVol_BT/equity_curve.png')
    print("\nEquity curve saved to /app/VRP_ShortVol_BT/equity_curve.png")

if __name__ == "__main__":
    import os
    if os.path.exists('/app/VRP_ShortVol_BT/trades.csv'):
        df = pd.read_csv('/app/VRP_ShortVol_BT/trades.csv')
        df['entry_date'] = pd.to_datetime(df['entry_date'])
        df['exit_date'] = pd.to_datetime(df['exit_date'])
        df['expiry'] = pd.to_datetime(df['expiry'])
        generate_report(df)
    else:
        print("Run backtest first.")
