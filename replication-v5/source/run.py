"""Frozen daily-calibrated, slow-trading company replication experiments."""
from pathlib import Path
import json,gzip,hashlib,time
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import ndtr
R=Path(__file__).resolve().parent
ASSETS=['GLD','SLV','SPY','TLT','USO','FXA','FXC'];CACHE={}
with gzip.open(R.parent/'model_v4/public/daily-data.json.gz','rt') as f:OLD=json.load(f)
SPECS=[]
def add(id,label,funds=2,window=504,h=3,half=None,lag='day',option=None,blend=False):SPECS.append(dict(id=id,label=label,funds=funds,window=window,h=h,half=half,lag=lag,option=option,blend=blend))
add('gold_stale','Daily gold · previous-month cutoff',1,lag='month')
add('gold_recent','Daily gold · recent cutoff',1)
add('metals_504q','Daily gold + silver · 504d',2)
add('metals_504m','Daily gold + silver · 504d / monthly',2,h=1)
add('metals_252q','Daily gold + silver · 252d',2,252)
add('metals_126q','Daily gold + silver · 126d',2,126)
add('metals_ewq','Daily gold + silver · recency weighted',2,756,half=126)
add('metals_ewm','Daily gold + silver · recency / monthly',2,756,h=1,half=126)
add('metals_blend','Daily gold + silver · short/long blend',2,504,blend=True)
add('calls_3atm','Metals + 3-month ATM calls',2,756,half=126,option=[3,1.])
add('calls_12itm','Metals + 12-month 80% strike calls',2,756,half=126,option=[12,.8])
add('calls_24itm','Metals + 24-month 80% strike calls',2,756,half=126,option=[24,.8])
add('calls_12atm','Metals + 12-month ATM calls',2,756,half=126,option=[12,1.])
add('market_q','Metals + broad equities · quarterly',3,756,half=126)
add('market_m','Metals + broad equities · monthly',3,756,h=1,half=126)
add('market_rates','Metals + equities + rates',4,756,half=126)
add('cost_fx','Metals + equities + rates + oil / FX',7,756,half=126)
add('market_calls','Metals + equities + rates + 12m calls',4,756,half=126,option=[12,.8])
def series(key):
 if key not in CACHE:
  folders=['v5_costs_20261004','v4_history_20261004','snapshot_20261003','expanded_20261003','v3_history_20261003']
  p=next(R.parent/'data'/f/(key+'.csv') for f in folders if (R.parent/'data'/f/(key+'.csv')).exists())
  CACHE[key]=pd.read_csv(p,parse_dates=['date']).set_index('date').adj_close
 return CACHE[key]
def load(stock):
 d=pd.DataFrame({k:series(k) for k in [stock]+ASSETS+['BIL','^GVZ']});d['^GVZ']=d['^GVZ'].ffill()
 return d.dropna().loc[:'2026-09-30']
def bs(s,k,t,v,rate):
 t=np.maximum(t,1e-10);z=np.maximum(v,.05)*np.sqrt(t);a=(np.log(s/k)+(rate+.5*v*v)*t)/z
 return s*ndtr(a)-k*np.exp(-rate*t)*ndtr(a-z)
def prepare(d,first):
 n=len(d);months=d.groupby(d.index.to_period('M')).tail(1).index;mi=d.index.get_indexer(months)
 quarter=[int(i) for i in mi if d.index[i].month%3==0];anchors=sorted(set([0,first]+quarter))
 price=d[ASSETS].to_numpy();cash=d.BIL.to_numpy();dt=np.r_[0,np.diff(d.index.asi8)/86400e9/365.25]
 rf=np.r_[0,cash[1:]/cash[:-1]-1];rets=np.vstack([np.zeros(7),price[1:]/price[:-1]-1]);rate=np.log(d.BIL/d.BIL.shift(21))/(pd.Series(d.index,index=d.index)-pd.Series(d.index,index=d.index).shift(21)).dt.days*365.25;rate=rate.fillna(0).to_numpy()
 v=np.column_stack([d['^GVZ'].to_numpy()/100,d.SLV.pct_change().rolling(63).std().fillna(.3/np.sqrt(252)).to_numpy()*np.sqrt(252)*1.25]);v=np.maximum(v,.05)
 p={'d':d,'price':price,'cash':cash,'rf':rf,'rets':rets,'dt':dt,'rate':rate,'vol':v,'mi':mi,'quarter':quarter,'options':{},'first':first}
 for tenor,strike in [[3,1.],[12,.8],[24,.8],[12,1.]]:
  feature=np.zeros((n,2));entrymarks={}
  for z,a in enumerate(anchors):
   end=anchors[z+1] if z+1<len(anchors) else n-1
   if a>=n-1:continue
   j=np.arange(a,end+1);expiry=d.index[a]+pd.DateOffset(months=tenor);t=np.asarray((expiry-d.index[j]).days)/365.25
   marks=np.column_stack([bs(price[j,k],price[a,k]*strike,t,v[j,k],rate[max(0,a-1)]) for k in [0,1]])
   feature[j[1:]]=(marks[1:]-marks[:-1])/price[j[:-1],:2]-rf[j[1:],None]*marks[:-1]/price[j[:-1],:2]
   entrymarks[a]=(j,marks)
  p['options'][(tenor,strike)]={'feature':feature,'marks':entrymarks}
 return p

