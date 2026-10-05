"""Write the investment findings directly from checked derived outputs."""
from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parent
def main():
 D=json.loads((R/'public/evidence.json').read_text());Q=json.loads((R/'validation.json').read_text())
 def met(group,model):return next(r for r in D['metrics'] if r['stock']=='WPM' and r['group']==group and r['model']==model)
 def agg(group,model):return next(r for r in D['aggregates'] if r['group']==group and r['model']==model)
 short=[met('hourly',x) for x in ['daily_metals_m','intraday_metals_m','realized_metals_m']];long=[met('sessions',x) for x in ['daily_ew_metals','daily_ew_market']]
 pc=next(r for r in D['pca'][1]['statistics'] if r['stock']=='WPM');b=next(r for r in D['wpm_portfolio_bootstrap'] if r['model']=='realized_metals_m');pca=[met('asset-pca',x) for x in ['asset_pca2','asset_pca4','asset_pca6']]
 text=f'''# Intraday estimates add little; peer returns explain much of Wheaton's residual risk

Intraday estimation gives a small, uncertain recent improvement. Peer principal components explain a much larger share of Wheaton's residual movement, but the permitted-asset portfolios tested here do not reproduce that gain. The tests cover twenty companies and {D['portfolio_rules']} portfolio rules, with financing and trading costs included. Portfolios still trade monthly or quarterly.

## Intraday estimates need the overnight component

Wheaton's matched April 30, 2025–September 30, 2026 monthly-traded metals accounts have daily tracking R² of {short[0]['daily_r2']:.3f} using daily calibration, {short[1]['daily_r2']:.3f} using hourly daytime calibration, and {short[2]['daily_r2']:.3f} using hourly plus overnight covariance. The last improves paired squared error by {b['sse_reduction']:.1%}, with a three-month-block interval of {b['interval95'][0]:.1%} to {b['interval95'][1]:.1%}. This short, recent sample does not establish a dependable improvement.

Across the twenty respective paired histories, monthly-traded metals' average daily R² is {agg('hourly','daily_metals_m')['mean_daily_r2']:.3f} for daily calibration and {agg('hourly','realized_metals_m')['mean_daily_r2']:.3f} with hourly plus overnight covariance. {agg('hourly','realized_metals_m')['wins']} companies improve. Quarterly intraday-only metals estimation improves zero companies against its matched daily control. One-bar lead/lag corrections and exposure blends remain in the tables; they do not rescue a consistent quarterly gain.

The five-minute experiment compares 5/15/30/60-minute and whole-session estimates on the same complete positive-volume dates within each company. The first half of dates trains the exposures and the second half tests them. The public tables include an overnight complement and session-block uncertainty. Raw coverage is 37 sessions; Wheaton has 31 complete usable sessions. DRD has insufficient complete sessions. Bar observations are not independent samples.

## PCA identifies shared risk the permitted portfolio misses

In the original seven-company diagnostic spanning December 31, 2009–September 30, 2026, Wheaton's daily explanatory R² rises from {pc['baseline']['tracking_r2']:.3f} with gold/silver/broad-equity factors to {pc['one_peer_pc']['tracking_r2']:.3f} with one peer residual principal component. Three components reach {pc['three_peer_pcs']['tracking_r2']:.3f}. One component removes {pc['residual_sse_reduction_pc1']:.1%} of the baseline squared residual error.

Each target is excluded from its PCA inputs. All coefficients and component loadings are fitted on the previous 504 sessions and frozen for the next quarter. Evaluation nevertheless uses contemporaneous peer returns and a fitted statistical intercept. These numbers describe shared company risk; they are neither an investable replica nor a return forecast. They show why treating the remaining error as wholly company-specific noise would be mistaken. The fourteen-name common panel, shortened by OR's listing, is reported separately.

## PCA of permitted assets does not produce a breakthrough

The investable PCA test uses gold, silver, broad equities, Treasury duration, oil and Australian/Canadian currency funds. Component positions map back to fund holdings within exposure limits; gold exposure is estimated separately. Components use uncentered excess-return second moments with past-only RMS scaling; this differs from ordinary centered covariance PCA.

For Wheaton over July 29, 2011–September 30, 2026, keeping two, four or all six extra-asset directions produces daily tracking R² of {pca[0]['daily_r2']:.3f}, {pca[1]['daily_r2']:.3f} and {pca[2]['daily_r2']:.3f}. Their CAGRs are {pca[0]['portfolio_cagr']:.1%}, {pca[1]['portfolio_cagr']:.1%} and {pca[2]['portfolio_cagr']:.1%}, against {pca[2]['stock_cagr']:.1%} for the stock. Reducing dimensions does not consistently improve reconstruction and can damage compounding.

The simpler metals and metals-plus-equities portfolios, estimated from recency-weighted daily returns, have daily R² of {long[0]['daily_r2']:.3f} and {long[1]['daily_r2']:.3f}. Their CAGRs are {long[0]['portfolio_cagr']:.1%} and {long[1]['portfolio_cagr']:.1%}. The long-history overnight/daytime alternatives do not consistently beat those controls. The remaining error could reflect production growth, acquisitions or valuation changes; these tests do not separate those effects.

## Accounting correction and limits

Independent bookkeeping found a date-unit error inherited from the reused engine, understating borrowing and short fees and misclassifying long calendar gaps. All new accounts charge financing by actual elapsed days. Published v5 results predate this correction; use this edition's corrected overlapping baselines for comparisons.

Positions are fixed adjusted total-return units between trades. The proxy convention includes dividend reinvestment; it is not a verified physical-share and separate cash-dividend ledger. Fund trading costs are 2bp, stressed to 10bp on both owned and replicated accounts. Borrowing costs the cash proxy plus 50bp annually; short funds pay a modeled 1% annual fee. Neither borrow availability nor actual bid/ask execution is established.

All candidates are historical exploratory tests after earlier results, with no untouched historical holdout. Bootstrap intervals condition on fitted paths; they omit parameter refitting and specification-search uncertainty. Long-horizon outcomes overlap. The universe remains survivor-selected despite the separate lifecycle study. Hourly observations cover about two years, with later starts where data are missing. The FactSet tick-history request returned HTTP500, which establishes a service failure, not an entitlement denial. Yahoo quotes supply the short intraday panel. No observed option surface or verified rolled-futures P&L enters this edition.

The downloadable tables retain every candidate, its sample, monthly statistics and cost stress. Methods describe the accounting and causal checks.
'''
 (R/'RESULTS.md').write_text(text);shutil.copy2(R/'RESULTS.md',R/'public/RESULTS.md');shutil.copy2(R/'DESIGN.md',R/'public/METHODS.md');shutil.copy2(R/'FOLLOWUP.md',R/'public/FOLLOWUP.md')
 with (R/'public/METHODS.md').open('a') as f:f.write(f'\n## Verification and corrections\n\n{len(Q["checks"])} checks pass across {Q["portfolio_accounts"]} accounts and {Q["fit_records"]} fit records. Independent actual-day bookkeeping matches account NAVs within1.8e-13. Timestamp resolution is normalized before asi8 day calculations; future shocks cannot change earlier decisions. The earlier engine assumed nanoseconds when some indexes stored microseconds, understating financing and short fees. This edition corrects elapsed-time accounting and long-gap masks. Positions are fixed adjusted total-return units; dividends are implicitly reinvested.\n\nSmall two/three-factor constrained fits enumerate all convex box faces, eliminating numerical line-search failures. Permitted-asset PCA uses standardized uncentered excess-return second moments, a separately estimated gold coordinate and linear physical bounds/gross cap. All six extra components span the full-factor control. Each target is omitted from its own diagnostic peer components; contemporaneous peer returns and statistical intercepts have no investable profit interpretation.\n')
 (R/'public/SOURCES.md').write_text('''# Sources and measurement

Daily total-return and raw open/close snapshots: registered Yahoo chart family, issuer-specific coverage through September30,2026. Hourly raw OHLCV: October7,2024–September30,2026; five-minute raw OHLCV: August10–September30,2026. Securities are synchronized to exact New York regular-session bar grids; incomplete or zero-volume grids are excluded, prices are never forward-filled. Recent sampling can contain trade-price and timing noise. Private raw replies and quote levels are not redistributed.

Existing GLD/SLV/BIL/SPY/TLT/USO/FXA/FXC history supplies funded proxies. Cash and financing accrue by actual elapsed days. Adjusted total-return units imply dividend reinvestment. Portfolio results include modeled costs; explanatory PCA diagnostics contain no investable wealth claim. No miner index or peer stock is held in a replica.

[FactSet official tick-history schema](https://github.com/FactSet/enterprise-sdk/blob/main/code/python/FactSetIntradayTickHistory/v1/docs/TickHistoryApi.md): bounded existing-subscription request returned HTTP500; no FactSet intraday data entered the calculations. [Realized-beta research](https://www.nber.org/papers/w11134) motivates measuring covariance at finer frequencies; this implementation is a finite-sample experimental comparison, not a microstructure-noise-consistent estimator.

The source registry, local receipt hashes, complete trial definitions and accounting checks are preserved in the research project. Shared-stock PCA uses contemporaneous peer observations solely to diagnose omitted common risk; targets are excluded from their component inputs.
''')
 print(text.split('## Accounting')[0])
if __name__=='__main__':main()
