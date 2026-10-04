from pathlib import Path
import json,gzip,hashlib,sys
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parent;S=Path(sys.argv[1]);B=Path(sys.argv[2])
assert (S/'daily-data.json.gz').read_bytes()==(B/'daily-data.json.gz').read_bytes()
assert (S/'summary.json').read_bytes()==(B/'summary.json').read_bytes()
out=json.loads((S/'lifecycle-summary.json').read_text());ledger={r['ticker']:r for r in json.loads((R/'terminal-ledger-private.json').read_text())};L={r['ticker']:r for r in out['companies']}
with gzip.open(R/'private-lifecycle-paths.json.gz','rt') as f:paths=json.load(f)
rows=[]
for p in (R/'data/raw/api').glob('*/request.json'):
 req=json.loads(p.read_text())
 if any('P_TOTAL_RETURN(01/01/2007,09/30/2026,D)' in x for x in req['payload']['data']['formulas']): rows+=json.loads((p.parent/'response.json').read_text()).get('data',[])
cash=pd.read_csv(R.parent/'data/snapshot_20261003/BIL.csv',parse_dates=['date']).set_index('date').adj_close
base=json.loads(gzip.decompress((B/'daily-data.json.gz').read_bytes()));checks=0
for cohort in out['cohorts']:
 start=cohort['start'];end=cohort['end'];terminal=[]
 for name in cohort['members']:
  if name in L:
   c=L[name];assert c['start']<=start<c['exit'];a=pd.DataFrame([x for x in rows if x.get('requestId')==c['id'] and x.get('price') is not None]).set_index('date').sort_index();assert start in a.index
   last=ledger[name]['previous_date'];r=a.loc[(a.index>start)&(a.index<=last),'tr'].fillna(0).to_numpy()/100
   value=float(np.prod(1+r))*ledger[name]['payout']/float(a.loc[last,'price'])*.9998*cash.loc[end]/cash.loc[c['exit']]
   if name=='GBG' and cohort['scenario']=='failed_last_quote':
    last=a.index[a.index<=c['exit']][-1];r=a.loc[(a.index>start)&(a.index<=last),'tr'].fillna(0).to_numpy()/100;value=float(np.prod(1+r))*.9998*cash.loc[end]/cash.loc[c['exit']]
  else:
   r=next(r for r in base['runs'] if r['stock']==name and r['model']=='unlevered_gold');a=r['dates'].index(start);b=r['dates'].index(end);value=r['stock_nav'][b]/r['stock_nav'][a]
  terminal.append(value)
 assert abs(np.mean(terminal)-1-cohort['total'])<1e-9,(cohort['year'],cohort['scenario'])
 for q,v in cohort['percentiles'].items():assert abs(np.quantile(np.array(terminal)-1,int(q)/100)-v)<1e-9
 for key,g in cohort['groups'].items():
  n=int(np.ceil(len(terminal)*(.1 if '10' in key else .25)));assert g['n']==n
  values=sorted(terminal)[-n:] if key.startswith('top') else sorted(terminal)[:n]
  assert abs(np.mean(values)-1-g['total'])<1e-9
 checks+=1
# No raw private records/individual NAV arrays in public lifecycle release.
assert set(out)=={'companies','cohorts','assumptions','source'}
for c in out['companies']:assert not any(k in c for k in ['price','tr','nav','dates'])
report={'passed':True,'cohorts_independently_rebuilt':checks,'original_paths_byte_identical':True,'percentiles_tail_groups_verified':True,'raw_vendor_panel_excluded':True,'lifecycle_data_sha256':hashlib.sha256((S/'lifecycle-summary.json').read_bytes()).hexdigest()}
(R/'lifecycle-audit.json').write_text(json.dumps(report,indent=2));print(report)
