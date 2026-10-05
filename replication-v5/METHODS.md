# Financing correction

The new [v7 evidence](../replication-v7/) corrects actual-day financing and long-calendar-gap filtering. The two daily-calibrated explorer choices are updated. Other v5 results remain a preserved historical edition and are not represented as recalculated here.

# Daily company replication: methods and boundaries

This is the next research pass after the monthly-calibrated v3/v4 studies. Source cutoff September 30, 2026. Twenty surviving USD-listed companies. All comparisons use each company's same available dates; shorter histories remain explicit.

## What changes

Use daily excess returns to estimate exposures, but trade monthly or calendar quarterly. Fund shares and option quantities stay fixed between trades. Daily estimates use 504/252/126 sessions, or756 sessions weighted with 126-session half-life. Recent estimates stop at the previous session. The stale controls stop at the previous month end. A50/50 short/long exposure blend and a past-only top-three metals blend are preserved as separate candidates. The adaptive rule scores candidates using up to 504 preceding sessions of net returns and needs 252 observations before selection; before then it uses the fixed504-session metals rule. Its selected exposures are averaged and traded quarterly, so it is not a hindsight average of subsequent returns.

The initial18 candidates and adaptive rule were declared before performance computation. Five no-shrink option fits were declared after initial results to test penalty sensitivity. Two original-silver-bound controls followed to test the importance of relaxed limits and recency. Total 26 new portfolio rules plus three retained v4 baselines. All are disclosed. The post-2020 and post-2023 sections are retrospective checks, not genuinely untouched test sets. Parameter estimation is past-only, but strategy design benefits from previous historical research.

## Fitting versus execution

Minimize weighted daily excess-return errors without an intercept, with fixed variance-scaled shrinkage on exposures beyond gold. Penalty is0.01 times weighted target excess-return second moment; option coefficients receive twice that penalty. Raw-convexity candidates set it to zero. Fund factors are asset returns minus BIL. Option features are dollar gains on quarterly-fixed hypothetical calls divided by the preceding underlying price, less the premium's cash opportunity cost. This is a local normalized P&L fitting criterion, not a claim that training recreates exact ongoing-portfolio percentage returns. Evaluation uses the explicit self-financing account below. Option strike and tenor are set at each quarter's start and daily marks retain that contract until the next trade.

A bounded quadratic optimizer solves the same weighted least-squares objective after a platform least-squares residual routine emitted floating-point warnings on finite small inputs. The warning-producing sources and outputs remain in a private archive; corrected runs are the published results. The feasible gold-only solution is a fallback if the candidate's penalized objective is worse. Bound projections and the blended rule do not certify a global constrained optimum. The blend's own training objective need not beat a standalone gold fit.

Gold weight is0–3× NAV, silver0–1.5× (matched controls0–1×), broad equities0–1×, Treasuries/oil/AUD/CAD each−0.5–0.5×. Options are long calls on gold and silver,0–2 underlying-equivalent units each with combined 2 cap. Total absolute fund and option underlying-equivalent exposure is capped 5. Actual option delta differs from underlying-equivalent notional. These static limits preserve a gold-only feasible choice but do not equalize every strategy's realized risk.

## Account mechanics and option hypotheses

Fund prices are dividend/split-adjusted GLD, SLV, SPY, TLT, USO, FXA and FXC; BIL is the cash proxy. At each trade, dollar weights set fixed fund quantities. Paid option quantities equal target underlying-equivalent exposure times NAV divided by spot. Cash equals NAV less funded shares, option premiums and costs. Negative cash earns/pays the BIL change plus a50 bp annual spread. Short funds additionally pay1% annual borrow fees; availability is assumed. No short-option writing. Fund trades cost2 bp and options pay5% of premium on purchase and sale. Final liquidation is charged. Higher-cost replay uses 10 bp fund costs and 10% option premium spreads with the same decisions.

Calls have3-month ATM,12-month ATM,12-month80%-strike or24-month80%-strike definitions. Gold marks use GVZ and silver uses 63-day annualized realized volatility times 1.25, floored at 5%. Both assume a flat Black-Scholes surface and a lagged21-session BIL financing-rate proxy frozen for each contract. Actual daily remaining time drives theta; calls are sold/replaced quarterly even when maturity is longer. Long-tenor surfaces, actual historical quotes and execution are not validated. USO is an oil-futures fund, not spot oil; currency ETFs are broad cost-currency proxies, not mine-specific hedges. Broader-factor models are not gold-only replicas.

Only GVZ may forward-fill. Inputs otherwise use aligned observed closes. Daily changes spanning over four calendar days are omitted from fitting and daily statistics; monthly NAV retains their full cumulative movement. Vendor revised histories, sample survival, ADR timing and business changes limit interpretation. No current filing ratio is backfilled into the historical estimates.

## Metrics and diagnostics

Tracking R² is1−sum((stock−portfolio daily or monthly return)^2)/sum((stock−sample mean stock return)^2). It can be negative. Regression R² is squared correlation, separately labeled. Monthly returns compound the same daily NAV. Stock paths include2 bp initial and terminal costs. Reported portfolio CAGR is realized growth of the modeled account; a good daily R² does not guarantee its long-run return matches the company.

The two separate explanatory models include an intercept and quarterly-frozen coefficients estimated from past daily observations. They explain a day's stock return using that day's realized factor moves; the nonlinear version adds gold², silver² and gold×silver. They are not next-day forecasts, investable replicas or universal upper bounds. Their intercept and nonlinear payoffs are never credited as portfolio earnings.

For Wheaton, a circular 12-month block bootstrap with 3,000 resamples estimates a descriptive range for paired squared-daily-error reduction versus the old gold/silver model. Shared time blocks retain some serial dependence; the range does not correct specification search or data revisions. Twenty-company means weight each company equally and use different available history lengths. We do not count companies or daily observations as independent experiments.

## Verification

All 580 paths checked for positivity, matching dimensions, statistics, higher-cost outcomes and daily-to-monthly reconciliation. Eighteen base candidates pass future-market/target perturbation checks. Independent blockwise cash/share accounting agrees with the main engine. Zero-option embedding reproduces the linear account. Decision dates are month ends and quarterly rules use calendar quarters after the initial entry. No outgoing email was sent in this research pass.
