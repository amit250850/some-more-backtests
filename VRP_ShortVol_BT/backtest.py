import yaml
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from data_fetch import fetch_bhavcopy
from chain_builder import build_chain
from black76_greeks import add_greeks_to_chain
from strategy import select_strikes, get_leg_prices
from costs import calculate_entry_costs, calculate_exit_costs

LOT_SIZE = 50 # NIFTY lot size

def run_backtest(config_path='/app/VRP_ShortVol_BT/config.yaml', ivp_threshold=0):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Read pre-computed IVP
    try:
        df_iv = pd.read_csv('/app/VRP_ShortVol_BT/atm_iv.csv')
        df_iv['date'] = pd.to_datetime(df_iv['date'])
        df_iv.set_index('date', inplace=True)
    except:
        df_iv = pd.DataFrame()

    start_date = pd.to_datetime(config['dates']['start'])
    end_date = pd.to_datetime(config['dates']['end'])

    trades = []

    current_trade = None
    last_traded_expiry = None

    # Warmup period for 252-day IVP
    # We enforce that ALL runs (even threshold=0) start evaluating only after we have a valid IVP (i.e. ~126-252 days)
    # We will just skip days where IVP is NaN.

    date_range = pd.date_range(start=start_date, end=end_date, freq='B')

    for date_obj in date_range:
        # Check IVP first to avoid heavy chain processing if not needed
        current_ivp = np.nan
        if not df_iv.empty and date_obj in df_iv.index:
            current_ivp = df_iv.loc[date_obj, 'ivp_252']

        # We need a valid IVP to make a decision (even for threshold 0, to keep comparison fair)
        # If we are holding a trade, we still need to process the day.
        # So we only enforce IVP on ENTRY.

        df_day = fetch_bhavcopy(date_obj)
        if df_day is None:
            continue

        f, upcoming_expiry, chain = build_chain(df_day, date_obj)
        if chain is None:
            continue

        dte = chain['dte'].iloc[0]

        # Are we looking to enter?
        if current_trade is None:
            # We ONLY enter if IVP is valid AND >= threshold
            if pd.isna(current_ivp):
                continue

            if dte <= config['strategy']['dte_entry'] and upcoming_expiry != last_traded_expiry:
                if current_ivp >= ivp_threshold:
                    # Enter trade
                    chain_greeks = add_greeks_to_chain(chain, f, config['pricing']['risk_free_rate'])
                    legs = select_strikes(chain_greeks, config)
                    if legs is None:
                        continue

                    slippage = config['costs']['slippage_pct']

                    p_sce, c_sce = calculate_entry_costs(legs['short_ce']['settle_price'], LOT_SIZE, 'SELL', slippage, config)
                    p_spe, c_spe = calculate_entry_costs(legs['short_pe']['settle_price'], LOT_SIZE, 'SELL', slippage, config)
                    p_lce, c_lce = calculate_entry_costs(legs['long_ce']['settle_price'], LOT_SIZE, 'BUY', slippage, config)
                    p_lpe, c_lpe = calculate_entry_costs(legs['long_pe']['settle_price'], LOT_SIZE, 'BUY', slippage, config)

                    entry_premium_received = (p_sce + p_spe) * LOT_SIZE
                    entry_premium_paid = (p_lce + p_lpe) * LOT_SIZE
                    entry_net_credit = entry_premium_received - entry_premium_paid
                    total_entry_cost = c_sce + c_spe + c_lce + c_lpe

                    current_trade = {
                        'entry_date': date_obj,
                        'expiry': upcoming_expiry,
                        'entry_ivp': current_ivp,
                        'legs': {
                            'short_ce': {'strike': legs['short_ce']['strike'], 'entry': p_sce, 'delta': legs['short_ce']['delta'], 'iv': legs['short_ce']['iv']},
                            'short_pe': {'strike': legs['short_pe']['strike'], 'entry': p_spe, 'delta': legs['short_pe']['delta'], 'iv': legs['short_pe']['iv']},
                            'long_ce': {'strike': legs['long_ce']['strike'], 'entry': p_lce, 'delta': legs['long_ce']['delta'], 'iv': legs['long_ce']['iv']},
                            'long_pe': {'strike': legs['long_pe']['strike'], 'entry': p_lpe, 'delta': legs['long_pe']['delta'], 'iv': legs['long_pe']['iv']},
                        },
                        'entry_short_premium': (legs['short_ce']['settle_price'] + legs['short_pe']['settle_price']),
                        'entry_net_credit': entry_net_credit,
                        'total_entry_cost': total_entry_cost,
                        'status': 'OPEN',
                        'sl_high_hit': False,
                        'sl_high_data': None
                    }

        # Are we holding?
        else:
            is_expiry_day = date_obj >= current_trade['expiry']

            leg_prices = {}
            missing_leg = False
            for leg_name, leg_data in current_trade['legs'].items():
                opt_type = 'CE' if 'ce' in leg_name else 'PE'
                prices = get_leg_prices(chain, leg_data['strike'], opt_type)

                if prices is None:
                    if is_expiry_day:
                        prices = pd.Series({'close': 0.0, 'settle_price': 0.0, 'high': 0.0, 'low': 0.0})
                    else:
                        missing_leg = True
                        break
                leg_prices[leg_name] = prices

            if missing_leg:
                continue

            sl_threshold = current_trade['entry_short_premium'] * (1 + config['strategy']['stop_loss_pct'] / 100.0)
            target_threshold = None
            if config['strategy']['profit_target_pct'] is not None:
                target_threshold = current_trade['entry_short_premium'] * (1 - config['strategy']['profit_target_pct'] / 100.0)

            high_short_premium = leg_prices['short_ce']['high'] + leg_prices['short_pe']['high']

            if not current_trade['sl_high_hit'] and high_short_premium >= sl_threshold:
                current_trade['sl_high_hit'] = True
                slippage = config['costs']['slippage_pct']
                short_exit_price = (sl_threshold / 2)

                p_sce, c_sce = calculate_exit_costs(short_exit_price, LOT_SIZE, 'BUY', slippage, config, False)
                p_spe, c_spe = calculate_exit_costs(short_exit_price, LOT_SIZE, 'BUY', slippage, config, False)
                p_lce, c_lce = calculate_exit_costs(leg_prices['long_ce']['close'], LOT_SIZE, 'SELL', slippage, config, False)
                p_lpe, c_lpe = calculate_exit_costs(leg_prices['long_pe']['close'], LOT_SIZE, 'SELL', slippage, config, False)

                exit_net_debit = (p_sce + p_spe) * LOT_SIZE - (p_lce + p_lpe) * LOT_SIZE
                total_exit_cost = c_sce + c_spe + c_lce + c_lpe

                current_trade['sl_high_data'] = {
                    'exit_date': date_obj,
                    'gross_pnl': current_trade['entry_net_credit'] - exit_net_debit,
                    'total_costs': current_trade['total_entry_cost'] + total_exit_cost,
                    'net_pnl': (current_trade['entry_net_credit'] - exit_net_debit) - (current_trade['total_entry_cost'] + total_exit_cost)
                }

            exit_reason = None
            current_short_premium = leg_prices['short_ce']['close'] + leg_prices['short_pe']['close']

            if current_short_premium >= sl_threshold:
                exit_reason = 'SL_CLOSE'
            elif target_threshold is not None and current_short_premium <= target_threshold:
                exit_reason = 'TARGET'
            elif is_expiry_day:
                exit_reason = 'EXPIRY'

            if exit_reason:
                slippage = config['costs']['slippage_pct']
                is_exp = exit_reason == 'EXPIRY'

                p_sce, c_sce = calculate_exit_costs(leg_prices['short_ce']['settle_price'] if is_exp else leg_prices['short_ce']['close'], LOT_SIZE, 'BUY', slippage, config, is_exp)
                p_spe, c_spe = calculate_exit_costs(leg_prices['short_pe']['settle_price'] if is_exp else leg_prices['short_pe']['close'], LOT_SIZE, 'BUY', slippage, config, is_exp)
                p_lce, c_lce = calculate_exit_costs(leg_prices['long_ce']['settle_price'] if is_exp else leg_prices['long_ce']['close'], LOT_SIZE, 'SELL', slippage, config, is_exp)
                p_lpe, c_lpe = calculate_exit_costs(leg_prices['long_pe']['settle_price'] if is_exp else leg_prices['long_pe']['close'], LOT_SIZE, 'SELL', slippage, config, is_exp)

                exit_premium_paid = (p_sce + p_spe) * LOT_SIZE
                exit_premium_received = (p_lce + p_lpe) * LOT_SIZE
                exit_net_debit = exit_premium_paid - exit_premium_received
                total_exit_cost = c_sce + c_spe + c_lce + c_lpe

                gross_pnl = current_trade['entry_net_credit'] - exit_net_debit
                total_costs = current_trade['total_entry_cost'] + total_exit_cost
                net_pnl = gross_pnl - total_costs

                if current_trade['sl_high_hit']:
                    net_pnl_high = current_trade['sl_high_data']['net_pnl']
                    gross_pnl_high = current_trade['sl_high_data']['gross_pnl']
                else:
                    net_pnl_high = net_pnl
                    gross_pnl_high = gross_pnl

                trade_record = {
                    'entry_date': current_trade['entry_date'],
                    'exit_date': date_obj,
                    'expiry': current_trade['expiry'],
                    'entry_ivp': current_trade['entry_ivp'],
                    'short_ce_strike': current_trade['legs']['short_ce']['strike'],
                    'short_pe_strike': current_trade['legs']['short_pe']['strike'],
                    'long_ce_strike': current_trade['legs']['long_ce']['strike'],
                    'long_pe_strike': current_trade['legs']['long_pe']['strike'],
                    'short_ce_delta': current_trade['legs']['short_ce']['delta'],
                    'short_pe_delta': current_trade['legs']['short_pe']['delta'],
                    'short_ce_iv': current_trade['legs']['short_ce']['iv'],
                    'short_pe_iv': current_trade['legs']['short_pe']['iv'],
                    'short_ce_entry_price': current_trade['legs']['short_ce']['entry'],
                    'short_pe_entry_price': current_trade['legs']['short_pe']['entry'],
                    'short_ce_exit_price': p_sce,
                    'short_pe_exit_price': p_spe,
                    'gross_pnl_close': gross_pnl,
                    'net_pnl_close': net_pnl,
                    'gross_pnl_high': gross_pnl_high,
                    'net_pnl_high': net_pnl_high,
                    'total_costs': total_costs,
                    'exit_reason': exit_reason,
                    'sl_high_hit': current_trade['sl_high_hit']
                }

                trades.append(trade_record)

                last_traded_expiry = current_trade['expiry']
                current_trade = None

    return pd.DataFrame(trades)

if __name__ == "__main__":
    df_trades = run_backtest()
    df_trades.to_csv('/app/VRP_ShortVol_BT/trades.csv', index=False)
