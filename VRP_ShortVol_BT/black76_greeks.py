import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq

def black76_price(F, K, T, r, sigma, option_type):
    """
    Computes the Black-76 option price.
    F: Forward price
    K: Strike
    T: Time to expiry in years
    r: Risk-free rate
    sigma: Implied volatility
    option_type: 'CE' or 'PE'
    """
    if T <= 0 or F <= 0 or K <= 0 or sigma <= 0:
        return 0.0

    d1 = (np.log(F / K) + (0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    discount = np.exp(-r * T)

    if option_type == 'CE':
        price = discount * (F * norm.cdf(d1) - K * norm.cdf(d2))
    else:
        price = discount * (K * norm.cdf(-d2) - F * norm.cdf(-d1))

    return price

def implied_volatility(price, F, K, T, r, option_type):
    """
    Solves for implied volatility using Brent's method.
    """
    if T <= 0 or price <= 0:
        return np.nan

    # Minimum price check for Black-76
    discount = np.exp(-r * T)
    intrinsic_value = discount * max(0, F - K) if option_type == 'CE' else discount * max(0, K - F)
    if price < intrinsic_value:
        # Price is below intrinsic value, IV is undefined or negative
        return np.nan

    def obj_func(sigma):
        return black76_price(F, K, T, r, sigma, option_type) - price

    try:
        # Brent's method requires bounding the root
        iv = brentq(obj_func, 1e-4, 5.0, xtol=1e-5, maxiter=100)
        return iv
    except (ValueError, RuntimeError):
        return np.nan

def calculate_delta(F, K, T, r, sigma, option_type):
    """
    Calculates the option delta based on Black-76.
    Note: For futures options, delta usually doesn't include the discount factor,
    but for equity options on futures, it's often e^{-rT} N(d1).
    We'll use standard Black-76 delta.
    """
    if np.isnan(sigma) or T <= 0:
        return np.nan

    d1 = (np.log(F / K) + (0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    discount = np.exp(-r * T)

    if option_type == 'CE':
        delta = discount * norm.cdf(d1)
    else:
        delta = discount * (norm.cdf(d1) - 1.0)

    return delta

def add_greeks_to_chain(chain, F, r=0.065):
    """
    Takes a chain dataframe and adds IV and Delta columns.
    """
    # Exclude 0 DTE or handle as tiny T
    chain = chain.copy()

    # Use trading days (approx 252/year) or calendar days (365)? Standard is calendar days for Indian markets
    # but some use trading days. Let's use 365 for T. If DTE is 0, use 0.001 to avoid div by zero.
    chain['T'] = np.maximum(chain['dte'], 0.001) / 365.0

    ivs = []
    deltas = []

    for idx, row in chain.iterrows():
        iv = implied_volatility(
            price=row['settle_price'],
            F=F,
            K=row['strike'],
            T=row['T'],
            r=r,
            option_type=row['opt_type']
        )
        ivs.append(iv)

        delta = calculate_delta(
            F=F,
            K=row['strike'],
            T=row['T'],
            r=r,
            sigma=iv,
            option_type=row['opt_type']
        )
        deltas.append(delta)

    chain['iv'] = ivs
    chain['delta'] = deltas

    return chain

if __name__ == "__main__":
    # Quick test
    F = 18000
    K = 18500
    T = 4 / 365.0
    r = 0.065
    price = 50.0

    iv = implied_volatility(price, F, K, T, r, 'CE')
    delta = calculate_delta(F, K, T, r, iv, 'CE')
    print(f"CE: IV={iv:.4f}, Delta={delta:.4f}")
