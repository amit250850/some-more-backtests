import yfinance as yf

# Let's check how much we can actually get with yfinance for intraday
data = yf.download("^NSEI", interval="5m", period="60d")
print("Yfinance max 5m length:", len(data))
