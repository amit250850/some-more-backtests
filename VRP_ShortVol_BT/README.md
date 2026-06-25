# VRP Short Volatility Backtester (NIFTY)

A rigorous, positional short-volatility options backtester for the NIFTY index in Python.
This project is designed as a "kill-test" to honestly evaluate if a defined-risk short-strangle (VRP harvesting) survives realistic trading costs over a multi-year period (~7 years).

## Features & Implementation Details

### Data Source & Format-Switch Handling
- **Source**: NSE daily F&O EOD bhavcopy ZIP archives.
- **Formats Handled**:
  - *Legacy format* (pre-July 2024): `fo{DD}{MMM}{YYYY}bhav.csv.zip`
  - *New UDiFF format* (post-July 2024): `BhavCopy_NSE_FO_0_0_0_YYYYMMDD_F_0000.csv.zip`
- The system gracefully tries the UDiFF format and falls back to the Legacy format.
- Data is downloaded and securely cached locally into Parquet files to prevent re-downloading and reduce backtesting iteration times.

### Greeks / IV Engine
- **No external VIX dependency**: Implied volatility is solved locally directly from the options' settlement prices using the Black-76 (futures-style Black-Scholes) model.
- **Futures-as-Forward**: We use the synchronous NIFTY near-month FUTURES settlement price as the forward price `F` because it more accurately represents the forward expectation in the Indian market compared to the spot index.
- Uses `scipy.optimize.brentq` to robustly solve for IV and standard normal CDF for delta calculation.

### Strategy Engine
- **Positional Short Strangle**: Sell a set delta (e.g. 0.18) strangles and buy protective wings (e.g. 0.07 delta).
- **Entry**: Configurable DTE before expiry.
- **Hold**: Positions are held overnight.
- **Exit Conditions**: Stop Loss (e.g. 30%), Profit Target, or Expiry Settlement.
- **EOD-SL Limitation**: Because we only have EOD data, the primary Stop-Loss check is performed on the daily CLOSE. Note that this limitation can obscure intraday drawdowns. We also compute a proxy using the daily HIGH to see if an intraday breach might have occurred, but report results primarily on close.

### Costs & Slippage
- Realistic execution costs are mandatory.
- **Slippage**: Settlement price does not equal tradeable price. A 1.5% slippage is assumed on both entry and exit premiums.
- **Brokerage & Taxes**: Calculates Zerodha-style F&O costs, including minimum brokerage, STT (sell-side only, currently configurable to 0.10%), NSE exchange transaction charge, SEBI charge, stamp duty, and GST.

## Running the Backtest

1. Configure parameters in `config.yaml`.
2. Run data fetch and strategy execution:
   ```bash
   python backtest.py
   ```
3. Generate the performance report and equity curve:
   ```bash
   python report.py
   ```
