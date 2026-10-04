import json,gzip,csv,hashlib
from pathlib import Path
import numpy as np,pandas as pd
import run as m
R=m.R;P=R/'public';P.mkdir(exist_ok=True)
models=[{'id':s['id'],'label':s['label'],'group':'Metals + other exposures' if s['funds']>2 else 'Metal-only'} for s in m.SPECS]
raw=json.loads((R/'results/stage2-specs.json').read_text());models += [{'id':s['id'],'label':s['label'],'group':'Raw convexity follow-up'} for s in raw]
models += [{'id':s['id'],'label':s['label'],'group':'Matched-bound controls'} for s in json.loads((R/'results/control-specs.json').read_text())]
models += [{'id':'adaptive_metals','label':'Past-only adaptive metals blend','group':'Metal-only'},{'id':'v4_gold_quarterly','label':'Previous monthly-fit gold','group':'Prior baseline'},{'id':'v4_gold_silver_quarterly','label':'Previous monthly-fit gold + silver','group':'Prior baseline'},{'id':'v4_gold_silver_options_quarterly','label':'Previous monthly-fit gold + silver + options','group':'Prior baseline'}]
results=[];rows=[];perstock={};aggregates=[]
for company in m.OLD['universe']:
 stock=company['ticker'];d=json.loads(gzip.decompress((R/'results'/f'{stock}.json.gz').read_bytes()));s=json.loads(gzip.decompress((R/'results'/f'{stock}-stage2.json.gz').read_bytes()));c=json.loads(gzip.decompress((R/'results'/f'{stock}-controls.json.gz').read_bytes()));s['runs']+=c['runs'];s['decisions']+=c['decisions'];runs=d['runs']+s['runs'];runmap={r['id']:r for r in runs};y=np.array(d['stock_nav']);dates=pd.to_datetime(d['dates']);old=runmap['v4_gold_silver_quarterly'];details={}
 for r in runs:
  nav=np.array(r['nav']);detail={k:v for k,v in r.items() if k not in ['nav','stress_nav']}
  if 'stress_nav' in r:detail['stress']={period:m.metrics(dates,r['stress_nav'],y,since) for period,since in [('full',None),('confirmation','2020-01-01'),('recent','2023-01-01')]}
  last=[x for x in d['decisions']+s['decisions'] if x['model']==r['id']]
  if last:detail['latest_decision']=last[-1]
  details[r['id']]=detail
  for period in ['full','confirmation','recent']:
   for frequency in ['daily','monthly']:
    met=r[period][frequency];rows.append({'stock':stock,'model':r['id'],'period':period,'frequency':frequency,**met,'improvement_vs_old_metals':met['r2']-old[period][frequency]['r2']})
 x=np.diff(runmap['market_q']['nav'])/runmap['market_q']['nav'][:-1];yr=np.diff(y)/y[:-1];err=yr-x;ix=np.argsort(abs(err))[-5:][::-1];events=[{'date':d['dates'][i+1],'stock_return':float(yr[i]),'model_return':float(x[i]),'residual':float(err[i])} for i in ix]
 topfrac=float(np.sum(np.sort(err*err)[-10:])/np.sum(err*err))
 results.append({'company':company,'runs':details,'diagnostics':s['diagnostics'],'largest_residuals':events,'top10_error_share':topfrac})
 # Preserve daily NAVs as derived data, loaded one company at a time.
 package={'company':company,'dates':d['dates'],'stock_nav':np.round(y,10).tolist(),'runs':{r['id']:{'nav':np.round(r['nav'],10).tolist(),**({'stress_nav':np.round(r['stress_nav'],10).tolist()} if 'stress_nav' in r else {})} for r in runs}}
 with gzip.open(P/f'{stock}.json.gz','wt') as f:json.dump(package,f,separators=(',',':'),allow_nan=False)
 perstock[stock]=(d,runmap)
for period in ['full','confirmation','recent']:
 for freq in ['daily','monthly']:
  for model in models:
   data=[r['runs'][model['id']][period][freq]['r2'] for r in results];base=[r['runs']['v4_gold_silver_quarterly'][period][freq]['r2'] for r in results]
   aggregates.append({'period':period,'frequency':freq,'model':model['id'],'mean_r2':float(np.mean(data)),'median_r2':float(np.median(data)),'wins':int(sum(a>b for a,b in zip(data,base))),'companies':len(data)})
# Block bootstrap of WPM's paired monthly contributions to DAILY squared error.
wpm,runmap=perstock['WPM'];dates=pd.to_datetime(wpm['dates']);y=np.diff(wpm['stock_nav'])/wpm['stock_nav'][:-1];valid=np.diff(dates.asi8)/86400e9<=4;bootstrap={};rng=np.random.default_rng(20261004)
base=np.diff(runmap['v4_gold_silver_quarterly']['nav'])/runmap['v4_gold_silver_quarterly']['nav'][:-1]
for id in ['metals_ewq','market_q']:
 x=np.diff(runmap[id]['nav'])/runmap[id]['nav'][:-1];v=pd.DataFrame({'base':(y-base)**2,'new':(y-x)**2},index=dates[1:]).loc[valid].groupby(dates[1:][valid].to_period('M')).sum();n=len(v);a=v.to_numpy();samples=[]
 for _ in range(3000):
  ix=(rng.integers(n,size=int(np.ceil(n/12)))[:,None]+np.arange(12))%n;z=a[ix.ravel()[:n]].sum(axis=0);samples.append(1-z[1]/z[0])
 bootstrap[id]={'sse_reduction':float(1-v.new.sum()/v.base.sum()),'range95':np.quantile(samples,[.025,.975]).tolist(),'block_months':12,'resamples':3000}
output={'models':models,'companies':results,'aggregates':aggregates,'wpm_block_bootstrap':bootstrap,'trial_count':26,'baseline_count':3,'diagnostic_count':2,'cutoff':'2026-09-30','confirmation_note':'2020 onward is retrospective confirmation, not an untouched holdout; all candidates were devised after earlier historical results.'}
(P/'summary.json').write_text(json.dumps(output,separators=(',',':'),allow_nan=False))
with (P/'all-results.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
print(json.dumps({'bootstrap':bootstrap,'daily_summary':[a for a in aggregates if a['frequency']=='daily' and a['period']=='full' and a['model'] in ['v4_gold_silver_quarterly','metals_ewq','market_q']],'wpm':{id:{p:runmap[id][p] for p in ['full','confirmation','recent']} for id in ['v4_gold_silver_quarterly','metals_ewq','market_q']}},indent=2))
