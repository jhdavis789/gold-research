# Basket ownership, percentiles and lifecycle sensitivity

## Selected-company account

The twenty checkboxes, x-axis technique and date controls govern an equal-dollar company basket and its matched replica basket. Start on the first available selected session on or after the requested date. A company is eligible only once its original model-evaluation history exists. These dates include estimation warmup; they are not IPO dates. No future return is used to admit a member.

Buy-and-hold starts with equal dollars in eligible companies and never admits later entrants. Monthly mode resets equal weights at each month-end and admits newly eligible selected names at that time. Underlying company replicas continue their original internal schedules: buying units of an ongoing account does not refit it. The two baskets target the same fractional allocations, each against its own wealth. They are not daily equal-weight indices.

The optional additional basket cost is charged per dollar bought or sold, including entry and exit. Existing company/replica path costs remain embedded. Rebalance targets are reduced proportionally to fund fees, with no external contribution or extra borrowing. The plot starts at $100 before entry cost. An allocation at a closing mark is followed by its fee in the next interval. Missing isolated session marks are carried from the latest available observation for account valuation, rather than treated as a fresh quotation. Individual-company daily statistics retain their prior gap exclusions.

Daily basket tracking R² uses the resulting paired daily returns and the same unrefitted 1−SSE/SST definition as the company chart. The measurement-frequency selector for the company chart does not change this explicitly daily basket statistic. CAGR uses actual elapsed days /365.25. CSV exports the displayed account.

## Distribution and rolling cohorts

Realized ranks are hindsight descriptions, not executable forecasts. Top/bottom decile means 10%; quartile means25%. A tail group contains ceil(N×fraction) names. Ties use ticker order. Groups can overlap in very small samples. Equal dollars in each chosen name means arithmetic-average terminal wealth; annualization happens after that average. The corresponding replica group holds those same company names, not independently chosen winners.

P10/P25/P50/P75/P90 are linearly interpolated cross-sectional thresholds. P50 is the median. The median group holds the middle name, or equal dollars in the two middle names; this reproduces the median total return before annualization. It is still chosen after seeing outcomes. End-to-end distribution tables use the fixed initial cohort even if the account above is set to monthly rebalance. The extra basket cost applies only to that ownership account, not to these distribution diagnostics.

The rolling scatter uses the selected holding period and return display. Each point is a fresh equal-dollar aggregation of the existing ongoing-account holding returns available at that window's start. Original twenty-company paths all end at the common research cutoff. No ending-outcome ranking is described as a rule known at entry. Rolling windows overlap and are not independent.

## Disappeared-company sensitivity

Six additional researched issuers: Sandstorm (SAND), Kirkland Lake (KL), Yamana (AUY), Goldcorp (GG), Golden Star (GSS), and Great Basin (GBG/GBGLF). The lifecycle table links primary corporate, SEC or receiver evidence. The fixed annual cohort comparison is separate from the twenty checkboxes; its year selector explicitly controls it. Entry is the first market session on/after January1, exit September30,2026. Buy and hold the entry basket; no subsequent entrants or rebalancing.

Acquisition consideration is calculated from the contractual cash/share ratios and completion-date acquirer closing prices. Received shares are modeled as sold immediately and the proceeds invested in BIL. This preserves consideration rather than dropping the acquired company, and avoids conflating its full later history with that of its acquirer. Settlement delays, tax, rounding and actual execution are not modeled. The hypothetical replica is liquidated on the last pre-event session and then holds BIL. These exit conventions can produce a final-day timing difference. Company sleeves include the original 2bp entry/exit convention; cohort ratios at later entries do not add a new trade fee. No additional basket turnover costs are applied to this supplemental fixed-cohort table.

Great Basin entered receivership June28,2013. The receiver anticipates no shareholder distribution; a verified final recovery is unavailable. The table reports two scenarios at receivership: zero, and last quoted value converted to BIL. They are neither verified final cashflows nor confidence bounds, and the quoted value may not have been executable. New entry is prohibited from receivership onward in either scenario. This assumption is visible beside every affected cohort result.

Allied Nevada is a documented omission. The former equity was canceled with warrant rights for holders; complete old-security history and recovery valuation remain unresolved. The current ANV symbol maps to an unrelated ETF and was rejected. See [SEC reorganization exhibit](https://www.sec.gov/Archives/edgar/data/1376610/000119312515335285/d190455dex992.htm) and [DTCC effective-date notice](https://www.dtcc.com/-/media/Files/pdf/2015/10/23/OTC-205.pdf).

The daily metals and metals+market replicas reuse the unchanged v5 rules; unlevered gold provides a third comparator. Other techniques show no supplemental replica result, instead of silently substituting another model. New-company eligibility requires 37 month-end observations. SAND data starts at its confirmed August20,2012 US exchange listing; KL at August16,2017. Earlier stitched or OTC history was excluded. Relevant listing evidence: [Sandstorm filing](https://www.sec.gov/Archives/edgar/data/1434614/000110465912058474/a12-18482_16k.htm), [Kirkland filing](https://www.sec.gov/Archives/edgar/data/1713443/000106299317004632/exhibit99-2.htm).

## What the result establishes

For the January2012 entry cohort, 18 eligible members of the original surviving sample compound at7.68% annually. Adding the three acquired names eligible then gives21 names and6.74%; including Great Basin gives22 names and6.41% under either displayed recovery scenario when rounded to two decimals. Other entry years can give different effects. These are research simulations, not live forward returns.

The chosen26 names are not a reconstructed historical gold-industry membership list. Adding five acquisitions and one failure does not eliminate survivorship bias. Small failures, bankrupt restructurings with rights distributions, foreign-only listings, earlier constituents and missing securities remain underrepresented. Eligibility warmup itself excludes young companies and early failures. Historical adjusted data may be revised.

## Sources and reproducibility

Existing twenty-company/proxy inputs are the previous Yahoo daily snapshots. New disappeared-security histories use privately cached FactSet Formula P_NAME, P_PRICE and P_TOTAL_RETURN with permanent identifier/name verification. Raw responses, individual vendor price/return histories, acquisition pricing inputs and normalized individual lifecycle paths stay private; only aggregate cohort research statistics and public lifecycle metadata are published here. API access does not establish redistribution rights. Published cohort summaries are not a raw vendor-data download.

Private build records preserve the frozen design, request/response hashes, terminal consideration ledger, cohort constituents, unchanged model specifications and accounting/browser validations. This package preserves all prior twenty-company series byte-for-byte. Aggregate results are in lifecycle-summary.json; basket calculations are in baskets.js. The earlier [v5 model methods](../replication-v5/METHODS.md) and [original explorer methods](METHODS.md) still apply.