def fit(p,stock,spec,i,window=None):
 end=i-1
 if spec['lag']=='month':end=max(int(j) for j in p['mi'] if j<i)
 window=window or spec['window'];begin=max(1,end-window+1);ix=np.arange(begin,end+1)
 # Extended market closures are not one-day samples; avoid treating a five-day gap as daily.
 ix=ix[p['dt'][ix]*365.25<=4]
 nf=spec['funds'];X=p['rets'][ix,:nf]-p['rf'][ix,None]
 if spec['option']:X=np.column_stack([X,p['options'][tuple(spec['option'])]['feature'][ix]])
 s=p['d'][stock].to_numpy();y=s[ix]/s[ix-1]-1-p['rf'][ix]
 sw=np.ones(len(ix)) if spec['half'] is None else 2.**(-(end-ix)/spec['half']);sw/=sw.sum()
 lam=(0. if spec.get('raw') else .01)*float(sw@(y*y));pen=np.r_[0,np.ones(nf-1),np.ones(2)*2 if spec['option'] else []]*lam
 lo=np.array([0,0,0,-.5,-.5,-.5,-.5][:nf]+([0,0] if spec['option'] else []));hi=np.array([3,spec.get('silver_cap',1.5),1,.5,.5,.5,.5][:nf]+([2,2] if spec['option'] else []))
 A=np.vstack([X*np.sqrt(sw[:,None]),np.diag(np.sqrt(pen))]);b=np.r_[y*np.sqrt(sw),np.zeros(len(lo))]
 # Solve the convex box-constrained quadratic without the platform's LAPACK/BLAS
 # residual path, which emitted invalid floating-point flags on finite tiny inputs.
 # Scaling by target variance changes conditioning, not the minimizer.
 gram=np.einsum('ni,n,nj->ij',X,sw,X)+np.diag(pen)
 cross=np.einsum('ni,n,n->i',X,sw,y)
 baseline=np.zeros(len(lo));baseline[0]=np.clip(cross[0]/gram[0,0],0,3)
 scale=max(float(np.sum(sw*y*y)),1e-12)
 def optfun(w):return (float(np.einsum('i,ij,j->',w,gram,w))-2*float(np.sum(cross*w)))/scale
 def jac(w):return 2*(np.einsum('ij,j->i',gram,w)-cross)/scale
 result=minimize(optfun,baseline,jac=jac,bounds=list(zip(lo,hi)),method='L-BFGS-B',options={'ftol':1e-13,'gtol':1e-9,'maxiter':2000})
 w=result.x
 if spec['option'] and w[-2:].sum()>2:w[-2:]*=2/w[-2:].sum()
 if np.abs(w).sum()>5:w*=5/np.abs(w).sum()
 objective=lambda ww:float(np.sum(sw*(np.einsum('ni,i->n',X,ww)-y)**2)+np.sum(pen*ww*ww))
 if objective(w)>objective(baseline):w=baseline
 if spec['blend'] and window!=126:w=.5*w+.5*fit(p,stock,{**spec,'blend':False},i,126)[0]
 return w,{'cutoff':str(p['d'].index[end].date()),'observations':len(ix),'objective':objective(w),'gold_only_objective':objective(baseline),'nesting_ok':objective(w)<=objective(baseline)+1e-12}

def simulate(p,spec,weights,cost=.0002,spread=.05):
 start=p['first'];n=len(p['d']);nf=spec['funds'];q=np.zeros(nf);oq=np.zeros(2);cash=1.;nav=1.;values=[1.];entry=None;fees=0.;turn=0.;maxgross=0.
 def marks(j):
  if not spec['option'] or entry is None:return np.zeros(2)
  tenor,strike=spec['option'];expiry=p['d'].index[entry]+pd.DateOffset(months=tenor);t=(expiry-p['d'].index[j]).days/365.25
  return np.array([float(bs(p['price'][j,k],p['price'][entry,k]*strike,t,p['vol'][j,k],p['rate'][max(0,entry-1)])) for k in [0,1]])
 for i in range(start,n-1):
  if i in weights:
   w=weights[i];oldmarks=marks(i);opening=cash+q@p['price'][i,:nf]+oq@oldmarks;assert abs(opening-nav)<1e-9
   newq=opening*w[:nf]/p['price'][i,:nf];dollars=np.abs(newq-q)@p['price'][i,:nf]
   fee=cost*dollars+spread*np.abs(oq)@oldmarks;q=newq;entry=i
   oq=opening*w[nf:]/p['price'][i,:2] if spec['option'] else np.zeros(2)
   premium=oq@marks(i);fee+=spread*premium
   cash=opening-q@p['price'][i,:nf]-premium-fee;fees+=fee/opening;turn+=dollars/opening;maxgross=max(maxgross,np.abs(w).sum())
  cash*=p['cash'][i+1]/p['cash'][i]
  if cash<0:cash*=1+.005*p['dt'][i+1]
  cash-=.01*(np.maximum(-q,0)@p['price'][i,:nf])*p['dt'][i+1]
  nav=cash+q@p['price'][i+1,:nf]+oq@marks(i+1)
  if i==n-2:
   fee=cost*np.abs(q)@p['price'][i+1,:nf]+spread*np.abs(oq)@marks(i+1);nav-=fee;fees+=fee/max(nav,1e-10)
  assert nav>0,(spec['id'],i,nav)
  values.append(float(nav))
 return np.array(values),{'fee_fraction_sum':float(fees),'annual_fund_turnover':float(turn/((n-start)/252)),'trades':len(weights),'max_gross':maxgross}

