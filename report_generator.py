import pandas as pd
import matplotlib.pyplot as plt
import os

class ReportGenerator:
    def __init__(self, results, all_trades, out_dir="reports"):
        self.results = results
        self.all_trades = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()
        self.out_dir = out_dir
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)

    def generate_all(self):
        self.generate_trade_log()
        self.generate_summary_rankings()
        self.generate_equity_curves()
        self.generate_html_report()

    def generate_trade_log(self):
        if not self.all_trades.empty:
            path = os.path.join(self.out_dir, "trade_log.csv")
            self.all_trades.to_csv(path, index=False)
            print(f"Trade log saved to {path}")

    def generate_summary_rankings(self):
        rankings = []
        for r in self.results:
            rankings.append({
                'Instrument': r['instrument'],
                'Strategy': r['strategy'],
                'IS_Sharpe': r['is_metrics'].get('Sharpe Ratio', 0),
                'OOS_Sharpe': r['oos_metrics'].get('Sharpe Ratio', 0),
                'Warning': r['warning']
            })

        df = pd.DataFrame(rankings)
        if df.empty:
            return

        df = df.sort_values(by='OOS_Sharpe', ascending=False).reset_index(drop=True)

        path = os.path.join(self.out_dir, "summary.txt")
        with open(path, "w") as f:
            f.write("=== SUMMARY RANKINGS (By OOS Sharpe Ratio) ===\n\n")
            f.write(df.to_string())
            f.write("\n\n=== TOP 3 RECOMMENDATIONS ===\n")
            for i, row in df.head(3).iterrows():
                f.write(f"{i+1}. {row['Strategy']} on {row['Instrument']} (OOS Sharpe: {row['OOS_Sharpe']})\n")
                if row['Warning']:
                    f.write("   *WARNING: Significant degradation in Out-of-Sample performance. Potential overfit.\n")

        print(df.to_string())
        print(f"Summary rankings saved to {path}")

    def generate_equity_curves(self):
        if self.all_trades.empty:
            return

        instruments = self.all_trades['instrument'].unique()
        fig, axes = plt.subplots(len(instruments), 1, figsize=(12, 6 * len(instruments)))

        if len(instruments) == 1:
            axes = [axes]

        for i, inst in enumerate(instruments):
            ax = axes[i]
            inst_trades = self.all_trades[self.all_trades['instrument'] == inst]

            for strat in inst_trades['strategy'].unique():
                strat_trades = inst_trades[inst_trades['strategy'] == strat].copy()
                if not strat_trades.empty:
                    strat_trades['date'] = pd.to_datetime(strat_trades['exit_date'])
                    strat_trades = strat_trades.sort_values('date')
                    strat_trades['cum_pnl'] = strat_trades['pnl'].cumsum()
                    ax.plot(strat_trades['date'], strat_trades['cum_pnl'], label=strat)

            ax.set_title(f"Equity Curves for {inst} (OOS)")
            ax.set_xlabel("Date")
            ax.set_ylabel("Cumulative PnL (INR)")
            ax.legend()
            ax.grid(True)

        plt.tight_layout()
        path = os.path.join(self.out_dir, "equity_curves.png")
        plt.savefig(path)
        plt.close()
        print(f"Equity curves saved to {path}")

    def generate_html_report(self):
        html = """
        <html>
        <head><title>Backtest Report</title></head>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }
            th { background-color: #f2f2f2; text-align: center; }
            h2 { color: #333; }
            .warning { color: red; font-weight: bold; }
        </style>
        <body>
            <h1>Walk-Forward Backtest Performance Report</h1>
        """

        for r in self.results:
            html += f"<h2>{r['strategy']} on {r['instrument']}</h2>"
            if r['warning']:
                html += "<p class='warning'>WARNING: OOS performance degraded >50% vs IS. Potential Overfit.</p>"

            html += f"<p><b>Best Parameters:</b> {r['best_params']}</p>"

            html += "<table>"
            html += "<tr><th>Metric</th><th>In-Sample (IS)</th><th>Out-of-Sample (OOS)</th></tr>"

            for key in r['is_metrics'].keys():
                is_val = r['is_metrics'][key]
                oos_val = r['oos_metrics'].get(key, 0)
                html += f"<tr><td>{key}</td><td>{is_val}</td><td>{oos_val}</td></tr>"

            html += "</table>"

        html += "</body></html>"

        path = os.path.join(self.out_dir, "backtest_report.html")
        with open(path, "w") as f:
            f.write(html)

        print(f"HTML Report saved to {path}")
