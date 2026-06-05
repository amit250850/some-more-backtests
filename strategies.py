import pandas as pd
import numpy as np
from typing import Dict

class BaseStrategy:
    def __init__(self, data: pd.DataFrame, params: Dict, extra_data: pd.DataFrame = None):
        self.data = data.copy()
        self.params = params
        self.extra_data = extra_data
        self.signals = pd.DataFrame(index=self.data.index)

    def generate_signals(self) -> pd.DataFrame:
        raise NotImplementedError

class Strategy1_SUVMomentum(BaseStrategy):
    """
    Strategy 1: SUV (Standardized Unexpected Volume) Momentum
    - Regress volume on abs(returns) for rolling 20-bar window
    - SUV = (actual_volume - expected_volume) / std(residuals)
    - Signal: SUV > 2.0 AND price breaks above/below VWAP
    """
    def generate_signals(self) -> pd.DataFrame:
        df = self.data
        window = 20
        suv_threshold = self.params.get('suv_threshold', 2.0)

        df['returns'] = df['close'].pct_change()
        df['abs_returns'] = df['returns'].abs()

        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['cum_vol'] = df['volume'].cumsum()
        df['cum_vol_price'] = (df['typical_price'] * df['volume']).cumsum()
        df['vwap'] = df['cum_vol_price'] / df['cum_vol']

        roll_x = df['abs_returns'].rolling(window)
        roll_y = df['volume'].rolling(window)

        cov_xy = roll_x.cov(df['volume'])
        var_x = roll_x.var()

        beta = cov_xy / var_x
        alpha = roll_y.mean() - beta * roll_x.mean()

        df['expected_volume'] = alpha + beta * df['abs_returns']
        df['residuals'] = df['volume'] - df['expected_volume']

        std_residuals = df['residuals'].rolling(window).std()
        df['SUV'] = df['residuals'] / std_residuals

        df['signal'] = 0

        long_cond = (df['SUV'] > suv_threshold) & (df['close'] > df['vwap']) & (df['close'].shift(1) <= df['vwap'].shift(1))
        short_cond = (df['SUV'] > suv_threshold) & (df['close'] < df['vwap']) & (df['close'].shift(1) >= df['vwap'].shift(1))

        df.loc[long_cond, 'signal'] = 1
        df.loc[short_cond, 'signal'] = -1

        self.signals = df[['date', 'open', 'high', 'low', 'close', 'volume', 'signal']].copy()
        self.signals['entry_price'] = self.signals['open'].shift(-1)

        return self.signals

class Strategy6_SilverCOMEXBreakout(BaseStrategy):
    """
    Strategy 6: SILVERM 15-min COMEX breakout
    - First 2 candles after 5:30 PM (17:30 and 17:45) establish range.
    - Breakout of range = entry (Wait for candle close outside range to avoid fakeouts, entry next bar open).
    - Volume filter: breakout candle volume > 20-period moving average.
    - Exit: 1.5 R:R, or Time Stop at 10:30 PM (22:30).
    """
    def generate_signals(self) -> pd.DataFrame:
        df = self.data

        # Calculate 20-period volume MA
        df['vol_ma20'] = df['volume'].rolling(20).mean()

        # Identify COMEX Open Range (17:30 to 18:00)
        # We need the highest high and lowest low between 17:30 and 18:00
        df['time'] = df['date'].dt.time

        # Initialize range columns
        df['comex_high'] = np.nan
        df['comex_low'] = np.nan
        df['in_comex_range_setup'] = False

        # Helper to get the day
        df['date_only'] = df['date'].dt.date

        # Group by day to find the range
        daily_ranges = {}
        for day, group in df.groupby('date_only'):
            # The candles representing the first 30 mins: 17:30 and 17:45
            setup_candles = group[(group['time'] >= pd.to_datetime('17:30:00').time()) &
                                  (group['time'] <= pd.to_datetime('17:45:00').time())]

            if not setup_candles.empty:
                daily_ranges[day] = {
                    'high': setup_candles['high'].max(),
                    'low': setup_candles['low'].min()
                }

        # Map back to main dataframe
        df['comex_high'] = df['date_only'].map(lambda x: daily_ranges.get(x, {}).get('high', np.nan))
        df['comex_low'] = df['date_only'].map(lambda x: daily_ranges.get(x, {}).get('low', np.nan))

        df['signal'] = 0
        df['exit_time'] = pd.to_datetime('22:30:00').time()

        # Conditions for breakout
        # 1. Time must be AFTER 18:00 (since 17:30-18:00 forms the range)
        # 2. Time must be BEFORE 22:30 (don't enter right before exit)
        time_cond = (df['time'] > pd.to_datetime('17:45:00').time()) & (df['time'] < pd.to_datetime('22:30:00').time())

        # 3. Volume > 20MA
        vol_cond = df['volume'] > df['vol_ma20']

        # 4. Breakout: We enter if the current candle CLOSES outside the range
        # (This prevents massive wicks from falsely triggering)
        long_cond = time_cond & vol_cond & (df['close'] > df['comex_high']) & (df['close'].shift(1) <= df['comex_high'])
        short_cond = time_cond & vol_cond & (df['close'] < df['comex_low']) & (df['close'].shift(1) >= df['comex_low'])

        df.loc[long_cond, 'signal'] = 1
        df.loc[short_cond, 'signal'] = -1

        # We only want to trigger the FIRST breakout of the day to avoid overtrading chop
        # Use transform to maintain identical index
        df['signal_cum'] = df.groupby('date_only')['signal'].transform(lambda x: x.abs().cumsum())
        df.loc[df['signal_cum'] > 1, 'signal'] = 0

        self.signals = df[['date', 'open', 'high', 'low', 'close', 'volume', 'comex_high', 'comex_low', 'signal']].copy()

        # Since we use R:R, we need to pass the Stop Loss level to the backtester
        # Stop loss for Long is the comex_low (the bottom of the range)
        # Stop loss for Short is the comex_high (the top of the range)
        self.signals['sl_price'] = np.where(self.signals['signal'] == 1, self.signals['comex_low'],
                                   np.where(self.signals['signal'] == -1, self.signals['comex_high'], np.nan))

        self.signals['entry_price'] = self.signals['open'].shift(-1)

        return self.signals

