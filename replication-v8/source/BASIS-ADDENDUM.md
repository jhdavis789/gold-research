# Bounded option spreads

Before inspecting any v8 tracking/wealth outcomes, add24 vertical debit spreads to the36 single-leg basis choices. The first single-leg WPM replay is retained under review/ as a prototype; only run/solver/settlement counts were inspected. Long-only standalone options cannot express negative local gamma, which is too restrictive for the user's convexity question.

For each metal and3/12/24-month tenor add bull call spreads80%–100% and100%–120%, and bear put spreads100%–80% and120%–100%. Each is a paid position with a long leg and a short leg at the same expiry; payoff is bounded and nonnegative. No naked short options are allowed. Both legs count toward gross notional and squared notional shrinkage. Costs charge5% (10% stress) of the sum of absolute leg marks at entry/early exit, not a cheap percentage of the net spread. Settlement pays the fixed net intrinsic value into cash and charges no sale fee. Report the60 candidate structures as instruments distinct from the64 fit coordinates (four funds plus60 options).

Premium budgets apply to the positive net purchase price. Actual premium can vary at execution; recorded scaling ensures30% cap. Training and final accounts use exactly the same instrument payoff definitions. This addition expands the feasible option toolkit before outcomes are examined; it is not evidence of superiority.
