# Coverage Findings for Bharat-sm-data

## Coverage Matrix Table

| Function | Instrument | Time Point | Result | Oldest Date | Granularity | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `get_options_expiry` | NIFTY | Current | OK | 2026-06-30 | List of Dates | Successfully fetches upcoming expiries. |
| `get_options_expiry` | BANKNIFTY | Current | OK | 2026-06-30 | List of Dates | Successfully fetches upcoming expiries. |
| `get_options_expiry` | RELIANCE | Current | OK | 2026-06-30 | List of Dates | Successfully fetches upcoming expiries. |
| `get_option_chain` | NIFTY | 1 week ago | EMPTY | N/A | N/A | `None of ['strikePrice'] are in columns`. |
| `get_option_chain` | NIFTY | 1 month ago | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | NIFTY | 6 months ago | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | NIFTY | 1 year (Jun 2025) | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | NIFTY | 2 years (Jun 2024) | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | NIFTY | 4 years (2022) | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | NIFTY | 6 years (2020) | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | NIFTY | Past Weekly 2025 | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | NIFTY | Past Weekly 2023 | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | NIFTY | Past Weekly 2020 | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | BANKNIFTY | 1 week ago | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | BANKNIFTY | 1 month ago | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | BANKNIFTY | 6 months ago | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | BANKNIFTY | 1 year (Jun 2025) | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | BANKNIFTY | 2 years (Jun 2024) | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | BANKNIFTY | 4 years (2022) | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | BANKNIFTY | 6 years (2020) | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | BANKNIFTY | Past Weekly 2025 | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | BANKNIFTY | Past Weekly 2023 | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | BANKNIFTY | Past Weekly 2020 | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | RELIANCE | 1 week ago | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | RELIANCE | 1 month ago | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | RELIANCE | 6 months ago | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | RELIANCE | 1 year (Jun 2025) | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | RELIANCE | 2 years (Jun 2024) | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | RELIANCE | 4 years (2022) | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | RELIANCE | 6 years (2020) | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | RELIANCE | Past Weekly 2025 | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | RELIANCE | Past Weekly 2023 | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_option_chain` | RELIANCE | Past Weekly 2020 | EMPTY | N/A | N/A | Fails for past expiries. |
| `get_options_data_with_greeks`| NIFTY | All Past Time Points| ERROR | N/A | N/A | Token search/lookup hits Sensibull live endpoint, failing for past dates. |
| `get_options_data_with_greeks`| BANKNIFTY | All Past Time Points| ERROR | N/A | N/A | Same as NIFTY. |
| `get_options_data_with_greeks`| RELIANCE | All Past Time Points| ERROR | N/A | N/A | Same as NIFTY. |
| `get_ohlc_data (Futures)` | FUTIDXNIFTY... | Current/Live | OK | 2026-06-25 | Daily | Current contract OHLC works, but only gives recent days. |
| `get_ohlc_data (Options)` | OPTIDXNIFTY... | Current/Live | OK | 2026-06-25 | Daily | Current contract OHLC works, but only gives recent days. |
| `get_ohlc_data (Index)` | NIFTY 50 | Various historical | ERROR | N/A | N/A | Internal pandas indexing error or empty responses on base tickers. |
| `get_india_vix` | INDIA VIX | Various historical | EMPTY | N/A | N/A | Method prints message that India VIX is no longer available on NSE India, returns Empty DataFrame. |

*Note on Sensibull greeks:* Sensibull's functions attempt to look up tokens and pull greeks but uniformly hit `ERROR` states in the probe when requesting old expiry dates, likely because Sensibull's public/free API endpoints are geared for live data rather than massive historical archives.

## VERDICT

**Can Bharat-sm-data serve as the historical data source for a 7-year EOD NIFTY options backtest?**

**NO.**

The single limiting factor is that **the underlying NSE Option Chain API endpoint (`/api/option-chain-v3`) only returns data for current/upcoming expiries, not historical ones.** When queried for past dates, the library either returns an empty dictionary/DataFrame, throws parsing errors (e.g., `None of ['strikePrice'] are in the columns`), or faces HTTP 403 blocks.

You cannot retrieve the full option chain WITH prices for past expiries using this library's free endpoints. It strictly functions as a scraper for **live/recent/upcoming** data from the NSE website and charting endpoints, not a historical database. Even for standard OHLC data on specific current contracts, it only returns the last few days of data (`2026-06-25` oldest returned).

## CAVEATS

1. **Datacenter IP Blocking (403s / Rate Limits):** The NSE website strictly throttles and often outright blocks requests originating from datacenter IPs (like AWS, GCP, etc.). During the probe, we frequently encountered `HTTPSConnectionPool` `403` errors. While a residential IP with proper rotating proxies might bypass the 403s to fetch the *live* chains, it would NOT fix the core issue: the NSE website does not expose a 7-year deep historical option chain endpoint for scraping.
2. **Missing VIX:** `INDIA VIX` data is no longer available via the NSE endpoints mapped by the `Technical` module in this library, explicitly printing a warning and returning an empty frame.
3. **Internal Errors:** The `get_ohlc_data` fallback endpoints are currently throwing pandas `IndexError` internally on empty scraped payloads when trying to resolve base index tickers.
