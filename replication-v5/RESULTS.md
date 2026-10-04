# Daily calibration improves company tracking

All results are historical walk-forward replays, with 26 new portfolio rules and three previous baselines retained. Same per-company dates; monthly or quarterly trading.

| Company | Previous gold/silver daily R² | New daily metals R² | New metals + equities R² |
|---|---:|---:|---:|
| NEM | 0.434 | 0.462 | 0.489 |
| AEM | 0.428 | 0.512 | 0.524 |
| B | 0.485 | 0.537 | 0.553 |
| AU | 0.397 | 0.474 | 0.484 |
| FNV | 0.435 | 0.465 | 0.479 |
| WPM | 0.505 | 0.538 | 0.564 |
| RGLD | 0.402 | 0.449 | 0.471 |
| GFI | 0.359 | 0.428 | 0.433 |
| KGC | 0.390 | 0.472 | 0.490 |
| HMY | 0.357 | 0.413 | 0.419 |
| EGO | 0.313 | 0.372 | 0.387 |
| IAG | 0.369 | 0.416 | 0.428 |
| BTG | 0.410 | 0.436 | 0.445 |
| OR | 0.355 | 0.428 | 0.438 |
| DRD | 0.240 | 0.328 | 0.334 |
| SSRM | 0.381 | 0.403 | 0.418 |
| CDE | 0.359 | 0.394 | 0.440 |
| EQX | 0.377 | 0.468 | 0.481 |
| SA | 0.360 | 0.389 | 0.400 |
| NG | 0.311 | 0.338 | 0.353 |

The equal-company average daily tracking R² rises from 0.383 to 0.436 with daily metals estimates, then0.452 with the broad-equity extension. All 20 companies improve versus the previous gold/silver model on their respective full histories. The original-cap controls retain the gain, so the new silver limit alone does not explain it.

Wheaton’s daily R² improves from 0.505 to 0.538 (metals) and 0.564 (metals plus equities). This represents about 6.7% and 12.0% less squared daily error. Its 2020-onward daily R² rises from 0.524 to 0.582 and 0.596; monthly measurements remain separately visible.

Paid longer-dated options did not provide a dependable incremental improvement over the simpler daily metals rule. Zero-shrink variants also failed to rescue the convexity gain. The broader oil/currency extension is mixed; the shorter-window and adaptive rules do not establish superiority over the fixed recency model. All results, including negative comparisons, remain in all-results.csv.

The retained quadratic explanatory diagnostic was worse than the linear version for Wheaton over the full and post2020 periods. That is evidence against these simple squared-return terms, not proof that the equity lacks real-option convexity. In a simplified asset model, margin is proportional to price minus cost, and local percentage sensitivity is P/(P−C): it rises near the cost threshold and falls as margins widen. A finite-tenor call also carries theta and vega that need not match the company.

Large residuals coincide with company-specific events: Wheaton’s December2018 tax settlement, Newmont’s October2024 results, Equinox’s September2023 financing announcement and SSR Mining’s February2024 incident. These were retained, not removed to improve R². See COMPANIES.md for primary sources and the dashboard for measured returns.

This model estimates exposures from prices; it does not yet reconstruct each mine’s reserves, costs, production schedule and financing from filing-known historical data. Such a point-in-time operating model is the next distinct research step. Daily R² improvement does not imply replication of business growth, dividends or terminal wealth. Current filings motivate hypotheses without supplying historical backfilled inputs.

These hypotheses follow prior historical study. Post2020 and post2023 are retrospective confirmation periods, not virgin holdouts. Portfolio holdings, fees and cash are modeled; actual historical option execution and futures rolls remain unverified.

## Tracking moves does not ensure matching compounding

Over Wheaton’s full paired history, stock CAGR is 10.4%. The previous gold/silver model compounds at 5.2%, the new daily metals model at 4.7%, and the metals-plus-equities model at 10.0%. Thus the metals-only improvement in daily R² does not solve the cumulative-return shortfall. Adding broad-equity exposure improves both for Wheaton in this sample, but also changes the economic exposure; it is not evidence that gold alone recreates the business or that all companies have the same result. Recent monthly R² can also be lower despite higher daily R². The full metrics and wealth paths expose those tradeoffs.