class Strategy2_VPIN(BaseStrategy):
    """
    Strategy 2: VPIN Approximation (Order Flow Toxicity)
    """
    def generate_signals(self) -> pd.DataFrame:
        df = self.data
        vpin_threshold = self.params.get('vpin_threshold', 0.6)
        bucket_divisor = self.params.get('bucket_divisor', 50)

        df['buy_vol'] = 0.0
        df['sell_vol'] = 0.0

        buy_cond = df['close'] > df['open']
        sell_cond = df['close'] < df['open']
        flat_cond = df['close'] == df['open']

        df.loc[buy_cond, 'buy_vol'] = df.loc[buy_cond, 'volume']
        df.loc[sell_cond, 'sell_vol'] = df.loc[sell_cond, 'volume']
        df.loc[flat_cond, 'buy_vol'] = df.loc[flat_cond, 'volume'] / 2
        df.loc[flat_cond, 'sell_vol'] = df.loc[flat_cond, 'volume'] / 2

        daily_vol = df['volume'].rolling(75 * 20).sum() / 20
        daily_vol = daily_vol.bfill()

        bucket_size = daily_vol / bucket_divisor

        avg_bar_vol = df['volume'].rolling(75 * 20).mean().bfill()
        bars_per_bucket = (bucket_size / avg_bar_vol).fillna(1).astype(int).clip(lower=1)

        median_bars = max(1, int(bars_per_bucket.median()))

        df['bucket_buy_vol'] = df['buy_vol'].rolling(median_bars).sum()
        df['bucket_sell_vol'] = df['sell_vol'].rolling(median_bars).sum()
        df['bucket_total_vol'] = df['volume'].rolling(median_bars).sum()

        df['bucket_vpin'] = (df['bucket_buy_vol'] - df['bucket_sell_vol']).abs() / df['bucket_total_vol']

        window_10_buckets = median_bars * 10
        df['VPIN'] = df['bucket_vpin'].rolling(window_10_buckets).mean()

        df['momentum'] = df['close'] - df['close'].shift(median_bars)

        df['signal'] = 0

        long_cond = (df['VPIN'] > vpin_threshold) & (df['bucket_buy_vol'] > df['bucket_sell_vol']) & (df['momentum'] > 0)
        short_cond = (df['VPIN'] > vpin_threshold) & (df['bucket_sell_vol'] > df['bucket_buy_vol']) & (df['momentum'] < 0)

        df.loc[long_cond, 'signal'] = 1
        df.loc[short_cond, 'signal'] = -1

        self.signals = df[['date', 'open', 'high', 'low', 'close', 'volume', 'signal']].copy()
        self.signals['entry_price'] = self.signals['open'].shift(-1)
        self.signals['bucket_bars'] = median_bars

        return self.signals

