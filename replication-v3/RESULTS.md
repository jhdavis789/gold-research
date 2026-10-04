# Version 3 quantitative findings

The study retains 14 surviving producers and streamers and 16 fixed candidate families. Funded GLD/BIL results reach 16.2 evaluation years for the longest eligible stock. Individual starts are shown below. The original seven stocks and versions 1–2 remain preserved.

Every option result below uses hypothetical Black-Scholes/GVZ prices. Historical observed option execution and actual rolled futures are unavailable in this quantitative implementation; see the separate access report. This limits implementation conclusions.

## Honest paired-period replication

Comparisons below start at the longest required start among the 24-month replication and 36-month risk candidates for each stock. Gold 60-month estimation is a later-start sensitivity and is excluded from this common-start construction. Monthly return tracking R² penalizes level and scale errors; it is not squared correlation.

| Stock | Start / months | Gold Q R² | Gold+options Q R² | Gold+silver+options Q R² | Risk-matched Q R² |
|---|---|---:|---:|---:|---:|
|NEM|2010-08 / 194|0.476|0.467|0.453|0.380|
|AEM|2010-08 / 194|0.521|0.499|0.448|0.412|
|B|2010-08 / 194|0.492|0.486|0.474|0.437|
|AU|2010-08 / 194|0.569|0.554|0.511|0.571|
|FNV|2011-02 / 188|0.532|0.532|0.521|0.467|
|WPM|2010-08 / 194|0.572|0.573|0.579|0.504|
|RGLD|2010-08 / 194|0.523|0.516|0.504|0.456|
|GFI|2010-08 / 194|0.550|0.545|0.512|0.548|
|KGC|2010-08 / 194|0.452|0.458|0.431|0.419|
|HMY|2010-08 / 194|0.435|0.446|0.418|0.430|
|EGO|2010-08 / 194|0.318|0.304|0.302|0.288|
|IAG|2010-08 / 194|0.415|0.393|0.373|0.402|
|BTG|2011-08 / 182|0.419|0.413|0.405|0.402|
|OR|2019-09 / 85|0.555|0.555|0.513|0.444|

## Wheaton focus

On its paired period, WPM gold-only monthly tracking R² is 0.570; gold+silver monthly is 0.580; illustrative gold-options monthly is 0.570; gold+silver+options monthly is 0.577. Their annualized tracking errors are respectively 27.7%, 27.4%, 27.7%, 27.5%. These are fixed candidate comparisons, not a fitted target or a promise of stable future performance.

## Past-only risk matching and fresh accounts

The risk benchmark estimates the trailing 36-month stock/gold monthly-volatility ratio using a full-month information gap. It caps gold at three times NAV, then holds share quantities between monthly/quarterly trades. Realized volatility can differ from the stock, particularly at the cap and through drift. No future target volatility sets exposure.

| Stock | Full-period risk Q CAGR | Stock CAGR | Risk Q vol | Stock vol | Median 5-year stock minus risk Q CAGR | Stock wins / overlapping windows / disjoint count |
|---|---:|---:|---:|---:|---:|---|
|NEM|15.7%|6.9%|37.0%|36.6%|-0.2 pp|49.6% / 135 / 3|
|AEM|14.9%|9.4%|42.9%|42.2%|-5.4 pp|40.0% / 135 / 3|
|B|15.0%|1.7%|40.0%|41.7%|-8.4 pp|13.3% / 135 / 3|
|AU|16.6%|6.8%|42.9%|54.0%|-7.4 pp|27.4% / 135 / 3|
|FNV|11.3%|16.0%|33.2%|32.2%|+6.0 pp|71.3% / 129 / 3|
|WPM|11.7%|14.2%|43.5%|42.3%|+2.2 pp|66.7% / 135 / 3|
|RGLD|12.6%|12.2%|39.7%|40.5%|-0.6 pp|48.1% / 135 / 3|
|GFI|16.5%|9.7%|42.5%|54.8%|+0.6 pp|50.4% / 135 / 3|
|KGC|17.6%|3.3%|43.0%|52.6%|-6.0 pp|17.8% / 135 / 3|
|HMY|15.5%|4.6%|43.6%|67.9%|-4.3 pp|28.1% / 135 / 3|
|EGO|13.9%|-4.3%|45.5%|56.2%|-18.4 pp|6.7% / 135 / 3|
|IAG|14.5%|1.4%|47.1%|59.2%|-10.6 pp|25.9% / 135 / 3|
|BTG|9.1%|4.4%|44.5%|50.5%|-2.0 pp|48.8% / 123 / 3|
|OR|27.9%|16.4%|41.3%|37.9%|-7.9 pp|11.5% / 26 / 1|

## Sequential silver-option extension

At the later user request, five further both-metal option hypotheses were frozen and evaluated. Silver prices are hypothetical premiums using past-only realized volatility times a fixed multiplier; the extra candidates are sequential research, with the initial 11-family snapshot and ledger preserved. The grid has eight option coefficients and stronger shrinkage.

| WPM added family | Paired R² | Tracking error |
|---|---:|---:|
|gold_silver_both_options_monthly|0.568|27.8%|
|gold_silver_both_options_quarterly|0.574|27.6%|
|gold_silver_both_options_monthly_rv1|0.562|28.0%|
|gold_silver_both_options_quarterly_rv1|0.573|27.6%|
|gold_silver_both_options_grid_quarterly|0.576|27.5%|

## Nested-fit verification

All 18,153 augmented fits preserve a feasible zero-extra baseline; retained unpenalized mean tracking SSE never exceeds that baseline within 1e-12. The in-sample global optimum has this property because the baseline feasible set is a subset of the augmented feasible set. The implementation retains the baseline whenever a numerical candidate is worse. This is a best-known numerical guarantee, not a global solver certificate.

The deployed fixed 0.0002 penalty on extra exposure prioritizes stability. It may produce higher unpenalized SSE than the best raw augmented candidate. Out-of-sample R² may also worsen. Neither is a contradiction of nesting. All 25,823 scheduled fits and candidate definitions are retained; no candidate was discarded because of its evaluated performance.

## Verification and limitations

Behavioral tests cover future perturbations, fixed quantities, cash financing, entry/exit charges, paid option premium, actual-return tracking R², zero-option embedding and the remaining-life option mark at truncated endpoints. The source snapshots are revised vendor histories. The universe has survivorship bias; shorter OR history cannot support a 10-year holding window. Costs are assumptions; drawdowns use monthly marks.

Each reported horizon starts a fresh account, uses decisions available at its entry, and pays entry/exit costs. All overlapping 1/3/6/12/36/60/120-month windows are preserved. Disjoint counts describe available windows, not independent statistical samples. The 12-month block bootstrap measures realized relative growth uncertainty; it does not re-estimate exposure or remove model-selection and source-history uncertainty.

Costsensitivity keeps the fitted rules fixed at 0/2/10bp fund trade costs. It is not a reoptimized strategy. No fitted alpha, miner index or peer-equity return enters any replicating portfolio.
