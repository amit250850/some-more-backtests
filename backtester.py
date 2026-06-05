import pandas as pd
import numpy as np
from utils import get_lot_size, calculate_costs, black_scholes_call, black_scholes_put

class VectorizedBacktester:
    def __init__(self, instrument, strategy_name, params):
        self.instrument = instrument
        self.strategy_name = strategy_name
        self.params = params
        self.capital = 100000
        self.trades = []

    def run_backtest(self, signals_df):
        df = signals_df.copy()

        is_options = "NIFTY" in self.instrument
        lot_size = get_lot_size(self.instrument)

        in_position = False
        position_type = 0 # 1 long, -1 short
        entry_price = 0
        entry_idx = 0
        entry_date = None
        option_entry_price = 0

        stop_loss_pct = self.params.get('stop_loss', 0.01)
        hold_bars = self.params.get('hold_bars', 6)

        if 'Strategy3' in self.strategy_name:
            atr_multiplier = self.params.get('atr_multiplier', 2.0)
            hold_bars = 8

        if 'Strategy4' in self.strategy_name:
            opt_exit_pct = self.params.get('opt_exit_pct', 0.20)
            opt_stop_pct = 0.30

        for row in df.itertuples():
            idx = row.Index

            if in_position:
                bars_held = idx - entry_idx
                exit_price = None
                exit_reason = None

                if is_options:
                    if position_type == 1:
                        current_opt_price = black_scholes_call(row.close, entry_price, 7/365, 0.05, 0.15)
                    else:
                        current_opt_price = black_scholes_put(row.close, entry_price, 7/365, 0.05, 0.15)

                    opt_ret = (current_opt_price - option_entry_price) / option_entry_price if option_entry_price > 0 else 0

                    if 'Strategy4' in self.strategy_name:
                        if opt_ret >= opt_exit_pct:
                            exit_price = current_opt_price
                            exit_reason = "Take Profit"
                        elif opt_ret <= -opt_stop_pct:
                            exit_price = current_opt_price
                            exit_reason = "Stop Loss"
                    else:
                        if bars_held >= hold_bars:
                            exit_price = current_opt_price
                            exit_reason = "Time Stop"
                else:
                    if position_type == 1:
                        ret = (row.low - entry_price) / entry_price
                        if ret <= -stop_loss_pct:
                            exit_price = entry_price * (1 - stop_loss_pct)
                            exit_reason = "Stop Loss"
                        elif 'Strategy3' in self.strategy_name:
                            trail_stop = entry_price - (atr_multiplier * getattr(row, 'atr', 0))
                            if row.low < trail_stop:
                                exit_price = trail_stop
                                exit_reason = "Trailing Stop"
                        elif 'Strategy5' in self.strategy_name:
                            if row.high >= getattr(row, 'vwap', 0):
                                exit_price = getattr(row, 'vwap', row.close)
                                exit_reason = "VWAP Target"

                    elif position_type == -1:
                        ret = (entry_price - row.high) / entry_price
                        if ret <= -stop_loss_pct:
                            exit_price = entry_price * (1 + stop_loss_pct)
                            exit_reason = "Stop Loss"
                        elif 'Strategy3' in self.strategy_name:
                            trail_stop = entry_price + (atr_multiplier * getattr(row, 'atr', 0))
                            if row.high > trail_stop:
                                exit_price = trail_stop
                                exit_reason = "Trailing Stop"
                        elif 'Strategy5' in self.strategy_name:
                            if row.low <= getattr(row, 'vwap', 0):
                                exit_price = getattr(row, 'vwap', row.close)
                                exit_reason = "VWAP Target"

                    if exit_price is None:
                        dyn_hold = getattr(row, 'bucket_bars', hold_bars) if 'Strategy2' in self.strategy_name else hold_bars
                        if bars_held >= dyn_hold:
                            exit_price = row.close
                            exit_reason = "Time Stop"

                if exit_price is not None:
                    if is_options:
                        trade_val_entry = option_entry_price * lot_size
                        trade_val_exit = exit_price * lot_size
                        costs = calculate_costs(trade_val_entry, trade_val_exit)
                        pnl = (exit_price - option_entry_price) * lot_size - costs
                        ret_pct = pnl / trade_val_entry if trade_val_entry > 0 else 0
                    else:
                        trade_val_entry = entry_price * lot_size
                        trade_val_exit = exit_price * lot_size
                        costs = calculate_costs(trade_val_entry, trade_val_exit)
                        if position_type == 1:
                            pnl = (exit_price - entry_price) * lot_size - costs
                        else:
                            pnl = (entry_price - exit_price) * lot_size - costs
                        ret_pct = pnl / (entry_price * lot_size)

                    self.trades.append({
                        'instrument': self.instrument,
                        'strategy': self.strategy_name,
                        'entry_date': entry_date,
                        'exit_date': row.date,
                        'direction': 'Long' if position_type == 1 else 'Short',
                        'entry_price': option_entry_price if is_options else entry_price,
                        'exit_price': exit_price,
                        'exit_reason': exit_reason,
                        'pnl': pnl,
                        'pnl_pct': ret_pct * 100,
                        'hold_bars': bars_held
                    })

                    in_position = False
                    position_type = 0

            if not in_position and row.signal != 0:
                entry_target = getattr(row, 'entry_price', row.close)
                if pd.isna(entry_target):
                    continue

                in_position = True
                position_type = row.signal
                entry_idx = idx
                entry_date = row.date
                entry_price = entry_target

                if is_options:
                    if position_type == 1:
                        option_entry_price = black_scholes_call(entry_price, entry_price, 7/365, 0.05, 0.15)
                    else:
                        option_entry_price = black_scholes_put(entry_price, entry_price, 7/365, 0.05, 0.15)

        return pd.DataFrame(self.trades)

    def calculate_metrics(self):
        trades_df = pd.DataFrame(self.trades)
        if trades_df.empty:
            return {
                'Total Return %': 0, 'CAGR %': 0, 'Sharpe Ratio': 0,
                'Max Drawdown %': 0, 'Win Rate %': 0, 'Profit Factor': 0,
                'Total Trades': 0, 'Avg Win / Avg Loss': 0
            }

        trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()
        trades_df['equity'] = self.capital + trades_df['cumulative_pnl']

        total_return_pct = (trades_df['equity'].iloc[-1] - self.capital) / self.capital * 100

        years = 60 / 365
        cagr = ((trades_df['equity'].iloc[-1] / self.capital) ** (1/years) - 1) * 100 if years > 0 else 0

        trades_df['peak'] = trades_df['equity'].cummax()
        trades_df['drawdown'] = (trades_df['equity'] - trades_df['peak']) / trades_df['peak'] * 100
        max_dd = trades_df['drawdown'].min()

        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] <= 0]
        win_rate = len(wins) / len(trades_df) * 100

        gross_profit = wins['pnl'].sum()
        gross_loss = abs(losses['pnl'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')

        avg_win = wins['pnl'].mean() if not wins.empty else 0
        avg_loss = abs(losses['pnl'].mean()) if not losses.empty else 0
        avg_win_loss = avg_win / avg_loss if avg_loss != 0 else float('inf')

        daily_pnl = trades_df.groupby(trades_df['exit_date'].dt.date)['pnl'].sum()
        daily_ret = daily_pnl / self.capital
        sharpe = (daily_ret.mean() / daily_ret.std()) * np.sqrt(252) if daily_ret.std() != 0 else 0

        return {
            'Total Return %': round(total_return_pct, 2),
            'CAGR %': round(cagr, 2),
            'Sharpe Ratio': round(sharpe, 2),
            'Max Drawdown %': round(max_dd, 2),
            'Win Rate %': round(win_rate, 2),
            'Profit Factor': round(profit_factor, 2),
            'Total Trades': len(trades_df),
            'Avg Win / Avg Loss': round(avg_win_loss, 2)
        }
