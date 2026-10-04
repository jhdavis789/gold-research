import run as m,json,gzip
import numpy as np
from pathlib import Path
specs=[{**next(s for s in m.SPECS if s['id']=='metals_ewq'),'id':'metals_ewq_cap1','label':'Daily recency metals · original silver cap','silver_cap':1.},{**next(s for s in m.SPECS if s['id']=='metals_504q'),'id':'metals_stale_cap1','label':'Daily 504d metals · original cap and month gap','silver_cap':1.,'lag':'month'}]
for company in m.OLD['universe']:
 stock=company['ticker'];d=m.load(stock);first=int(d.index.searchsorted(company['start']));p=m.prepare(d,first);base=json.loads(gzip.decompress((m.R/'results'/f'{stock}.json.gz').read_bytes()));y=np.array(base['stock_nav']);dates=d.index[first:];out=m.R/'results'/f'{stock}-controls.json.gz';runs=[];decisions=[]
 for spec in specs:
  weights={}
  for i in [first]+[int(i) for i in p['quarter'] if first<i<len(d)-1]:
   w,info=m.fit(p,stock,spec,i);weights[i]=w;decisions.append({'model':spec['id'],'entry':str(d.index[i].date()),'weights':w.tolist(),**info})
  nav,detail=m.simulate(p,spec,weights);stress,_=m.simulate(p,spec,weights,cost=.001,spread=.1)
  runs.append({'id':spec['id'],'nav':nav.tolist(),'stress_nav':stress.tolist(),'full':m.metrics(dates,nav,y),'confirmation':m.metrics(dates,nav,y,'2020-01-01'),'recent':m.metrics(dates,nav,y,'2023-01-01'),**detail})
 with gzip.open(out,'wt') as f:json.dump({'runs':runs,'decisions':decisions},f,separators=(',',':'),allow_nan=False)
 print(stock,[(r['id'],r['full']['daily']['r2']) for r in runs],flush=True)
(m.R/'results/control-specs.json').write_text(json.dumps(specs,indent=2))
