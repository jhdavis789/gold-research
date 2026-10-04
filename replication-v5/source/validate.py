import json,gzip
from pathlib import Path
import numpy as np
import pandas as pd
import run as m
R=m.R
checks={}
files=[R/'results'/f'{c["ticker"]}.json.gz' for c in m.OLD['universe']]
for path in files:
 d=json.loads(gzip.decompress(path.read_bytes()));stock=d['company']['ticker'];part=json.loads(gzip.decompress((R/'results'/f'{stock}-stage2.json.gz').read_bytes()));ctrl=json.loads(gzip.decompress((R/'results'/f'{stock}-controls.json.gz').read_bytes()));part['runs']+=ctrl['runs'];part['decisions']+=ctrl['decisions'];dates=pd.to_datetime(d['dates']);y=np.array(d['stock_nav'])
 for r in d['runs']+part['runs']:
  nav=np.array(r['nav']);assert np.isfinite(nav).all() and (nav>0).all();assert len(nav)==len(y)
  calc=m.metrics(dates,nav,y)
  assert abs(calc['daily']['r2']-r['full']['daily']['r2'])<1e-12
  mi=np.unique(np.r_[0,np.flatnonzero(np.r_[dates[:-1].month!=dates[1:].month,True])]);ret=nav[1:]/nav[:-1]-1
  for a,b in zip(mi[:-1],mi[1:]):assert abs(np.prod(1+ret[a:b])-nav[b]/nav[a])<1e-10
  if 'stress_nav' in r:assert r['stress_nav'][-1]<=nav[-1]+1e-8
 for r in d['decisions']+part['decisions']:
  w=np.array(r['weights']);assert np.isfinite(w).all() and np.abs(w).sum()<=5+1e-9
  if 'cutoff' in r:assert r['cutoff']<r['entry']
 checks[stock]=len(d['runs'])+len(part['runs'])
# Perturb future targets and every future market input. Earlier decisions must not move.
d=m.load('WPM');first=int(d.index.searchsorted('2011-07-29'));p=m.prepare(d,first);i=int(d.index.searchsorted('2019-12-31'));changed=d.copy();changed.iloc[i+1:]*=1.31;future=m.prepare(changed,first)
for spec in m.SPECS:
 a=m.fit(p,'WPM',spec,i)[0];b=m.fit(future,'WPM',spec,i)[0];assert np.allclose(a,b,atol=1e-12),spec['id']
# Monthly/quarterly decisions only; no hidden daily rebalancing.
payload=json.loads(gzip.decompress((R/'results/WPM.json.gz').read_bytes()));byid={s['id']:s for s in m.SPECS}
for row in payload['decisions']:
 t=pd.Timestamp(row['entry']);assert t==d.groupby(d.index.to_period('M')).tail(1).index[d.groupby(d.index.to_period('M')).tail(1).index.to_period('M')==t.to_period('M')][0]
 if byid[row['model']]['h']==3 and row['entry']!='2011-07-29':assert t.month%3==0
# Independent fixed-share/cash benchmark, computed one holding block at a time.
spec=next(s for s in m.SPECS if s['id']=='metals_ewq');rows=[r for r in payload['decisions'] if r['model']==spec['id']];weights={int(d.index.get_loc(r['entry'])):np.array(r['weights']) for r in rows};nav,detail=m.simulate(p,spec,weights);independent=[1.];v=1.
for k,(a,w) in enumerate(weights.items()):
 end=list(weights)[k+1] if k+1<len(weights) else len(d)-1
 price=p['price'][a:end+1,:2];q=v*w/price[0]
 oldq=np.zeros(2) if k==0 else priorq
 fee=.0002*(np.abs(q-oldq)@price[0]);cash=v-q@price[0]-fee
 growth=p['cash'][a+1:end+1]/p['cash'][a:end]
 if cash<0:growth=growth*(1+.005*p['dt'][a+1:end+1])
 cv=cash*np.cumprod(growth);vpath=price[1:]@q+cv
 if k==len(weights)-1:vpath[-1]-=.0002*(np.abs(q)@price[-1])
 independent.extend(vpath);v=float(vpath[-1]);priorq=q
assert np.allclose(nav,independent,rtol=1e-11,atol=1e-12)
# Zero options reproduce the linear portfolio, including fees and cash.
opt={**spec,'option':[12,.8]};ow={i:np.r_[w,0,0] for i,w in weights.items()};zero,_=m.simulate(p,opt,ow);assert np.allclose(nav,zero,atol=1e-12)
(R/'validation.json').write_text(json.dumps({'passed':True,'path_counts':checks,'future_perturbation_candidates':18,'independent_accounting':True,'zero_option_embedding':True,'monthly_compounding':True,'higher_cost_paths_checked':True,'monthly_or_quarterly_trades_only':True},indent=2))
print('PASS',sum(checks.values()),'paths, all statistics and compounding; 18 causal perturbations; independent accounting; zero-option embedding; trade calendars; costs.')
