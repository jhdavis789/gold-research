"""Investment-review prose from retained paid-account evidence."""
from pathlib import Path
import json
R=Path(__file__).resolve().parent;P=R/'public'
def main():
 D=json.loads((P/'evidence.json').read_text());Q=json.loads((R/'validation.json').read_text());assert Q['status']=='passed'
 def m(id):return next(z for z in D['metrics'] if z['stock']=='WPM' and z['model']==id)
 previous=next(z['same_date_metrics'] for z in D['prior_v7'] if z['stock']=='WPM');rates=m('conditional_rates_daily_q');priority=m('conditional_options_daily_priority_q');full=m('equity_conditional_options_balanced_q');gold=m('gold_daily_q');risk=m('volatility_gold_q')
 rows=['| Model, quarterly trades | Daily R² | 3-month R² | Annual R² | 5-year R² | CAGR |','|---|---:|---:|---:|---:|---:|']
 for label,id in [('Past-volatility gold','volatility_gold_q'),('Gold tracking control','gold_daily_q'),('Changing metals + rates, daily fit','conditional_rates_daily_q'),('Add options, daily fit','conditional_options_daily_q'),('Options, 80/10/10','conditional_options_daily_priority_q'),('Options, 50/25/25','conditional_options_balanced_q'),('Add broad equities, 50/25/25','equity_conditional_options_balanced_q')]:
  z=m(id);rows.append(f"| {label} | {z['daily_r2']:.3f} | {z['r2_3m']:.3f} | {z['r2_12m']:.3f} | {z['r2_60m']:.3f} | {z['replica_cagr']:.1%} |")
 cohort=[]
 for z in D['comparisons']:
  if not z['new'].endswith('_q'):continue
  cohort.append(f"| {z['test']} | {z['daily_wins']}/{z['companies']} | {z['annual_wins']}/{z['companies']} | {z['median_daily_delta']:+.3f} | {z['median_annual_delta']:+.3f} |")
 profit=[]
 for id in ['volatility_gold_q','gold_daily_q','conditional_rates_daily_q','conditional_options_daily_priority_q','equity_conditional_options_balanced_q']:
  name=next(z['label'] for z in D['models'] if z['id']==id[:-2]);outcomes=[next(z for z in D['profit_by_horizon'] if z['model']==id and z['horizon_months']==h) for h in [12,36,60]]
  profit.append('| '+name+' | '+' | '.join(f"{z['median_company_stock_win_fraction']:.0%}" for z in outcomes)+' |')
 text=f'''# Daily prices help estimate exposure; matching wealth remains harder

Wheaton can be approximated from price behavior with monthly or quarterly trades, but the broadest tested toolkit does not dominate at every horizon. The quarterly metals/rates model has daily tracking R² {rates['daily_r2']:.3f} and annual tracking R² {rates['r2_12m']:.3f}. The daily-priority option model has corresponding R² values of {priority['daily_r2']:.3f} and {priority['r2_12m']:.3f}. Adding broad equities to the balanced option model reaches annual tracking R² {full['r2_12m']:.3f}, with daily R² {full['daily_r2']:.3f}. These are later paid-account outcomes after each estimate, not training fit.

## Wheaton: horizon and return evidence

{chr(10).join(rows)}

Sample: {full['start']}–{full['end']}. Owned-stock CAGR is {full['stock_cagr']:.1%}. The broad-equity extension compounds at {full['replica_cagr']:.1%}, while the daily-priority option model compounds at {priority['replica_cagr']:.1%}. The latter improves a chosen horizon without recreating the stock's cumulative return. Its median absolute annual return gap is {priority['gap_12m_pp']:.1f} percentage points, rising to {priority['gap_60m_pp']:.1f} points over five years. The full extension's gaps are {full['gap_12m_pp']:.1f} and {full['gap_60m_pp']:.1f} points.

The preserved v7 daily-focused metals-plus-equities account has daily tracking R² {previous['daily']['r2']:.3f} and annual R² {previous['horizons'][2]['tracking_r2']:.3f} on Wheaton's same dates. The new balanced extension improves annual tracking while losing daily fit versus that earlier account. It does not dominate the previous study.

The gold risk control targets the stock's previous 252-session volatility, then holds its quantity until the next trade. Its realized volatility is {risk['replica_vol']:.1%}, versus {risk['stock_vol']:.1%} for Wheaton; matching past risk does not ensure equal future risk. The explorer plots stock returns against this gold account and each selected model across overlapping one-, three- and five-year windows.

## Test the toolkit across all twenty companies

Every comparison below uses the same dates within each company and quarterly trades. Counts describe these surviving companies; different companies have different sample lengths. A positive delta is an improvement in tracking R².

| Addition or change | Daily wins | Annual wins | Median daily delta | Median annual delta |
|---|---:|---:|---:|---:|
{chr(10).join(cohort)}

The explorer retains all thirteen fitted definitions, two execution calendars and two past-volatility gold controls: {D['accounts']} paid accounts. No retrospective winner is presented as an ex ante selection rule. The 80/10/10 and 50/25/25 blends test how strongly to prioritize daily identification over longer-horizon tracking.

## Which investment returned more over longer windows?

For each company, calculate the fraction of rolling windows in which the owned stock beats its paired paid replica. The table reports the median company fraction, giving each eligible company one observation. Different horizons can cover different company subsets. This describes return comparisons, not independent significance tests.

| Quarterly-traded comparator | 1-year stock wins | 3-year stock wins | 5-year stock wins |
|---|---:|---:|---:|
{chr(10).join(profit)}

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
'''
 (P/'RESULTS.md').write_text(text)
 (P/'METHODS.md').write_text('''# Price-only exposures with monthly or quarterly holdings

Twenty surviving producers, streamers, royalties and developers use the preserved adjusted daily quote snapshots through September 30, 2026. Common per-company dates include GLD, SLV, TLT, SPY and BIL. Evaluation begins at a month-end after at least 1,008 prior common sessions. Company starts differ. No raw price forward-fill is used; GVZ alone carries its last observation over its calendar.

## Instrument account

Gold and silver are funded bullion-fund proxies. TLT is an explicit Treasury-duration holding; SPY is allowed only in the separately labeled equity extension. BIL supplies cash. Gold target weight is 0–3, silver 0–1.5, Treasury −0.75–0.75 and optional broad equities 0–1. Borrowing costs BIL plus 50 annual basis points; short-TLT fees are 1% annually, accrued by actual calendar days. Fund trading costs are 2 basis points, with 10 in stress. Fixed adjusted fund quantities imply dividend reinvestment; they do not implement futures contract rolls or integer lots.

Sixty modeled option structures span each metal, 3/12/24 calendar-month tenors and entry strikes at 80/100/120% of spot: 36 calls/puts and 24 bounded debit spreads. The two spread legs are priced, charged and counted separately. No naked short-option position is allowed. Gross fund/underlying-leg notional is at most five times capital; option premium at most 30%. At execution, option units are reduced if actual modeled premiums exceed the decision's prior-close estimate. Decision and executed weights are both preserved.

European Black–Scholes marks use entry strikes and fixed expiry dates. Gold uses observed GVZ when available; before GVZ, trailing realized volatility ×1.25. Silver uses trailing 63-session realized volatility ×1.25, with at least 40 observations; initialization is 20% gold/30% silver. This single volatility per metal/date is an assumed surface across all strikes and tenors. The cash-yield estimate uses prior 21-session BIL returns. Each contract fixes its payoff at the final observed close on/before expiry, settles once into cash and incurs no settlement spread. Later spot moves cannot resurrect the contract. Live exits and entries cost 5% of absolute leg marks, with 10% in stress. All contracts are rolled only on scheduled dates; terminal liquidation is charged.

## Estimation and changing exposure

At a scheduled date, train on the preceding 1,008 common sessions, excluding the execution date. The training account applies a constant candidate allocation at historical monthly/quarterly dates, holds fixed adjusted fund and option quantities between trades and pays borrowing, Treasury-short fees, fund turnover and modeled option-leg spreads. Its daily percentage returns and compounded 3/12-month returns come from the same funded cash ledger. A partial final past holding segment is retained without artificial cutoff liquidation. Deployed allocations are re-estimated at each future scheduled date. The target during fitting is before one-time stock entry/exit fees; the owned-stock evaluation pays those fees.

Recency weights have a 252-session half-life. Conditional fits also weight entry states by their similarity to the latest available state: 126-session gold trend, 63-session gold realized volatility, 21-session cash yield and the stock's past 126-session gold beta. Standardization uses training states only. Similarity is exp(−0.5 × mean squared standardized distance), with floor 0.25. The company's own past returns may estimate exposure; no future target or peer observations enter paid decisions.

Daily-only fits use daily squared return error normalized by target training variance. The balanced criterion allocates 50% to daily, 25% to rolling three-month and 25% to rolling annual normalized squared errors. The daily-priority criterion uses 80/10/10. Their long-horizon targets overlap. A fixed 0.01 squared-notional penalty discourages non-gold coordinates; option structures receive twice their squared leg count. This is a tracking criterion, not a profit objective.

SLSQP is constrained during fitting. Gold, previous and feasible parent candidates are retained; the lowest finite feasible objective wins, including the numerical solution when feasible. Results include solver and fallback statuses. Nesting is a feasible-criterion check, not a global-optimality certificate or an out-of-sample dominance guarantee. Every source hash and trial definition is retained. The thirteen definitions × two calendars give 520 fitted accounts. Forty separate volatility-gold controls use the previous 252 daily excess-return standard deviations, capped at three times capital. Their realized risk is shown independently.

## Measurements and diagnostic PCA

Daily returns omit gaps longer than four calendar days. Month-end and 3/12/36/60-month returns compound the same NAV. Tracking R² = 1 − squared return-error sum / stock demeaned squared-return sum. Regression correlation squared is separately retained and can be larger: it does not test return scale or drift. Median absolute gaps are percentage-point total-return differences. Annualized growth uses actual elapsed calendar days. Fresh-window reentry costs are not added to ongoing-NAV rolling windows.

The shared-factor translation reuses the preserved seven-company v7 leave-target-out peer contribution. At quarter ends, the previous 504 sessions fit that response to allowed fund and modeled option increments. Training-RMS standardized coordinates have ridge penalty 0.01; an intercept is allowed. Evaluation uses contemporaneous market movements with past-fitted coefficients. These signed unconstrained coefficients provide explanatory tracking, never paid wealth. All four diagnostic families and seven targets are reported.

Checks include an independent contract/cash ledger, expiry and bounded-payoff cases, derivatives versus finite differences, native/Python kernel agreement, future-data shocks, premium caps, cutoffs, exact retained-path replay, horizon arithmetic, nested criteria and cost stress. All paid accounts and trial outcomes remain visible. Sequential research and surviving-company selection limit inference; no new independent years are created by finer bars or overlapping windows.
''')
 (P/'SOURCES.md').write_text('''# Source coverage and limitations

Preserved Yahoo chart JSON snapshots supply adjusted daily fund and stock prices through September 30, 2026. Public files contain derived research, not vendor quote archives. Back-adjusted histories are revised observations and this universe contains surviving companies. Per-company evaluation dates appear in every result row. Older source editions remain preserved.

Gold volatility uses [Cboe GVZ](https://www.cboe.com/us/indices/dashboard/gvz/), a thirty-day implied-volatility measure for gold through GLD options. It is not a historical option chain across the strikes and maturities used here. Silver and pre-GVZ gold volatility use explicit trailing-realized assumptions. Option marks and spreads are hypothetical. BIL, GLD, SLV, TLT and the separately allowed SPY provide funded returns, not contract-specific futures.

The October 7 historical GLD chain probe used the official [FactSet Options chain endpoint](https://github.com/FactSet/enterprise-sdk/blob/main/code/python/FactSetOptions/v1/docs/OptionChainsScreeningApi.md) for September 30, 2025. Existing access returned HTTP 403; no historical option executions or surface were obtained. Local access receipts and raw response remain private. No paid data was purchased.

The earlier [intraday edition](https://jhdavis789.github.io/gold-research/replication-v7/) retains recent hourly and five-minute evidence and the leave-target-out PCA source. This edition uses longer daily history for paid construction and a separate translation of that shared residual. The earlier [valuation/margin experiment](https://jhdavis789.github.io/gold-research/replication-v3/FUNDAMENTALS.md) uses filing-known annual observations and remains separate.

Actual futures replication requires contract settlements, expiry and roll rules, collateral, margin and transaction costs. Option replication also requires historical executable prices. Those requirements remain open. Modeled fit is evidence about this instrument representation and sample; it is not proof of an executable strategy or a causal model of the business.
''')
 print('Reports written')
if __name__=='__main__':main()
