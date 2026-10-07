# Source coverage and limitations

Preserved Yahoo chart JSON snapshots supply adjusted daily fund and stock prices through September 30, 2026. Public files contain derived research, not vendor quote archives. Back-adjusted histories are revised observations and this universe contains surviving companies. Per-company evaluation dates appear in every result row. Older source editions remain preserved.

Gold volatility uses [Cboe GVZ](https://www.cboe.com/us/indices/dashboard/gvz/), a thirty-day implied-volatility measure for gold through GLD options. It is not a historical option chain across the strikes and maturities used here. Silver and pre-GVZ gold volatility use explicit trailing-realized assumptions. Option marks and spreads are hypothetical. BIL, GLD, SLV, TLT and the separately allowed SPY provide funded returns, not contract-specific futures.

The October 7 historical GLD chain probe used the official [FactSet Options chain endpoint](https://github.com/FactSet/enterprise-sdk/blob/main/code/python/FactSetOptions/v1/docs/OptionChainsScreeningApi.md) for September 30, 2025. Existing access returned HTTP 403; no historical option executions or surface were obtained. Local access receipts and raw response remain private. No paid data was purchased.

The earlier [intraday edition](https://jhdavis789.github.io/gold-research/replication-v7/) retains recent hourly and five-minute evidence and the leave-target-out PCA source. This edition uses longer daily history for paid construction and a separate translation of that shared residual. The earlier [valuation/margin experiment](https://jhdavis789.github.io/gold-research/replication-v3/FUNDAMENTALS.md) uses filing-known annual observations and remains separate.

Actual futures replication requires contract settlements, expiry and roll rules, collateral, margin and transaction costs. Option replication also requires historical executable prices. Those requirements remain open. Modeled fit is evidence about this instrument representation and sample; it is not proof of an executable strategy or a causal model of the business.
