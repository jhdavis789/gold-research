"""Daily marked replay; frozen monthly fits, monthly/quarterly trades. Private prices."""
import sys,json,gzip,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'model_v3'));import model as core
sys.path.insert(0,str(R.parent));import fetch_snapshot as fetch
NEW=['DRD','SSRM','CDE','EQX','SA','NG']
NAMES=['DRDGOLD','SSR Mining','Coeur Mining','Equinox Gold','Seabridge Gold','NOVAGOLD']
MODELS=['unlevered_gold','risk_matched_quarterly','risk_matched_monthly','gold_quarterly','gold_monthly','gold_silver_quarterly','gold_silver_options_quarterly']
LABELS=['Unlevered gold (GLD)','Volatility-targeted gold · quarterly','Volatility-targeted gold · monthly','Fitted gold · quarterly','Fitted gold · monthly','Gold + silver · quarterly','Gold + silver + illustrative gold options · quarterly']
fetch.DATA=R.parent/'data/v4_history_20261004';fetch.SYMBOLS=NEW
if not (fetch.DATA/'receipt.json').exists():fetch.main()
CACHE={}
def series(key):
 if key not in CACHE:
  folders=['v4_history_20261004','snapshot_20261003','expanded_20261003','v3_history_20261003']
  p=next(R.parent/'data'/f/(key+'.csv') for f in folders if (R.parent/'data'/f/(key+'.csv')).exists())
  CACHE[key]=pd.read_csv(p,parse_dates=['date']).set_index('date').adj_close
 return CACHE[key]
def daily(stock):
 d=pd.DataFrame({k:series(k) for k in [stock,'GLD','SLV','BIL','^GVZ']})
 d['^GVZ']=d['^GVZ'].ffill();return d.dropna().loc[:'2026-09-30']
