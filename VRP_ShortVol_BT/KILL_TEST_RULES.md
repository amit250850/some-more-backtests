# Strategy Kill-Test Rules

These rules dictate whether an options backtest constitutes a viable, survivable strategy. They are fixed to ensure we never move the goalposts to flatter a backtest.

Every strategy must be evaluated against these gates. A strategy is only considered a **PASS** if it clears *all* gates.

## Mandatory Testing Conditions
1. **Minimum Sample Size**: The strategy must generate at least **50 trades**.
   - *Failure Mode*: Any run producing `< 30 trades` is immediately flagged as **UNRELIABLE** due to lack of statistical significance, regardless of returns.
2. **Strict Cost Enforcement**: Costs (brokerage, STT, exchange txns, SEBI, stamp, GST) and Slippage MUST be enabled.
   - *Failure Mode*: Auto-reject any run claiming zero slippage or zero costs.
3. **Primary Evaluation Metric**: The strategy is judged strictly on the **SL-HIGH-PROXY** numbers.
   - The *SL-on-Close* numbers are provided for optimistic reference only and cannot be used to pass the gates.

## Performance Risk Gates (The "Kill-Test")
1. **Calmar Ratio**: Must be `>= 1.0`
   - *Fail Threshold*: `< 1.0 = FAIL*
2. **Maximum Drawdown**: Must be `<= 25%` of deployed capital.
   - *Fail Threshold*: `> 25% = FAIL`
3. **Expectancy**: Net Expectancy per trade must be profoundly positive.
   - *Fail Threshold*: `<= 0 = FAIL`
4. **Tail Risk (Worst Expiry)**: The worst single losing trade must not wipe out more than roughly ~3 months of average gains.
   - *Fail Threshold*: Severe single-trade blowouts trigger a **RED FLAG** requiring manual review.
5. **Correlation Check (Qualitative)**:
   - Does the strategy merely replicate NIFTY beta or long-only momentum? If it acts purely as a highly-leveraged delta proxy, it fails to provide the required diversification benefit.

## Verdict Criteria
- **PASS**: Meets all Mandatory Testing Conditions AND clears all Performance Risk Gates on the conservative SL-High-Proxy.
- **FAIL**: Fails one or more Performance Risk Gates.
- **UNRELIABLE**: Generates fewer than 30 trades, or uses a flawed/zero-cost setup.
