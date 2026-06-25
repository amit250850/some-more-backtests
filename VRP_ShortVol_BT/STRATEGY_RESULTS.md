# Master Strategy Results & Graveyard

This file acts as the master ledger for all options strategies tested through the EOD kill-test engine. All results reported here reflect the strict, cost-inclusive, SL-high-proxy evaluation criteria defined in `KILL_TEST_RULES.md`.

| Strategy | Key Params | Trades | Net P&L (Close) | Net P&L (High) | Win% | R:R | Expectancy | MaxDD% | Calmar | Worst Expiry | Verdict | Notes/Cause-of-death |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| VRP Short Strangle | weekly, delta 0.18 short / 0.07 wing, no filter | 256 | -₹2.14L | -₹2.08L | 33% | 0.51 | -₹837 | -121% | -0.9 | -₹16,293 (2022-02-24) | FAIL | Structurally negative net of costs; only 2019 positive; deteriorates every year. |
