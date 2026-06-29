import pandas as pd
import numpy as np
import glob
import os
import warnings
warnings.filterwarnings('ignore')

def run_kill_test():
    # Use relative paths
    bhav_files = glob.glob('./VRP_ShortVol_BT/data/bhavcopy_*.parquet')
    if not bhav_files:
        print("No bhavcopy files found in ./VRP_ShortVol_BT/data/.")
        return

    dfs = [pd.read_parquet(f) for f in bhav_files]
    df = pd.concat(dfs, ignore_index=True)
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values('date', inplace=True)
    dates = sorted(df['date'].unique())

    spot = pd.read_parquet('./VRP_ShortVol_BT/data/nifty_spot.parquet')
    spot['date'] = pd.to_datetime(spot['date'])
    spot.sort_values('date', inplace=True)
    spot.set_index('date', inplace=True)
    spot['ema10'] = spot['close'].ewm(span=10, adjust=False).mean()

    results = []

    print("Starting kill-test evaluation over", len(dates) - 1, "days...")

    for i in range(len(dates) - 1):
        t_date = dates[i]
        t1_date = dates[i+1]

        df_t = df[df['date'] == t_date]
        df_t1 = df[df['date'] == t1_date]

        opt_t = df_t[(df_t['symbol'] == 'NIFTY') & (df_t['instrument'].isin(['OPTIDX', 'OPT']))]
        fut_t = df_t[(df_t['symbol'] == 'NIFTY') & (df_t['instrument'].isin(['FUTIDX', 'FUT']))]

        if opt_t.empty or fut_t.empty:
            print(f"Skipping {t_date.date()}: Missing NIFTY options or futures data")
            continue

        # Option expiry
        expiries = sorted(opt_t['expiry'].unique())
        future_expiries = [e for e in expiries if e >= t_date]
        if not future_expiries:
            print(f"Skipping {t_date.date()}: No future expiries found")
            continue

        # Use nearest WEEKLY expiry as per specs
        nearest_opt_exp = future_expiries[0]

        if nearest_opt_exp == t_date:
            print(f"Skipping {t_date.date()}: Today is expiry day")
            continue

        opt_chain = opt_t[opt_t['expiry'] == nearest_opt_exp]

        # S and R
        puts = opt_chain[opt_chain['opt_type'] == 'PE']
        calls = opt_chain[opt_chain['opt_type'] == 'CE']

        if puts.empty or calls.empty:
            print(f"Skipping {t_date.date()}: Missing puts or calls in the chain")
            continue

        # Check for thin-OI (degenerate chain)
        if puts['oi'].sum() == 0 or calls['oi'].sum() == 0:
            print(f"Skipping {t_date.date()}: Thin-OI / degenerate chain (OI sum is 0)")
            continue

        S = puts.loc[puts['oi'].idxmax(), 'strike']
        R = calls.loc[calls['oi'].idxmax(), 'strike']

        if pd.isna(S) or pd.isna(R):
            print(f"Skipping {t_date.date()}: S or R is NaN")
            continue

        if S >= R:
            print(f"Skipping {t_date.date()}: S ({S}) >= R ({R})")
            continue

        # Future close T
        fut_expiries = sorted(fut_t['expiry'].unique())
        future_fut_expiries = [e for e in fut_expiries if e >= t_date]
        if not future_fut_expiries:
            print(f"Skipping {t_date.date()}: No future expiries for futures")
            continue

        nearest_fut_exp = future_fut_expiries[0]

        fut_chain = fut_t[fut_t['expiry'] == nearest_fut_exp]
        if fut_chain.empty:
            continue

        close_T = fut_chain['close'].iloc[0]

        # Future T+1
        fut_t1 = df_t1[(df_t1['symbol'] == 'NIFTY') & (df_t1['instrument'].isin(['FUTIDX', 'FUT'])) & (df_t1['expiry'] == nearest_fut_exp)]
        if fut_t1.empty:
            print(f"Skipping {t_date.date()}: Missing future data for T+1")
            continue

        open_T1 = fut_t1['open'].iloc[0]
        close_T1 = fut_t1['close'].iloc[0]

        spot_close_T = spot.loc[t_date, 'close'] if t_date in spot.index else np.nan
        ema10_T = spot.loc[t_date, 'ema10'] if t_date in spot.index else np.nan

        results.append({
            'date': t_date,
            'close_T': close_T,
            'open_T1': open_T1,
            'close_T1': close_T1,
            'spot_close_T': spot_close_T,
            'ema10_T': ema10_T,
            'S': S,
            'R': R
        })

    df_res = pd.DataFrame(results)
    if df_res.empty:
        print("No valid days found.")
        return

    df_res['dist_S'] = abs(df_res['close_T'] - df_res['S']) / df_res['close_T']
    df_res['dist_R'] = abs(df_res['close_T'] - df_res['R']) / df_res['close_T']

    CAPITAL = 100000
    LOT_SIZE = 50
    COST_PTS = (40.0 / LOT_SIZE) + 4.0

    def evaluate_signals(signals, name):
        trades = df_res[signals != 0].copy()
        trades['signal'] = signals[signals != 0]

        if trades.empty:
            return {
                'Variant': name,
                'Trades': 0,
                'Net Exp (INR)': 0,
                'MaxDD %': 0,
                'Calmar': 0,
                'Verdict': 'INCONCLUSIVE (sample < 40)'
            }

        trades['pnl_pts'] = np.where(trades['signal'] == 1,
                                     trades['close_T1'] - trades['open_T1'] - COST_PTS,
                                     trades['open_T1'] - trades['close_T1'] - COST_PTS)
        trades['pnl_inr'] = trades['pnl_pts'] * LOT_SIZE

        total_trades = len(trades)
        net_exp = trades['pnl_inr'].mean()

        trades['cum_pnl'] = trades['pnl_inr'].cumsum()
        trades['peak'] = trades['cum_pnl'].cummax()
        trades['drawdown'] = trades['peak'] - trades['cum_pnl']
        max_dd_inr = trades['drawdown'].max()
        max_dd_pct = (max_dd_inr / CAPITAL) * 100

        total_pnl = trades['pnl_inr'].sum()
        days_in_test = (df_res['date'].max() - df_res['date'].min()).days
        if days_in_test == 0:
            days_in_test = 1
        annualized_ret = (total_pnl / CAPITAL) * (365 / days_in_test)

        calmar = annualized_ret / (max_dd_pct / 100) if max_dd_pct > 0 else np.inf

        fails = []
        if net_exp <= 0: fails.append("net expectancy <= 0")
        if calmar < 1.0: fails.append("Calmar < 1.0")
        if max_dd_pct > 25: fails.append("MaxDD > 25%")

        if total_trades < 40:
            verdict = "INCONCLUSIVE (sample < 40)"
        elif fails:
            verdict = "FAIL (" + ", ".join(fails) + ")"
        else:
            verdict = "PASS"

        return {
            'Variant': name,
            'Trades': total_trades,
            'Net Exp (INR)': round(net_exp, 2),
            'MaxDD %': round(max_dd_pct, 2),
            'Calmar': round(calmar, 2),
            'Verdict': verdict
        }

    out = []

    # Generate signals for BASE to compare against EMA
    base_signals_dict = {}

    # 1. BASE
    for k in [0.003, 0.005, 0.010]:
        l_cond = df_res['dist_S'] <= k
        s_cond = df_res['dist_R'] <= k
        signals = pd.Series(0, index=df_res.index)
        signals[l_cond & ~s_cond] = 1
        signals[s_cond & ~l_cond] = -1
        out.append(evaluate_signals(signals, f"BASE (k={k*100}%)"))
        base_signals_dict[k] = signals

    filter_removed_info = []

    # 2. EMA10 FILTER
    for k in [0.003, 0.005, 0.010]:
        l_cond = (df_res['dist_S'] <= k) & (df_res['spot_close_T'] > df_res['ema10_T'])
        s_cond = (df_res['dist_R'] <= k) & (df_res['spot_close_T'] < df_res['ema10_T'])
        signals = pd.Series(0, index=df_res.index)
        signals[l_cond & ~s_cond] = 1
        signals[s_cond & ~l_cond] = -1

        # Calculate how many signals were removed
        base_sigs = base_signals_dict[k]
        base_trades = (base_sigs != 0).sum()
        ema_trades = (signals != 0).sum()
        removed = base_trades - ema_trades
        filter_removed_info.append(f"- For k={k*100}%, the EMA10 filter removed {removed} signals.")

        out.append(evaluate_signals(signals, f"EMA10 FILTER (k={k*100}%)"))

    # 3. BREAKOUT
    l_brk = df_res['close_T'] > df_res['R']
    s_brk = df_res['close_T'] < df_res['S']
    signals_brk = pd.Series(0, index=df_res.index)
    signals_brk[l_brk & ~s_brk] = 1
    signals_brk[s_brk & ~l_brk] = -1
    out.append(evaluate_signals(signals_brk, "BREAKOUT"))

    res_df = pd.DataFrame(out)

    md_content = "\n## Kill-Test Results: OI-Wall Mean Reversion (Candidate #21)\n\n"
    md_content += res_df.to_markdown(index=False)
    md_content += "\n\n### Additional Information:\n"
    for info in filter_removed_info:
        md_content += info + "\n"
    md_content += "\n**Note**: Test run on limited bhavcopy data loaded in session.\n"

    with open('./STRATEGY_RESULTS.md', 'a') as f:
        f.write(md_content)

    print("\nKill-test completed and results appended to ./STRATEGY_RESULTS.md")

if __name__ == '__main__':
    run_kill_test()
