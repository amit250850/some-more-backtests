import yfinance as yf
import pandas as pd

nse_spot = yf.download('^NSEI', start='2019-01-01', end='2024-01-01')
print(nse_spot.head())
