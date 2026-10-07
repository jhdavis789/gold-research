# Daily prices help estimate exposure; matching wealth remains harder

Wheaton can be approximated from price behavior with monthly or quarterly trades, but the broadest tested toolkit does not dominate at every horizon. The quarterly metals/rates model has daily tracking R² 0.537 and annual tracking R² 0.728. The daily-priority option model has corresponding R² values of 0.524 and 0.741. Adding broad equities to the balanced option model reaches annual tracking R² 0.805, with daily R² 0.525. These are later paid-account outcomes after each estimate, not training fit.

## Wheaton: horizon and return evidence

| Model, quarterly trades | Daily R² | 3-month R² | Annual R² | 5-year R² | CAGR |
|---|---:|---:|---:|---:|---:|
| Past-volatility gold | 0.368 | 0.564 | 0.655 | 0.630 | 5.4% |
| Gold tracking control | 0.491 | 0.600 | 0.724 | 0.672 | 7.0% |
| Changing metals + rates, daily fit | 0.537 | 0.645 | 0.728 | 0.623 | 4.3% |
| Add options, daily fit | 0.536 | 0.639 | 0.713 | 0.523 | 1.2% |
| Options, 80/10/10 | 0.524 | 0.638 | 0.741 | 0.623 | 3.2% |
| Options, 50/25/25 | 0.490 | 0.627 | 0.726 | 0.634 | 3.2% |
| Add broad equities, 50/25/25 | 0.525 | 0.658 | 0.805 | 0.914 | 10.3% |

Sample: 2011-07-29–2026-09-30. Owned-stock CAGR is 10.4%. The broad-equity extension compounds at 10.3%, while the daily-priority option model compounds at 3.2%. The latter improves a chosen horizon without recreating the stock's cumulative return. Its median absolute annual return gap is 12.8 percentage points, rising to 32.9 points over five years. The full extension's gaps are 10.8 and 12.7 points.

The preserved v7 daily-focused metals-plus-equities account has daily tracking R² 0.564 and annual R² 0.747 on Wheaton's same dates. The new balanced extension improves annual tracking while losing daily fit versus that earlier account. It does not dominate the previous study.

The gold risk control targets the stock's previous 252-session volatility, then holds its quantity until the next trade. Its realized volatility is 40.9%, versus 39.7% for Wheaton; matching past risk does not ensure equal future risk. The explorer plots stock returns against this gold account and each selected model across overlapping one-, three- and five-year windows.

## Test the toolkit across all twenty companies

Every comparison below uses the same dates within each company and quarterly trades. Counts describe these surviving companies; different companies have different sample lengths. A positive delta is an improvement in tracking R².

| Addition or change | Daily wins | Annual wins | Median daily delta | Median annual delta |
|---|---:|---:|---:|---:|
| Rates | 10/20 | 7/20 | -0.000 | -0.004 |
| Changing exposure | 15/20 | 11/20 | +0.001 | +0.001 |
| Options | 9/20 | 7/20 | -0.001 | -0.010 |
| Conditional options | 8/20 | 6/20 | -0.001 | -0.012 |
| 80/10/10 horizon blend | 1/20 | 5/20 | -0.014 | -0.034 |
| 50/25/25 horizon blend | 0/20 | 2/20 | -0.043 | -0.079 |
| 80/10/10 option blend | 1/20 | 6/20 | -0.016 | -0.013 |
| 50/25/25 option blend | 0/20 | 4/20 | -0.044 | -0.060 |
| Broad equities | 20/20 | 10/20 | +0.012 | -0.004 |

The explorer retains all thirteen fitted definitions, two execution calendars and two past-volatility gold controls: 560 paid accounts. No retrospective winner is presented as an ex ante selection rule. The 80/10/10 and 50/25/25 blends test how strongly to prioritize daily identification over longer-horizon tracking.

## Which investment returned more over longer windows?

For each company, calculate the fraction of rolling windows in which the owned stock beats its paired paid replica. The table reports the median company fraction, giving each eligible company one observation. Different horizons can cover different company subsets. This describes return comparisons, not independent significance tests.

| Quarterly-traded comparator | 1-year stock wins | 3-year stock wins | 5-year stock wins |
|---|---:|---:|---:|
| Gold past-volatility control | 45% | 46% | 44% |
| Gold tracking control | 44% | 41% | 44% |
| Changing metals + rates · daily fit | 43% | 42% | 43% |
| Changing metals + rates + options · 80/10/10 | 48% | 50% | 51% |
| Add broad equities · 50/25/25 | 46% | 46% | 48% |

The prior-volatility comparator is the relevant test for comparable historical risk; the fitted replicas instead prioritize matching returns. Neither produces exact equal future volatility. Borrowing, exposure limits and company-specific risk also affect the comparison. The explorer and full rolling CSV show where each company under- or outperformed.

## More options cannot guarantee better later returns

For ordinary least squares on identical observations, adding unconstrained regressors cannot worsen the best in-sample R². These paid fits minimize a cost-aware, regularized return-error criterion with exposure and premium limits. A zero-option portfolio remains feasible; the retained objective never worsens against its feasible gold/parent candidate on the identical criterion. Nonconvex optimization does not certify the global optimum. Neither nesting nor more tools guarantees better out-of-sample tracking, unpenalized R² or wealth.

The revised fitting account pays the same hypothetical roll spreads and financing as the deployed account. The earlier pre-cost Wheaton experiment is retained separately in WPM-precost-comparison.csv. Options add delta and curvature, but also time decay, volatility exposure and roll costs. A finite-expiry metal option need not share the return behavior of a company with changing assets and market valuation. This intuition motivates the test; it is not a measured cause of the residual.

## A shared residual is not yet a replicating instrument

In the earlier seven-company diagnostic, adding one leave-target-out peer component reduced Wheaton's daily squared tracking error by 48.3%. Translating that leave-target-out contribution into permitted fund and modeled option movements fails in this follow-up: all 28 frozen-coefficient diagnostic tracking R² values are negative. The response was already residualized against metals and broad equities, so weak linear translation is unsurprising. The option basis also fails to establish a useful translation. Signed statistical coordinates, fitted intercepts and contemporaneous peer outcomes provide no paid-portfolio return claim. This does not identify the economic cause or establish an unhedgeable limit.

## Scope and uncertainty

The one- and five-year return comparisons compound each paid daily NAV. Overlapping windows are descriptive; they are not independent annual samples. Wheaton's paired squared-error intervals use twelve-month blocks for daily tracking and twenty-four-month blocks for annual tracking. They condition on fitted paths and do not cover model-search or re-estimation uncertainty. This edition follows earlier results and the pre-cost option trial; it has no untouched holdout.

The option marks are illustrative European prices. Gold GVZ is a thirty-day volatility measure, not the historical strike/tenor surface; silver volatility uses a trailing realized-volatility assumption. FactSet's historical chain request returned HTTP 403 with the existing access. Funded GLD/SLV proxies and modeled marks cannot establish contract-level futures or executable option performance.

The earlier [filing-known valuation and margin study](https://jhdavis789.github.io/gold-research/replication-v3/FUNDAMENTALS.md) remains a separate timing experiment. This price-only edition does not refresh those fundamentals, identify supply causality, or infer that all miners destroy value. The explorer compares each retained stock's returns with its paid replicas across horizons.
