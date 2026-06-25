from data_fetch import fetch_bhavcopy
from chain_builder import build_chain
from black76_greeks import add_greeks_to_chain
from datetime import datetime

date_obj = datetime(2023, 1, 2)
df = fetch_bhavcopy(date_obj)

f, exp, chain = build_chain(df, date_obj)
print(f"Forward: {f}, DTE: {chain['dte'].iloc[0]}")

chain_greeks = add_greeks_to_chain(chain, f, 0.065)

# Filter out NA and sort by strike
ce_chain = chain_greeks[chain_greeks['opt_type'] == 'CE'].dropna(subset=['delta'])
pe_chain = chain_greeks[chain_greeks['opt_type'] == 'PE'].dropna(subset=['delta'])

print("Calls near 0.18 delta:")
print(ce_chain.iloc[(ce_chain['delta'] - 0.18).abs().argsort()[:3]][['strike', 'settle_price', 'iv', 'delta']])

print("\nPuts near -0.18 delta:")
print(pe_chain.iloc[(pe_chain['delta'] - (-0.18)).abs().argsort()[:3]][['strike', 'settle_price', 'iv', 'delta']])
