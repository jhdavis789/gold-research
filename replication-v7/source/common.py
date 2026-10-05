"""Shared data, bounded covariance fits and paid slow-trading accounting."""
from pathlib import Path
import json,gzip,sys,itertools
import numpy as np
import pandas as pd
from scipy.optimize import minimize
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'model_v5'));import run as v5
STOCKS=[c['ticker'] for c in v5.OLD['universe']]
FUNDS=['GLD','SLV','SPY']
CACHE={}
def ohlc(key):
 if key not in CACHE:
  folders=['v5_costs_20261004','v4_history_20261004','snapshot_20261003','expanded_20261003','v3_history_20261003']
  path=next(R.parent/'data'/f/(key+'.json') for f in folders if (R.parent/'data'/f/(key+'.json')).exists())
  a=json.loads(path.read_text())['chart']['result'][0];q=a['indicators']['quote'][0]
  close=np.array(q['close'],dtype=float);op=np.array(q['open'],dtype=float);adj=np.array(a['indicators']['adjclose'][0]['adjclose'],dtype=float)
  # Pandas may retain seconds/microseconds. Engines using asi8 require a known
  # unit; normalize here instead of silently assuming every index is nanoseconds.
  index=pd.to_datetime(a['timestamp'],unit='s',utc=True).tz_localize(None).normalize().as_unit('ns')
  d=pd.DataFrame({'open':op*adj/close,'close':adj},index=index)
  d=d.loc[:'2026-09-30'];d=d.replace([np.inf,-np.inf],np.nan).dropna();d=d[(d>0).all(axis=1)]
  assert not d.index.duplicated().any()
  CACHE[key]=d
 return CACHE[key]
def panel(stock):
 keys=FUNDS+[stock,'BIL'];d=pd.concat({k:ohlc(k) for k in keys},axis=1).dropna()
 return d
def returns(d):
 close=d.xs('close',axis=1,level=1);op=d.xs('open',axis=1,level=1)
 cc=close.pct_change();day=close/op-1;night=op/close.shift(1)-1
 # Dividend-adjustment factors multiply both open and close, assigning adjustment
 # accrual to overnight. No claim of an actual historical cash-dividend ledger.
 assert np.nanmax(abs((1+day)*(1+night)-(1+cc)).to_numpy())<1e-12
 rf=cc.BIL.fillna(0)
 for x in [cc,night]:x.loc[:,x.columns!='BIL']=x.loc[:,x.columns!='BIL'].sub(rf,axis=0)
 day=day.drop(columns='BIL');night=night.drop(columns='BIL');cc=cc.drop(columns='BIL')
 return cc,day,night
def fit_cov(gram,cross,yy):
 n=len(cross);pen=.01*yy*np.r_[0,np.ones(n-1)];G=gram+np.diag(pen);bounds=[(0,3),(0,1.5),(0,1)][:n]
 base=np.zeros(n);base[0]=np.clip(cross[0]/max(G[0,0],1e-16),0,3)
 scale=max(yy,1e-12)
 objective=lambda w:float((np.einsum('i,ij,j->',w,G,w)-2*np.sum(w*cross))/scale)
 # With two or three coordinates, enumerate all faces of the box and solve each
 # free quadratic exactly. This avoids rare line-search terminations on tiny SSEs.
 w=base.copy();best=objective(w)
 for state in itertools.product([0,1,2],repeat=n):
  free=np.flatnonzero(np.array(state)==1);fixed=np.flatnonzero(np.array(state)!=1);candidate=np.zeros(n)
  for j in fixed:candidate[j]=bounds[j][0 if state[j]==0 else 1]
  if len(free):candidate[free]=np.linalg.solve(G[np.ix_(free,free)],cross[free]-G[np.ix_(free,fixed)]@candidate[fixed])
  if any(candidate[j]<bounds[j][0]-1e-10 or candidate[j]>bounds[j][1]+1e-10 for j in range(n)):continue
  candidate=np.clip(candidate,[a for a,b in bounds],[b for a,b in bounds]);value=objective(candidate)
  if value<best:w,best=candidate,value
 assert np.isfinite(w).all()
 return w,{'nesting_ok':objective(w)<=objective(base)+1e-12,'optimizer_success':True,'solver':'enumerated convex box faces','objective':objective(w),'gold_only_objective':objective(base)}
def gram_fit(sets,weights,nf):
 G=np.zeros((nf,nf));b=np.zeros(nf);yy=0.
 for factor,y,mix in sets:
  G+=mix*np.einsum('ni,n,nj->ij',factor[:,:nf],weights,factor[:,:nf]);b+=mix*np.einsum('ni,n,n->i',factor[:,:nf],weights,y);yy+=mix*float(np.sum(weights*y*y))
 return fit_cov(G,b,yy)
def trade_dates(d,first,h):
 mi=d.groupby(d.index.to_period('M')).tail(1).index
 return [first]+[int(i) for i in d.index.get_indexer(mi) if first<i<len(d)-1 and (h==1 or d.index[i].month%3==0)]
def account(d,stock,weights,nf,cost=.0002):
 close=d.xs('close',axis=1,level=1);first=min(weights);p=close[FUNDS[:nf]].to_numpy();cp=close.BIL.to_numpy();q=np.zeros(nf);cash=1.;nav=1.;values=[1.];ledger=[]
 for i in range(first,len(d)-1):
  if i in weights:
   opening=cash+q@p[i];assert abs(opening-nav)<1e-8
   nq=opening*weights[i]/p[i];fee=cost*np.abs(nq-q)@p[i];cash=opening-nq@p[i]-fee;q=nq
   ledger.append({'date':str(d.index[i].date()),'quantities':q.tolist(),'cash':float(cash),'fee':float(fee),'weights':weights[i].tolist()})
  cash*=cp[i+1]/cp[i]
  if cash<0:cash*=1+.005*(d.index[i+1]-d.index[i]).days/365.25
  nav=cash+q@p[i+1]
  if i==len(d)-2:nav-=cost*np.abs(q)@p[i+1]
  assert nav>0
  values.append(float(nav))
 y=close[stock].to_numpy()[first:];y=y/y[0];y[1:]*=1-cost;y[-1]*=1-cost
 return np.array(values),y,ledger
def metrics(dates,x,y):return v5.metrics(pd.DatetimeIndex(dates).as_unit('ns'),x,y)
def stats(x,y):
 return {'n':len(y),'tracking_r2':float(1-np.sum((y-x)**2)/np.sum((y-y.mean())**2)),'regression_r2':float(np.corrcoef(x,y)[0,1]**2),'rmse':float(np.sqrt(np.mean((y-x)**2)))}
def save(name,data):
 (R/'results').mkdir(exist_ok=True)
 with gzip.open(R/'results'/name,'wt') as f:json.dump(data,f,separators=(',',':'),allow_nan=False)
