# Intraday estimates add little; peer returns explain much of Wheaton's residual risk

Intraday estimation gives a small, uncertain recent improvement. Peer principal components explain a much larger share of Wheaton's residual movement, but the permitted-asset portfolios tested here do not reproduce that gain. The tests cover twenty companies and 41 portfolio rules, with financing and trading costs included. Portfolios still trade monthly or quarterly.

## Intraday estimates need the overnight component

Wheaton's matched April 30, 2025–September 30, 2026 monthly-traded metals accounts have daily tracking R² of 0.661 using daily calibration, 0.649 using hourly daytime calibration, and 0.668 using hourly plus overnight covariance. The last improves paired squared error by 2.1%, with a three-month-block interval of -2.4% to 7.8%. This short, recent sample does not establish a dependable improvement.

Across the twenty respective paired histories, monthly-traded metals' average daily R² is 0.547 for daily calibration and 0.561 with hourly plus overnight covariance. 16 companies improve. Quarterly intraday-only metals estimation improves zero companies against its matched daily control. One-bar lead/lag corrections and exposure blends remain in the tables; they do not rescue a consistent quarterly gain.

The five-minute experiment compares 5/15/30/60-minute and whole-session estimates on the same complete positive-volume dates within each company. The first half of dates trains the exposures and the second half tests them. The public tables include an overnight complement and session-block uncertainty. Raw coverage is 37 sessions; Wheaton has 31 complete usable sessions. DRD has insufficient complete sessions. Bar observations are not independent samples.

## PCA identifies shared risk the permitted portfolio misses

In the original seven-company diagnostic spanning December 31, 2009–September 30, 2026, Wheaton's daily explanatory R² rises from 0.568 with gold/silver/broad-equity factors to 0.777 with one peer residual principal component. Three components reach 0.778. One component removes 48.3% of the baseline squared residual error.

Each target is excluded from its PCA inputs. All coefficients and component loadings are fitted on the previous 504 sessions and frozen for the next quarter. Evaluation nevertheless uses contemporaneous peer returns and a fitted statistical intercept. These numbers describe shared company risk; they are neither an investable replica nor a return forecast. They show why treating the remaining error as wholly company-specific noise would be mistaken. The fourteen-name common panel, shortened by OR's listing, is reported separately.

## PCA of permitted assets does not produce a breakthrough

The investable PCA test uses gold, silver, broad equities, Treasury duration, oil and Australian/Canadian currency funds. Component positions map back to fund holdings within exposure limits; gold exposure is estimated separately. Components use uncentered excess-return second moments with past-only RMS scaling; this differs from ordinary centered covariance PCA.

For Wheaton over July 29, 2011–September 30, 2026, keeping two, four or all six extra-asset directions produces daily tracking R² of 0.553, 0.557 and 0.565. Their CAGRs are 3.1%, 1.7% and 6.5%, against 10.4% for the stock. Reducing dimensions does not consistently improve reconstruction and can damage compounding.

The simpler metals and metals-plus-equities portfolios, estimated from recency-weighted daily returns, have daily R² of 0.538 and 0.564. Their CAGRs are 4.7% and 10.0%. The long-history overnight/daytime alternatives do not consistently beat those controls. The remaining error could reflect production growth, acquisitions or valuation changes; these tests do not separate those effects.

## Accounting correction and limits

Independent bookkeeping found a date-unit error inherited from the reused engine, understating borrowing and short fees and misclassifying long calendar gaps. All new accounts charge financing by actual elapsed days. Published v5 results predate this correction; use this edition's corrected overlapping baselines for comparisons.

Positions are fixed adjusted total-return units between trades. The proxy convention includes dividend reinvestment; it is not a verified physical-share and separate cash-dividend ledger. Fund trading costs are 2bp, stressed to 10bp on both owned and replicated accounts. Borrowing costs the cash proxy plus 50bp annually; short funds pay a modeled 1% annual fee. Neither borrow availability nor actual bid/ask execution is established.

All candidates are historical exploratory tests after earlier results, with no untouched historical holdout. Bootstrap intervals condition on fitted paths; they omit parameter refitting and specification-search uncertainty. Long-horizon outcomes overlap. The universe remains survivor-selected despite the separate lifecycle study. Hourly observations cover about two years, with later starts where data are missing. The FactSet tick-history request returned HTTP500, which establishes a service failure, not an entitlement denial. Yahoo quotes supply the short intraday panel. No observed option surface or verified rolled-futures P&L enters this edition.

The downloadable tables retain every candidate, its sample, monthly statistics and cost stress. Methods describe the accounting and causal checks.
