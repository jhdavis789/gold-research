#!/usr/bin/env python3
"""Public chart JSON snapshot. Existing registered Yahoo family, gold study extension.

Raw responses remain private/local under data/. This is revised vendor history,
not a historical point-in-time data archive. No corporate-fundamental backfill.
"""
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data' / 'snapshot_20261003'
SYMBOLS = ['GLD', 'BIL', 'NEM', 'AEM', 'B', 'AU', 'FNV', 'WPM', 'RGLD']

def main():
    DATA.mkdir(parents=True, exist_ok=True)
    receipt = {'recorded_at': datetime.now(timezone.utc).isoformat(),
               'source': 'Yahoo public chart JSON', 'symbols': {},
               'cutoff': '2026-09-30', 'revised_history': True}
    for symbol in SYMBOLS:
        url = ('https://query1.finance.yahoo.com/v8/finance/chart/' + quote(symbol)
               + '?period1=315532800&period2=1790899200&interval=1d&events=div%2Csplits')
        with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30) as r:
            raw = r.read()
        result = json.loads(raw)['chart']['result'][0]
        name = result['meta'].get('longName') or result['meta'].get('shortName')
        if symbol == 'B':
            assert 'Barrick' in name, ('wrong entity', name)
        adj = result['indicators']['adjclose'][0]['adjclose']
        px = result['indicators']['quote'][0]['close']
        stamps = result['timestamp']
        rows = []
        for ts, a, p in zip(stamps, adj, px):
            date = datetime.fromtimestamp(ts, timezone.utc).strftime('%Y-%m-%d')
            if a is not None and p is not None and date <= '2026-09-30':
                assert a > 0 and p > 0
                rows.append((date, a, p))
        assert len(rows) > 120, (symbol, 'insufficient history')
        assert rows[-1][0] == '2026-09-30', (symbol, 'stale or delisted tail', rows[-1][0])
        (DATA / f'{symbol}.json').write_bytes(raw)
        with (DATA / f'{symbol}.csv').open('w') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'adj_close', 'close'])
            writer.writerows(rows)
        receipt['symbols'][symbol] = {'name': name, 'url': url, 'rows': len(rows),
            'start': rows[0][0], 'end': rows[-1][0], 'sha256': hashlib.sha256(raw).hexdigest(),
            'dividend_events': len(result.get('events', {}).get('dividends', {}))}
        print(symbol, name, len(rows), rows[0][0], rows[-1][0])
    (DATA / 'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')

if __name__ == '__main__':
    main()
