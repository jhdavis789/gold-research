# Quantitative audit

Core 11 families and subsequent 5 silver-option families remain distinct sequential research stages. The final unified data has 14 stocks, 16 families, 224 full-period summaries, 236,517 fresh-account outcome windows and 25,823 scheduled fit records. Initial core data, ledger and results are preserved. Root-owned futures/data-access, fundamentals and ex-post diagnostics are separate from this implemented proxy engine.

## Objective and nesting

The objective is the mean squared error of actual self-financing monthly replica returns against target-stock holding returns, including matching target entry/exit costs. There is no fitted intercept. The same simulator supplies training and execution: fixed share and option quantities between scheduled trades, paid premiums, cash collateral in a funded fund portfolio, negative-cash financing spread, trade costs and terminal liquidation. Training uses observations ending one full month before entry. Future price and volatility perturbations do not change that decision.

For the unpenalized objective f, let feasible baseline weights be b and define an embedding E(b) by appending zero new-instrument weights. Tested accounting establishes f_baseline(b) = f_augmented(E(b)). The augmented feasible set contains every embedded baseline. Therefore min f_augmented ≤ min f_baseline. Numerical code additionally compares every candidate against E(b) and retains the lower-SSE candidate, guaranteeing recorded best-known fits satisfy the comparison even if a solver is imperfect. This is not a certificate of the global optimum.

The core augmented records embed the unpenalized gold baseline on their exact aligned calendar. The supplemental both-metal records embed an optimized unpenalized gold+silver baseline; baseline_family labels this stronger comparator. Different earliest permissible gold/volatility histories are not silently equated. Paired summaries explicitly show their dates. The 60-month gold sensitivity begins later than the common start of other families and is labeled accordingly.

Deployment uses a fixed extra-exposure penalty. Its raw SSE can exceed the best raw augmented SSE; future SSE can exceed baseline SSE. Neither violates the mathematical in-sample nesting statement. The retained outcomes show this distinction rather than suppressing weaker candidates.

## Accounting checks

Paid option premiums are denominated in each option's own underlying share dollars, debited from cash with their spread, and subsequently valued or paid at expiry. No free gold-square payoff enters NAV. Option expiries follow predetermined monthly calendars even beyond the dataset endpoint; a truncated account pays sale spread on its remaining-life mark. Gold option volatility is GVZ; silver option volatility is explicitly hypothetical realized-volatility-times-multiplier. Neither supplies observed strike/premium/bid/ask execution histories.

The fund-exposure cap refers to target quantity at pre-trade NAV; fees and market movement can change realized leverage. The risk-matched benchmark targets past observed volatility and caps gold exposure at three times NAV. It need not realize exact stock volatility. Cash is a BIL proxy with fund expense already embedded; negative balances incur the fixed additional 50bp annual borrowing spread. No futures margin/roll or integer contracts are inferred from this funded account.

Costsensitivity changes fund-trade cost between 0/2/10bp, holding fitted quantities/rules fixed; option spreads and borrowing charges remain. Thus the zero-fund-cost scenario is not an entirely cost-free portfolio.

## Output coherence

Both validation scripts pass: 17 core/accounting/calendar/output checks and 7 supplemental silver checks, including all recorded nesting comparisons. Full precision CSVs remain local; public JSON contains derived metrics/returns/exposures and source coverage metadata, not raw market quotes or credentials. Overlapping outcomes are preserved, while summary counts distinguish the available disjoint windows. Source prices are revised vendor history, universe membership is selected survival, drawdowns are monthly, and supplemental hypotheses were added after core outcomes were known. Core block bootstrap intervals are retained; supplemental intervals were not computed.

The optional WPM duration experiment has its own frozen design, separate data/result files and explicit post-core provenance. It cannot be retrospectively called a predeclared core winner.

The independent calendar review identified and corrected relative-index quarter phases. Corrected families share the stock entry and calendar quarter schedule in both training and execution; final tests establish identical target returns on the common calendar. All superseded phase-confounded data/engines/ledger/narrative remain preserved. The separate WPM raw diagnostic retains 11 families × raw/deployed variants; all raw variants performed worse than shrinkage in this replay.
