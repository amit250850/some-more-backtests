import pandas as pd
import numpy as np

def find_nearest_strike(chain, target_delta, opt_type):
    """
    Finds the strike in the chain closest to the target_delta.
    """
    opts = chain[chain['opt_type'] == opt_type].dropna(subset=['delta'])
    if opts.empty:
        return None

    if opt_type == 'PE':
        target_delta = -target_delta # Puts have negative delta

    idx = (opts['delta'] - target_delta).abs().idxmin()
    return opts.loc[idx]

def get_leg_prices(chain, strike, opt_type):
    """
    Gets O, H, L, C, Settle for a given strike and option type in the current day's chain.
    """
    opts = chain[(chain['opt_type'] == opt_type) & (chain['strike'] == strike)]
    if opts.empty:
        return None
    return opts.iloc[0]

def select_strikes(chain, config):
    """
    Selects the 4 legs for the Iron Condor (Short Strangle + Wings).
    """
    sell_delta = config['strategy']['sell_delta']
    buy_delta = config['strategy']['buy_delta']

    short_ce = find_nearest_strike(chain, sell_delta, 'CE')
    short_pe = find_nearest_strike(chain, sell_delta, 'PE')
    long_ce = find_nearest_strike(chain, buy_delta, 'CE')
    long_pe = find_nearest_strike(chain, buy_delta, 'PE')

    if any(x is None for x in [short_ce, short_pe, long_ce, long_pe]):
        return None

    return {
        'short_ce': short_ce,
        'short_pe': short_pe,
        'long_ce': long_ce,
        'long_pe': long_pe
    }
