import pandas as pd
import numpy as np
import yaml
from tabulate import tabulate
from backtest import run_backtest
from report import get_max_losing_streak
import matplotlib.pyplot as plt

def generate_metrics(trades, capital):
    if trades.empty:
        return {
            'Trades': 0, 'Net P&L (High)': 0, 'CAGR (%)': 0, 'Win%': 0,
            'R:R': 0, 'Expectancy': 0, 'MaxDD (₹)': 0, 'MaxDD (%)': 0, 'Calmar': 0,
            'Worst Trade': 0
        }

    trades = trades.copy()
    trades['cum_net_pnl_high'] = trades['net_pnl_high'].cumsum()
    trades['equity'] = capital + trades['cum_net_pnl_high']

    total_trades = len(trades)
    wins = trades[trades['net_pnl_high'] > 0]
    losses = trades[trades['net_pnl_high'] <= 0]

    win_pct = len(wins) / total_trades if total_trades > 0 else 0
    avg_win = wins['net_pnl_high'].mean() if not wins.empty else 0
    avg_loss = losses['net_pnl_high'].mean() if not losses.empty else 0

    reward_risk = abs(avg_win / avg_loss) if avg_loss != 0 else np.inf
    expectancy = (win_pct * avg_win) - ((1 - win_pct) * abs(avg_loss))

    trades['peak'] = trades['equity'].cummax()
    trades['drawdown'] = trades['equity'] - trades['peak']
    max_dd_rupee = trades['drawdown'].min()
    max_dd_pct = (max_dd_rupee / capital) * 100

    days = (trades['exit_date'].max() - trades['entry_date'].min()).days
    years = days / 365.25 if days > 0 else 0
    total_return = trades['cum_net_pnl_high'].iloc[-1] / capital
    cagr = ((1 + total_return) ** (1 / years) - 1) * 100 if years > 0 else 0

    calmar = cagr / abs(max_dd_pct) if max_dd_pct != 0 else np.inf
    worst_trade = trades['net_pnl_high'].min()

    return {
        'Trades': total_trades,
        'Net P&L (High)': round(trades['cum_net_pnl_high'].iloc[-1], 2),
        'CAGR (%)': round(cagr, 2),
        'Win%': round(win_pct * 100, 2),
        'R:R': round(reward_risk, 2),
        'Expectancy': round(expectancy, 2),
        'MaxDD (₹)': round(max_dd_rupee, 2),
        'MaxDD (%)': round(max_dd_pct, 2),
        'Calmar': round(calmar, 2),
        'Worst Trade': round(worst_trade, 2)
    }

def run_sweep():
    with open('/app/VRP_ShortVol_BT/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    capital = config['capital']
    thresholds = [0, 50, 60, 70, 80]
    results = []

    all_trades = {}

    print("Running Volatility-Regime Sweep...")

    plt.figure(figsize=(12, 6))

    for t in thresholds:
        print(f"Running for IVP Threshold: {t}...")
        df_trades = run_backtest(ivp_threshold=t)
        all_trades[t] = df_trades

        metrics = generate_metrics(df_trades, capital)

        # Gates Evaluation
        calmar = metrics['Calmar']
        max_dd = metrics['MaxDD (%)']
        exp = metrics['Expectancy']
        trades_cnt = metrics['Trades']

        verdict = "PASS"
        reasons = []
        if trades_cnt < 30:
            verdict = "FAIL"
            reasons.append("Too Few Trades")
        if calmar < 1.0:
            verdict = "FAIL"
            reasons.append("Calmar<1.0")
        if max_dd < -25.0:
            verdict = "FAIL"
            reasons.append("MaxDD>25%")
        if exp <= 0:
            verdict = "FAIL"
            reasons.append("Exp<=0")

        metrics['Threshold'] = t
        metrics['Verdict'] = verdict
        metrics['Fails'] = ", ".join(reasons) if reasons else "-"

        results.append(metrics)

        if not df_trades.empty:
            df_trades['cum_net_pnl_high'] = df_trades['net_pnl_high'].cumsum()
            plt.plot(df_trades['exit_date'], df_trades['cum_net_pnl_high'], label=f"IVP > {t}")

    df_results = pd.DataFrame(results)
    cols = ['Threshold', 'Trades', 'Net P&L (High)', 'CAGR (%)', 'Win%', 'R:R', 'Expectancy', 'MaxDD (%)', 'Calmar', 'Worst Trade', 'Verdict', 'Fails']

    print("\n" + "="*80)
    print("VRP SHORT VOLATILITY: IV-REGIME SWEEP (SL-HIGH PROXY)")
    print("="*80)
    print(tabulate(df_results[cols], headers="keys", tablefmt="pretty", showindex=False))

    print("\n--- BLUNT VERDICT ---")
    best = df_results[df_results['Verdict'] == 'PASS']
    if best.empty:
        print("FAIL: Even the best threshold fails the gates or has too few trades to be meaningful.")
        print("Conclusion: Shorting vol blindly is terrible, and filtering for rich IV still isn't enough to survive the brutal tail risk and slippage in NIFTY options over 5.5 years.")
    else:
        print("PASS: We found a survivable regime!")
        print(tabulate(best[cols], headers="keys", tablefmt="pretty", showindex=False))

    plt.title('VRP Short Volatility - IV Regime Sweep (SL-High Proxy Net P&L)')
    plt.xlabel('Date')
    plt.ylabel('P&L (₹)')
    plt.legend()
    plt.grid(True)
    plt.savefig('/app/VRP_ShortVol_BT/sweep_equity.png')

    # Save the baseline trades (0 threshold) to CSV
    all_trades[0].to_csv('/app/VRP_ShortVol_BT/trades.csv', index=False)

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore')
    run_sweep()
