## Kill-Test Results: OI-Wall Mean Reversion (Candidate #21)

| Variant               |   Trades |   Net Exp (INR) |   MaxDD % |   Calmar | Verdict                    |
|:----------------------|---------:|----------------:|----------:|---------:|:---------------------------|
| BASE (k=0.3%)         |        0 |             0   |         0 |        0 | INCONCLUSIVE (sample < 40) |
| BASE (k=0.5%)         |        0 |             0   |         0 |        0 | INCONCLUSIVE (sample < 40) |
| BASE (k=1.0%)         |        1 |          1462.5 |         0 |      inf | INCONCLUSIVE (sample < 40) |
| EMA10 FILTER (k=0.3%) |        0 |             0   |         0 |        0 | INCONCLUSIVE (sample < 40) |
| EMA10 FILTER (k=0.5%) |        0 |             0   |         0 |        0 | INCONCLUSIVE (sample < 40) |
| EMA10 FILTER (k=1.0%) |        1 |          2050   |         0 |      inf | INCONCLUSIVE (sample < 40) |
| BREAKOUT              |        0 |             0   |         0 |        0 | INCONCLUSIVE (sample < 40) |

### Additional Information:
- For k=0.3%, the EMA10 filter removed 0 signals.
- For k=0.5%, the EMA10 filter removed 0 signals.
- For k=1.0%, the EMA10 filter removed 0 signals.

**Note**: Test run on limited bhavcopy data loaded in session.
