import json,gzip
from pathlib import Path
import numpy as np
import pandas as pd
import run as m
R=m.R
RAW=[{**s,'id':s['id']+'_raw','label':s['label']+' · no shrink','raw':True} for s in m.SPECS if s['option']]
IDS=['metals_504q','metals_504m','metals_252q','metals_126q','metals_ewq','metals_ewm','metals_blend']
for company in m.OLD['universe']:
 stock=company['ticker'];path=R/'results'/f'{stock}.json.gz';old=json.loads(gzip.decompress(path.read_bytes()));out=R/'results'/f'{stock}-stage2.json.gz'
 if out.exists():continue
 d=m.load(stock);first=int(d.index.searchsorted(company['start']));p=m.prepare(d,first);dates=d.index[first:];y=np.array(old['stock_nav']);trade=[first]+[int(i) for i in p['quarter'] if first<i<len(d)-1]
 runs=[];decisions=[]
 for spec in RAW:
  weights={}
  for i in trade:
   w,info=m.fit(p,stock,spec,i);weights[i]=w;decisions.append({'model':spec['id'],'entry':str(d.index[i].date()),'weights':w.tolist(),**info})
  nav,detail=m.simulate(p,spec,weights);stress,_=m.simulate(p,spec,weights,cost=.001,spread=.1)
  runs.append({'id':spec['id'],'nav':nav.tolist(),'stress_nav':stress.tolist(),'full':m.metrics(dates,nav,y),'confirmation':m.metrics(dates,nav,y,'2020-01-01'),'recent':m.metrics(dates,nav,y,'2023-01-01'),**detail})
 # Rule chosen exclusively on previously realized net tracking errors.
 byid={r['id']:r for r in old['runs']};wr={(z['model'],z['entry']):z['weights'] for z in old['decisions']};weights={}
 for i in trade:
  k=i-first;start=max(0,k-504);scores=[]
  if k>=252:
   yr=y[start+1:k]/y[start:k-1]-1
   for id in IDS:
    nav=np.array(byid[id]['nav']);rr=nav[start+1:k]/nav[start:k-1]-1;scores.append((float(np.mean((yr-rr)**2)),id))
   chosen=[t[1] for t in sorted(scores)[:3]]
  else:chosen=['metals_504q']
  dt=str(d.index[i].date());w=np.mean([wr[id,dt] for id in chosen],axis=0);weights[i]=w
  decisions.append({'model':'adaptive_metals','entry':dt,'weights':w.tolist(),'selected':chosen,'score_cutoff':str(d.index[max(first,i-1)].date()),'past_scores':scores})
 spec={**next(s for s in m.SPECS if s['id']=='metals_504q'),'id':'adaptive_metals'}
 nav,detail=m.simulate(p,spec,weights);stress,_=m.simulate(p,spec,weights,cost=.001,spread=.1)
 runs.append({'id':'adaptive_metals','nav':nav.tolist(),'stress_nav':stress.tolist(),'full':m.metrics(dates,nav,y),'confirmation':m.metrics(dates,nav,y,'2020-01-01'),'recent':m.metrics(dates,nav,y,'2023-01-01'),**detail})
 # These predictions are NOT invested returns. Hold coefficients quarterly, fit on prior daily observations.
 diagnostics=[];returns=d[stock].pct_change().fillna(0).to_numpy();factors=p['rets'][:,:3]
 for quadratic in [False,True]:
  X=factors.copy()
  if quadratic:X=np.column_stack([X,factors[:,0]**2,factors[:,1]**2,factors[:,0]*factors[:,1]])
  prediction=np.full(len(d),np.nan)
  for k,i in enumerate(trade):
   end=i-1;ix=np.arange(max(1,end-755),end+1);ww=2.**(-(end-ix)/126);ww/=ww.sum();scale=X[ix].std(axis=0);scale=np.maximum(scale,1e-9)
   A=np.column_stack([np.ones(len(ix)),X[ix]/scale]);sw=np.sqrt(ww);beta=np.linalg.lstsq(A*sw[:,None],returns[ix]*sw,rcond=None)[0]
   until=trade[k+1] if k+1<len(trade) else len(d)-1;j=np.arange(i+1,until+1);prediction[j]=np.column_stack([np.ones(len(j)),X[j]/scale])@beta
  rows={}
  for name,since in [('full',dates[0]),('confirmation',pd.Timestamp('2020-01-01')),('recent',pd.Timestamp('2023-01-01'))]:
   mask=np.isfinite(prediction)&(d.index>=since)&(p['dt']*365.25<=4);a=prediction[mask];b=returns[mask];rows[name]={'r2':float(1-np.sum((a-b)**2)/np.sum((b-b.mean())**2)),'n':len(a)}
  diagnostics.append({'id':'quadratic_explanation' if quadratic else 'linear_explanation','metrics':rows})
 payload={'runs':runs,'decisions':decisions,'diagnostics':diagnostics}
 with gzip.open(out,'wt') as f:json.dump(payload,f,separators=(',',':'),allow_nan=False)
 print(stock,[(r['id'],round(r['full']['daily']['r2'],3)) for r in runs],diagnostics,flush=True)
(R/'results/stage2-specs.json').write_text(json.dumps(RAW,indent=2))
