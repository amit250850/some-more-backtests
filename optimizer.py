import itertools
import pandas as pd
from typing import Dict, List, Type
from strategies import BaseStrategy
from backtester import VectorizedBacktester

class WalkForwardOptimizer:
    def __init__(self, data: pd.DataFrame, strategy_class: Type[BaseStrategy], param_grid: Dict[str, List], instrument: str, extra_data: pd.DataFrame = None):
        self.data = data
        self.strategy_class = strategy_class
        self.param_grid = param_grid
        self.instrument = instrument
        self.extra_data = extra_data

        # Split 70% IS, 30% OOS
        split_idx = int(len(data) * 0.7)
        self.is_data = data.iloc[:split_idx].copy()
        self.oos_data = data.iloc[split_idx:].copy()

    def optimize(self):
        keys, values = zip(*self.param_grid.items())
        combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

        best_params = None
        best_sharpe = -float('inf')
        best_is_metrics = None

        print(f"Optimizing {self.strategy_class.__name__} for {self.instrument} with {len(combinations)} combinations...")

        for params in combinations:
            strat = self.strategy_class(self.is_data, params, self.extra_data)
            signals = strat.generate_signals()

            bt = VectorizedBacktester(self.instrument, self.strategy_class.__name__, params)
            bt.run_backtest(signals)
            metrics = bt.calculate_metrics()

            if metrics['Sharpe Ratio'] > best_sharpe:
                best_sharpe = metrics['Sharpe Ratio']
                best_params = params
                best_is_metrics = metrics

        if best_params is None:
            best_params = combinations[0]
            best_is_metrics = {'Sharpe Ratio': 0, 'Total Trades': 0}

        # Run OOS with best params
        strat_oos = self.strategy_class(self.oos_data, best_params, self.extra_data)
        signals_oos = strat_oos.generate_signals()

        bt_oos = VectorizedBacktester(self.instrument, self.strategy_class.__name__, best_params)
        trades_oos = bt_oos.run_backtest(signals_oos)
        oos_metrics = bt_oos.calculate_metrics()

        warning = False
        if best_is_metrics['Sharpe Ratio'] > 0 and oos_metrics['Sharpe Ratio'] < best_is_metrics['Sharpe Ratio'] * 0.5:
            warning = True

        return {
            'best_params': best_params,
            'is_metrics': best_is_metrics,
            'oos_metrics': oos_metrics,
            'oos_trades': trades_oos,
            'warning': warning
        }