class Strategy3_VolumeSpike(BaseStrategy):
    """
    Strategy 3: Volume Spike + Level Break
    - Rolling 20-bar volume average and std
    - Spike = volume > avg + sigma*std
    - Level break = price crosses above 20-bar high or below 20-bar low on same bar
    """
    def generate_signals(self) -> pd.DataFrame:
        df = self.data
        sigma = self.params.get('spike_sigma', 2.0)
        lookback = self.params.get('lookback', 20)

        df['vol_avg'] = df['volume'].rolling(lookback).mean()
        df['vol_std'] = df['volume'].rolling(lookback).std()

        df['is_spike'] = df['volume'] > (df['vol_avg'] + sigma * df['vol_std'])

        # Shift 1 to avoid lookahead for resistance/support
        df['res'] = df['high'].shift(1).rolling(lookback).max()
        df['sup'] = df['low'].shift(1).rolling(lookback).min()

        df['break_up'] = df['close'] > df['res']
        df['break_down'] = df['close'] < df['sup']

        # ATR for exit calculation
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(lookback).mean()

        df['signal'] = 0
        df.loc[df['is_spike'] & df['break_up'], 'signal'] = 1
        df.loc[df['is_spike'] & df['break_down'], 'signal'] = -1

        self.signals = df[['date', 'open', 'high', 'low', 'close', 'volume', 'atr', 'signal']].copy()
        self.signals['entry_price'] = self.signals['open'].shift(-1)

        return self.signals

class Strategy4_OptionVolumeImbalance(BaseStrategy):
    """
    Strategy 4: Option Volume Imbalance (NIFTY/BANKNIFTY only)
    - Uses synthetic daily PCR data
    - PCR spike: rolling PCR > 95th percentile -> bearish
    - rolling PCR < 5th percentile -> bullish
    - On signal, simulate buying ATM option
    """
    def generate_signals(self) -> pd.DataFrame:
        df = self.data
        pcr_df = self.extra_data # The daily PCR data
        percentile_thresh = self.params.get('pcr_percentile', 95)

        if pcr_df is None or pcr_df.empty:
            df['signal'] = 0
            self.signals = df[['date', 'open', 'high', 'low', 'close', 'volume', 'signal']].copy()
            return self.signals

        # Map daily PCR to intraday data
        df['date_only'] = df['date'].dt.date
        pcr_df['date_only'] = pd.to_datetime(pcr_df['date']).dt.date

        df = df.merge(pcr_df[['date_only', 'PCR']], on='date_only', how='left')

        # Calculate rolling percentiles on daily data
        lookback_days = 20
        # Convert to bars
        bars_per_day = 75
        lookback_bars = lookback_days * bars_per_day

        df['pcr_upper'] = df['PCR'].rolling(lookback_bars).quantile(percentile_thresh/100.0)
        df['pcr_lower'] = df['PCR'].rolling(lookback_bars).quantile((100-percentile_thresh)/100.0)

        df['signal'] = 0
        # PCR high = lots of puts = bearish sentiment -> signal bearish (buy PE)
        df.loc[df['PCR'] > df['pcr_upper'], 'signal'] = -1
        # PCR low = bullish -> buy CE
        df.loc[df['PCR'] < df['pcr_lower'], 'signal'] = 1

        # We only want to trigger once per day max, so keep only first signal per day
        df['signal_changed'] = df['signal'] != df['signal'].shift(1)
        df.loc[~df['signal_changed'], 'signal'] = 0

        self.signals = df[['date', 'open', 'high', 'low', 'close', 'volume', 'signal']].copy()
        self.signals['entry_price'] = self.signals['open'].shift(-1)

        return self.signals

class Strategy5_VolumeDivergence(BaseStrategy):
    """
    Strategy 5: Volume Divergence Reversal
    - Price makes new N-bar high/low BUT volume is BELOW 20-bar average
    - RSI > 70 (short) or < 30 (long)
    """
    def generate_signals(self) -> pd.DataFrame:
        df = self.data
        lookback = self.params.get('lookback', 10)
        rsi_thresh_long = self.params.get('rsi_long', 30)
        rsi_thresh_short = self.params.get('rsi_short', 70)

        # RSI Calculation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        df['vol_avg'] = df['volume'].rolling(20).mean()

        df['highest_high'] = df['high'].rolling(lookback).max()
        df['lowest_low'] = df['low'].rolling(lookback).min()

        df['new_high'] = df['high'] == df['highest_high']
        df['new_low'] = df['low'] == df['lowest_low']

        df['vol_divergence'] = df['volume'] < df['vol_avg']

        # Calculate VWAP for exit
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['cum_vol'] = df['volume'].cumsum()
        df['cum_vol_price'] = (df['typical_price'] * df['volume']).cumsum()
        df['vwap'] = df['cum_vol_price'] / df['cum_vol']

        df['signal'] = 0

        # Fade the extreme
        long_cond = df['new_low'] & df['vol_divergence'] & (df['rsi'] < rsi_thresh_long)
        short_cond = df['new_high'] & df['vol_divergence'] & (df['rsi'] > rsi_thresh_short)

        df.loc[long_cond, 'signal'] = 1
        df.loc[short_cond, 'signal'] = -1

        self.signals = df[['date', 'open', 'high', 'low', 'close', 'volume', 'vwap', 'signal']].copy()
        self.signals['entry_price'] = self.signals['open'].shift(-1)

        return self.signals
