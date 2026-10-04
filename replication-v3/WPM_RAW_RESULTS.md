# WPM stored raw versus shrinkage diagnostic

All stored raw and deployed variants were replayed on the same dates and schedule with the same costs. This is sequential single-name exploration after the calendar correction; it is not an independent winner selection.

| Family | Deployed shrink R² | Raw training-SSE fit R² |
|---|---:|---:|
|gold_options_monthly|0.5696|0.5677|
|gold_options_quarterly|0.5726|0.5690|
|gold_silver_both_options_grid_quarterly|0.5764|0.5643|
|gold_silver_both_options_monthly|0.5677|0.5617|
|gold_silver_both_options_monthly_rv1|0.5622|0.5544|
|gold_silver_both_options_quarterly|0.5740|0.5698|
|gold_silver_both_options_quarterly_rv1|0.5730|0.5675|
|gold_silver_monthly|0.5800|0.5785|
|gold_silver_options_monthly|0.5773|0.5722|
|gold_silver_options_quarterly|0.5791|0.5730|
|gold_silver_quarterly|0.5815|0.5797|

The raw fits use the retained feasible-baseline fallback and need not be globally optimal. Comparing realized results does not retroactively change model selection or the fixed deployment penalty. All raw/deployed variants and cost sensitivities remain available in the separate JSON/CSV artifacts; the core dashboard data is unchanged.
