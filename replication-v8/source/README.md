# Reproducing this edition

Restore this source as model_v8 beside the preserved model_v5/run.py adapter,
model_v4/public/daily-data.json.gz universe and private source snapshots. Requires
Python, NumPy, pandas and SciPy. The private vendor archives and email credentials
are intentionally omitted; preserved input hashes identify the source vintage.
Current newly downloaded quotes may revise corporate adjustments and differ.

The numeric engine has a pure Python cash recursion. For optional native speed,
compile cash.c with clang -O3 -dynamiclib -o cash.dylib cash.c on macOS, or
cc -O3 -shared -fPIC -o cash.so cash.c on Linux. Do not enable fast-math.
The binary is omitted. The native and Python kernels were independently checked.

Run batch.py, risk_control.py, teacher.py, validate.py, summarize.py and report.py
in that order. The teacher additionally requires the preserved private derived
model_v7/results/original7-pca.json.gz input. It is explanatory, not a paid account.
Source snapshots and the earlier pre-cost WPM trial are not publicly licensed
quote archives. WPM-precost-comparison.csv retains their derived account results.

DESIGN.md records the initial pre-cost protocol; BASIS-ADDENDUM.md and
COST-ADDENDUM.md record subsequent definitions. Final training uses the paid cash
ledger, not the pre-cost function retained in run.py. There are26 fitted rules
plus2 volatility controls per company. All historical trials are exploratory.
