def calculate_entry_costs(premium, qty, action, slippage_pct, config):
    """
    Calculates execution price and costs on entry.
    action: 'BUY' or 'SELL'
    """
    # Apply slippage
    if action == 'BUY':
        exec_price = premium * (1 + slippage_pct)
    else:
        exec_price = premium * (1 - slippage_pct)

    order_val = exec_price * qty

    # Brokerage: min(20, 0.03% of order_val)
    brokerage = min(config['costs']['brokerage_per_order'], order_val * config['costs']['brokerage_pct'])

    # STT: Sell side only
    stt = order_val * config['costs']['stt_sell_pct'] if action == 'SELL' else 0.0

    # NSE Txn
    txn = order_val * config['costs']['nse_txn_pct']

    # SEBI
    sebi = order_val * config['costs']['sebi_turnover_pct']

    # Stamp Duty: Buy side only
    stamp = order_val * config['costs']['stamp_duty_buy_pct'] if action == 'BUY' else 0.0

    # GST
    gst = (brokerage + txn + sebi) * config['costs']['gst_pct']

    total_cost = brokerage + stt + txn + sebi + stamp + gst

    return exec_price, total_cost

def calculate_exit_costs(premium, qty, action, slippage_pct, config, is_expiry=False):
    """
    Calculates execution price and costs on exit.
    If is_expiry is True, it settles at exchange without slippage and brokerage,
    but STT applies if it's an ITM option expiring (STT is high on ITM exercise,
    but for short positions that expire ITM, it gets cash-settled. Usually we exit
    before expiry or it's OTM. For simplicity, we apply standard STT on ITM exit).
    """
    if is_expiry:
        exec_price = premium
        # Brokerage usually zero on expiry settlement, STT applies if it's a long ITM option
        # (0.125% of intrinsic value). For shorts it's zero.
        # To be conservative, let's just charge normal costs without slippage.
        brokerage = 0
        stt = 0
        txn = 0
        sebi = 0
        stamp = 0
        gst = 0
        # If long ITM, STT on intrinsic value
        if action == 'SELL' and premium > 0.05: # Long option expiring ITM
            stt = premium * qty * config['costs']['stt_sell_pct']

        total_cost = brokerage + stt + txn + sebi + stamp + gst
        return exec_price, total_cost

    # Apply slippage
    if action == 'BUY': # Exiting a short
        exec_price = premium * (1 + slippage_pct)
    else: # Exiting a long
        exec_price = premium * (1 - slippage_pct)

    order_val = exec_price * qty

    brokerage = min(config['costs']['brokerage_per_order'], order_val * config['costs']['brokerage_pct'])
    stt = order_val * config['costs']['stt_sell_pct'] if action == 'SELL' else 0.0
    txn = order_val * config['costs']['nse_txn_pct']
    sebi = order_val * config['costs']['sebi_turnover_pct']
    stamp = order_val * config['costs']['stamp_duty_buy_pct'] if action == 'BUY' else 0.0
    gst = (brokerage + txn + sebi) * config['costs']['gst_pct']

    total_cost = brokerage + stt + txn + sebi + stamp + gst

    return exec_price, total_cost
