# Sources and measurement

Daily total-return and raw open/close snapshots: registered Yahoo chart family, issuer-specific coverage through September30,2026. Hourly raw OHLCV: October7,2024–September30,2026; five-minute raw OHLCV: August10–September30,2026. Securities are synchronized to exact New York regular-session bar grids; incomplete or zero-volume grids are excluded, prices are never forward-filled. Recent sampling can contain trade-price and timing noise. Private raw replies and quote levels are not redistributed.

Existing GLD/SLV/BIL/SPY/TLT/USO/FXA/FXC history supplies funded proxies. Cash and financing accrue by actual elapsed days. Adjusted total-return units imply dividend reinvestment. Portfolio results include modeled costs; explanatory PCA diagnostics contain no investable wealth claim. No miner index or peer stock is held in a replica.

[FactSet official tick-history schema](https://github.com/FactSet/enterprise-sdk/blob/main/code/python/FactSetIntradayTickHistory/v1/docs/TickHistoryApi.md): bounded existing-subscription request returned HTTP500; no FactSet intraday data entered the calculations. [Realized-beta research](https://www.nber.org/papers/w11134) motivates measuring covariance at finer frequencies; this implementation is a finite-sample experimental comparison, not a microstructure-noise-consistent estimator.

The source registry, local receipt hashes, complete trial definitions and accounting checks are preserved in the research project. Shared-stock PCA uses contemporaneous peer observations solely to diagnose omitted common risk; targets are excluded from their component inputs.
