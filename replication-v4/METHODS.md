# New daily-calibrated techniques

Two additional choices fit on daily returns and retain quarterly trades: gold/silver, and gold/silver plus broad equities. They use the same per-company dates but the [v5 methods](../replication-v5/METHODS.md). The original seven choices below retain the previous monthly calibration.

# Daily and monthly gold tracking explorer

Snapshot cutoff: September 30, 2026. Extension of the frozen v3 study, preserving the earlier artifacts. Twenty companies and seven techniques, with daily valuations and monthly or quarterly trades.

## Returns and fit

Daily adjusted-close stock and GLD/SLV/BIL observations are aligned. Only GVZ can carry a previous value across missing dates. Portfolio shares stay fixed between scheduled trades. Cash follows BIL; negative cash additionally pays 50 basis points annual borrowing spread, accrued by actual elapsed calendar days. Stock and portfolio fund trades pay 2 basis points. Monthly NAVs are sampled from the same daily paths, and monthly returns are the compounded daily changes. These are historical simulations using revised vendor data.

The original fourteen companies reuse the frozen v3 monthly model weights. Six additions use the same estimation engine: 24 monthly returns for fitted replication, 36 for risk targeting, with an entire month gap before entry. Initial evaluation waits for 37 aligned monthly marks, including the GVZ availability requirement for all seven techniques. This gives a common start across techniques for each company, but different companies may have different coverage. Model calibration remains monthly even when performance is measured daily. A daily-calibrated optimizer would be a separate research experiment.

Gold/silver/options fitting retains the v3 bounds and fixed stabilizing penalty. Gold is capped at 3×, silver at 1×, and gold call/put quantities at 1× underlying-equivalent exposure each. Model-defined paid calls and puts are valued using Black-Scholes and the observed GVZ input, with a fixed lagged BIL-derived rate per option contract and 5% premium spread. These are illustrative model marks, not execution quotes or observed historical option surfaces. Options expire on the last common session of the target month. Calendar-day financing and actual trading-day option expiry differ slightly from the earlier month-end-only engine; do not attribute every cross-version difference to return frequency.

Tracking R² = 1 − sum((stock return − portfolio return)^2) / sum((stock return − sample mean stock return)^2). It is evaluated on the replay's actual returns; no hindsight intercept or slope is credited to the portfolio. Regression R² = squared Pearson correlation, equivalent to an in-sample univariate OLS regression with intercept. Its separately shown slope and intercept are diagnostics only. R² can change materially with measurement frequency. Daily changes spanning more than four calendar days are omitted from daily statistics and charts; monthly measurements retain full monthly returns. Annualized tracking error uses sample standard deviation of return differences times sqrt(252) or sqrt(12).

Holding-period dots use month-end NAV ratios from an ongoing account, including its transaction costs. They are not fresh-entry backtests. Annualized returns use the selected number of months. Adjacent windows overlap and do not represent independent experiments. Filters restrict the return observations and both endpoints of the holding window; they do not retrain models.

## Universe and sources

Original universe: NEM, AEM, B, AU, FNV, WPM, RGLD, GFI, KGC, HMY, EGO, IAG, BTG, OR. Additions: DRD, SSRM, CDE, EQX, SA, NG. SA and NG are developers; other companies may have substantial non-gold exposure. Current survivors and revised corporate-adjusted histories introduce selection and revision bias. No fabricated history precedes available observations.

Data: registered Yahoo Finance chart JSON endpoint, explicit-date daily adjusted closes and dividend/split adjustments, private source snapshots with names, request URLs, dates and SHA-256 hashes. New fetches retain the same September cutoff as the prior study. Only derived portfolio research is published; raw quote snapshots, credentials and correspondence are excluded.

The prior study's methods and wider sensitivities remain at [replication-v3](../replication-v3/). Seven candidates are shown here for comparability, without selecting a historical winner. Funded bullion proxies are not actual rolled futures returns; historical futures and option-execution validation remains incomplete. There is no claim of a live forward test or of independent daily observations.