def load(stock,spec):return daily(stock).resample('ME').last()
core.load=load
old=pd.read_csv(R.parent/'model_v3/results/paths.csv')
allstocks=core.STOCKS+NEW
colors=core.COLORS+['#8c564b','#a51c30','#b8860b','#2c7c89','#a0529c','#525252']
universe=[];runs=[];qa=[]
for stock,name,color in zip(allstocks,core.NAMES+NAMES,colors):
 d=daily(stock);m=load(stock,{})
 start=max(37,int(m.index.searchsorted(core.common_entry(stock))))
 if start>=len(m)-2:continue
 monthends=d.groupby(d.index.to_period('M')).tail(1).index
 pos={dt.to_period('M'):i for i,dt in enumerate(d.index)}
 first=pos[m.index[start].to_period('M')]
 dates=d.index[first:];s=d[stock].to_numpy();g=d.GLD.to_numpy();silver=d.SLV.to_numpy();cashpx=d.BIL.to_numpy();vol=d['^GVZ'].to_numpy()/100
 sn=s[first:]/s[first];sn[1:] *= 1-core.COST;sn[-1]*=1-core.COST
 universe.append({'ticker':stock,'name':name,'color':color,'group':'Developer' if stock in ['SA','NG'] else ('Streamer / royalty' if stock in ['FNV','WPM','RGLD','OR'] else 'Producer (may include other metals)'),'history_start':str(d.index[0].date()),'start':str(dates[0].date()),'end':str(dates[-1].date())})
 for mid in MODELS:
  spec=core.SPECS.get(mid,{'n':1,'h':3,'options':False,'lookback':24})
  inds=core.rebalance_indices({'dates':m.index},spec,start,len(m)-1)
  if mid=='unlevered_gold':weights={i:np.array([1.]) for i in inds}
  elif stock in NEW:
   p,st,weights,diag=core.schedule(m,spec,stock);assert st==start
  else:
   sub=old[(old.stock==stock)&(old.model==mid)].set_index('month')
   weights={}
   for i in inds:
    r=sub.loc[str(m.index[i+1].to_period('M'))]
    weights[i]=np.array([r.gold_weight]+([r.silver_weight] if spec['n']==2 else [])+([r.call_weight,r.put_weight] if spec['options'] else []))
  trades={pos[m.index[i].to_period('M')]:w for i,w in weights.items()}
  nav=1.;cash=1.;q=np.zeros(spec['n']);oq=np.zeros(2);expiry=None;strike=None;rate=0.;values=[1.];tradecount=0
  assets=np.column_stack([g,silver])[:,:spec['n']]
  def marks(j):
   if expiry is None:return np.zeros(2)
   return np.array([core.bs(g[j],strike,max(0,(d.index[expiry]-d.index[j]).days)/365.25,vol[j],rate,put) for put in [False,True]])
  for j in range(first,len(d)-1):
   mk=marks(j)
   if expiry is not None and j>=expiry:cash+=oq@mk;oq[:]=0;expiry=None;mk=np.zeros(2)
   if j in trades:
    w=trades[j];opening=cash+q@assets[j]+oq@mk;oldq=q.copy();cash+=oq@mk
    exitfee=core.OPTION_SPREAD*np.abs(oq)@mk;oq[:]=0
    q=opening*w[:spec['n']]/assets[j];fee=core.COST*np.abs(q-oldq)@assets[j]+exitfee;cash=opening-q@assets[j]-fee
    if spec['options']:
     month=m.index.searchsorted(d.index[j]+pd.offsets.MonthEnd(0));exp=core.next_expiry(m.index[month],spec).to_period('M');expiry=pos[exp];strike=g[j]
     rate=float(np.log(m.BIL.iloc[max(0,month-1)]/m.BIL.iloc[max(0,month-2)])*12)
     oq=opening*w[spec['n']:]/strike;cash-=(oq@marks(j))*(1+core.OPTION_SPREAD)
    tradecount+=1
   cash*=cashpx[j+1]/cashpx[j]
   if cash<0:cash*=1+core.BORROW*(d.index[j+1]-d.index[j]).days/365.25
   nav=cash+q@assets[j+1]+oq@marks(j+1)
   if j==len(d)-2:
    nav-=core.COST*np.abs(q)@assets[j+1]
    if expiry is not None and j+1<expiry:nav-=core.OPTION_SPREAD*np.abs(oq)@marks(j+1)
   assert nav>0,(stock,mid,j);values.append(float(nav))
  values=np.array(values);assert len(values)==len(sn)
  ix=[0]+[i for i,dt in enumerate(dates) if dt in monthends and i>0]
  def stats(x,y,daily_dates=None):
   xx=x[1:]/x[:-1]-1;yy=y[1:]/y[:-1]-1
   if daily_dates is not None:
    valid=np.diff(daily_dates.asi8)/86400e9<=4;xx=xx[valid];yy=yy[valid]
   return {'n':len(xx),'tracking_r2':float(1-np.sum((yy-xx)**2)/np.sum((yy-yy.mean())**2)),'regression_r2':float(np.corrcoef(xx,yy)[0,1]**2)}
  qa.append({'stock':stock,'model':mid,'daily':stats(values,sn,dates),'monthly':stats(values[ix],sn[ix]),'trades':tradecount})
  runs.append({'stock':stock,'model':mid,'dates':[str(x.date()) for x in dates],'portfolio':np.round(values,10).tolist(),'stock_nav':np.round(sn,10).tolist(),'monthends':ix})
 print(stock,'done',flush=True)
meta={'cutoff':'2026-09-30','companies':len(universe),'measurement':'Daily NAV; monthly observations compounded from identical daily NAV. Fits remain monthly; trades monthly or quarterly.','source':'Yahoo chart JSON revised adjusted closes; derived research only','cost_bps':2,'borrowing_spread_bps':50,'option_premium_spread':.05,'new_symbols':NEW}
payload={'meta':meta,'universe':universe,'models':[{'id':i,'label':l} for i,l in zip(MODELS,LABELS)],'runs':runs}
with gzip.open(R/'public/daily-data.json.gz','wt',compresslevel=9) as f:json.dump(payload,f,separators=(',',':'),allow_nan=False)
(R/'statistics.json').write_text(json.dumps(qa,indent=2))
(R/'public/summary.json').write_text(json.dumps(qa,separators=(',',':')))
print('WPM',json.dumps([r for r in qa if r['stock']=='WPM']),flush=True)