def metrics(dates,x,y,since=None):
 dates=pd.DatetimeIndex(dates);keep=np.ones(len(x),dtype=bool) if since is None else dates>=pd.Timestamp(since);x=np.asarray(x)[keep];y=np.asarray(y)[keep];dates=dates[keep]
 if len(x)<60:return None
 dr=np.diff(x)/x[:-1];sr=np.diff(y)/y[:-1];valid=np.diff(dates.asi8)/86400e9<=4;dr=dr[valid];sr=sr[valid]
 def stat(a,b):return {'n':len(a),'r2':float(1-np.sum((a-b)**2)/np.sum((b-b.mean())**2)),'regression_r2':float(np.corrcoef(a,b)[0,1]**2),'rmse':float(np.sqrt(np.mean((a-b)**2)))}
 ix=np.r_[0,np.flatnonzero(np.r_[dates[:-1].month!=dates[1:].month,True])];ix=np.unique(ix);mx=x[ix];my=y[ix]
 return {'daily':stat(dr,sr),'monthly':stat(np.diff(mx)/mx[:-1],np.diff(my)/my[:-1]),'start':str(dates[0].date()),'end':str(dates[-1].date()),'stock_cagr':float((y[-1]/y[0])**(365.25/(dates[-1]-dates[0]).days)-1),'portfolio_cagr':float((x[-1]/x[0])**(365.25/(dates[-1]-dates[0]).days)-1)}

def main():
 (R/'results').mkdir(exist_ok=True);manifest={'specs':SPECS,'candidate_count':19,'design_hash':hashlib.sha256((R/'DESIGN.md').read_bytes()).hexdigest(),'engine_hash':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'created_at':pd.Timestamp.now(tz='UTC').isoformat()};(R/'results/manifest.json').write_text(json.dumps(manifest,indent=2))
 for company in OLD['universe']:
  stock=company['ticker'];out=R/'results'/f'{stock}.json.gz'
  if out.exists():print(stock,'cached',flush=True);continue
  d=load(stock);first=int(d.index.searchsorted(company['start']));assert str(d.index[first].date())==company['start'];p=prepare(d,first);dates=d.index[first:];y=d[stock].to_numpy()[first:];y=y/y[0];y[1:]*=.9998;y[-1]*=.9998
  runs=[];ledgers=[]
  for spec in SPECS:
   trade=[first]+[int(i) for i in (p['mi'] if spec['h']==1 else p['quarter']) if first<i<len(d)-1]
   weights={}
   for i in trade:
    w,info=fit(p,stock,spec,i);weights[i]=w;ledgers.append({'model':spec['id'],'entry':str(d.index[i].date()),'weights':w.tolist(),**info})
   nav,detail=simulate(p,spec,weights);stress,_=simulate(p,spec,weights,cost=.001,spread=.1)
   runs.append({'id':spec['id'],'nav':nav.tolist(),'stress_nav':stress.tolist(),'full':metrics(dates,nav,y),'confirmation':metrics(dates,nav,y,'2020-01-01'),'recent':metrics(dates,nav,y,'2023-01-01'),**detail})
  for id in ['gold_quarterly','gold_silver_quarterly','gold_silver_options_quarterly']:
   old=next(r for r in OLD['runs'] if r['stock']==stock and r['model']==id);oldnav=pd.Series(old['portfolio'],index=pd.to_datetime(old['dates'])).reindex(dates).to_numpy();assert np.isfinite(oldnav).all()
   runs.append({'id':'v4_'+id,'nav':oldnav.tolist(),'full':metrics(dates,oldnav,y),'confirmation':metrics(dates,oldnav,y,'2020-01-01'),'recent':metrics(dates,oldnav,y,'2023-01-01')})
  payload={'company':company,'dates':[str(dt.date()) for dt in dates],'stock_nav':y.tolist(),'runs':runs,'decisions':ledgers}
  with gzip.open(out,'wt') as f:json.dump(payload,f,separators=(',',':'),allow_nan=False)
  print(stock,[(r['id'],round(r['full']['daily']['r2'],3)) for r in runs],flush=True)
if __name__=='__main__':main()
