import numpy as np
from scipy.stats import norm

# Lot sizes based on instructions
LOT_SIZES = {
    "SILVERMIC": 30, # 30kg? Instruction says 30kg lot.
    "GOLDGUINEA": 8, # 8gm lot
    "NIFTY": 75,
    "BANKNIFTY": 30
}

def get_lot_size(instrument_name):
    for key, val in LOT_SIZES.items():
        if key in instrument_name:
            return val
    return 1 # Default

def calculate_costs(trade_val_entry, trade_val_exit):
    """
    Calculate slippage, brokerage, and STT/exchange charges
    """
    slippage_entry = trade_val_entry * 0.0005
    slippage_exit = trade_val_exit * 0.0005
    brokerage = 40 # 20 entry + 20 exit
    stt_exchange_entry = trade_val_entry * 0.0001
    stt_exchange_exit = trade_val_exit * 0.0001

    return slippage_entry + slippage_exit + brokerage + stt_exchange_entry + stt_exchange_exit

def black_scholes_call(S, K, T, r, sigma):
    if T <= 0:
        return max(0.0, S - K)
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return (S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2))

def black_scholes_put(S, K, T, r, sigma):
    if T <= 0:
        return max(0.0, K - S)
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return (K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1))
