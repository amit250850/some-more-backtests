# VRP Short-Vol Engine Specification

This document defines the core architecture and rules of the options backtesting engine. To ensure that all tested strategies remain strictly comparable, the core engine components must remain immutable. New strategies are implemented via predefined extension points.

## 1. Data Layer
- **Source**: NSE daily F&O EOD bhavcopy ZIP archives.
- **Formats Handled**:
  - Legacy format (pre-July 2024): `fo{DD}{MMM}{YYYY}bhav.csv.zip`
  - New UDiFF format (post-July 2024): `BhavCopy_NSE_FO_0_0_0_YYYYMMDD_F_0000.csv.zip`
- **Fields Available**: Date, Expiry, Strike, Option Type (CE/PE/FUT), Open, High, Low, Close, Settlement Price, Volume, Open Interest.
- **Date Coverage**: Support for deep historical analysis (tested from 2019-01-01 to present).
- **Caching**: All downloaded bhavcopies are strictly cached locally as `.parquet` files to prevent redundant network requests and API rate-limiting during iteration.

## 2. Pricing & Greeks Engine
- **Implied Volatility**: Solved locally from the option's EOD settlement price using the Black-76 model (futures-style Black-Scholes). We do *not* rely on external VIX feeds or spot IV proxies.
- **Futures-as-Forward**: The synchronous NIFTY near-month futures settlement price is used as the forward price (`F`) to correctly account for Indian market funding rates and dividends.
- **Greeks**: Delta is computed analytically from the locally solved IV using the standard normal CDF.

## 3. Cost & Slippage Model
To accurately reflect realistic trading conditions, costs are mandatory and calculated identically across all runs:
- **Brokerage**: `min(₹20, 0.03% of order value)` per leg per side.
- **STT (Securities Transaction Tax)**: Sell-side only, configurable % on premium (currently defaults to 0.10% / 0.125% based on recent exchange revisions).
- **Exchange Transaction Charge**: ~0.05% on premium.
- **SEBI Turnover Charge**: ₹10 per crore (0.0001%).
- **Stamp Duty**: Buy-side only, ₹300 per crore (0.003%).
- **GST**: 18% applied on (Brokerage + Exchange Txn + SEBI).
- **Slippage**: Configurable (default `1.5%` of the premium). Applied to both entry and exit premiums. *Zero slippage runs are explicitly forbidden.*

## 4. Stop-Loss (SL) Handling
Because the engine operates entirely on EOD data, it cannot definitively observe the exact intraday price path. Consequently, two SL variants are reported to prevent survivorship bias:
1. **SL-on-Close (Optimistic)**: Checks if the combined premium at the EOD *Close* breaches the SL threshold. If so, exits at the *Close* price (plus slippage).
2. **SL-on-High Proxy (Conservative)**: Checks if the combined daily *High* premiums breach the SL threshold. If breached, assumes an exit at exactly the SL threshold (plus slippage). Note: This overestimates risk slightly since individual leg highs may not occur synchronously, making it a robust, conservative proxy.

## 5. Standard Output Metrics
Every tested strategy must output the following metrics for comparison:
- **Total Trades**
- **Net P&L** (Both SL-Close and SL-High variants)
- **CAGR (%)**
- **Win Rate (%)**
- **Average Win / Average Loss**
- **Reward:Risk Ratio**
- **Expectancy (₹)**
- **Max Drawdown (₹ and % of deployed capital)**
- **Calmar Ratio** (CAGR / MaxDD)
- **Worst Single Expiry Trade (₹ and Date)**
- **Max Losing Streak (Trades)**
- **Year-wise Net P&L and MaxDD Table**

## 6. Extension Points
To maintain scientific consistency, only the following components may be altered when introducing a new strategy:
- **Allowed Changes**:
  - Entry/Exit Rules (e.g., DTE thresholds, specific days of the week).
  - Leg Structure (e.g., Straddles, Iron Condors, Ratio Spreads).
  - Strike Selection (e.g., Delta-based, ATM-offset).
  - Expiry Choice (e.g., Weekly vs. Monthly).
  - Regime/Event Filters (e.g., IV Percentile thresholds, VIX filters, moving averages).
- **Fixed Components (Do NOT Change)**:
  - Data ingestion and caching mechanism.
  - Black-76 pricing and Greeks computation.
  - Cost and slippage formulas.
  - Standard metric definitions and SL reporting rules.

## 7. Known Limitations
- **EOD Resolution**: Lacks precise intraday entry/exit mechanics and cannot backtest 0-DTE intraday strategies.
- **Simulated Slippage**: Real bid-ask spreads are unavailable; the 1.5% premium slippage is a flat assumption.
- **Single Underlying**: Currently hardcoded for NIFTY; extending to BankNifty/Finnifty requires adjusting lot sizes and instrument symbols.
