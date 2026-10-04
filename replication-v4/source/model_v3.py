"""Frozen v3 financed, nested exposure models. No raw quotes in public output."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
import numpy as np
import pandas as pd
from scipy.optimize import minimize,minimize_scalar
from scipy.special import ndtr
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
STOCKS=['NEM','AEM','B','AU','FNV','WPM','RGLD','GFI','KGC','HMY','EGO','IAG','BTG','OR']
NAMES=['Newmont','Agnico Eagle','Barrick','AngloGold Ashanti','Franco-Nevada','Wheaton Precious Metals','Royal Gold','Gold Fields','Kinross Gold','Harmony Gold','Eldorado Gold','IAMGOLD','B2Gold','OR Royalties']
COLORS=['#1565c0','#00796b','#c62828','#ef6c00','#6a1b9a','#00838f','#ad7c16','#3949ab','#558b2f','#d81b60','#5e35b1','#00897b','#f4511e','#546e7a']
SPECS={}
for label,n,opt in [('gold',1,False),('gold_silver',2,False),('gold_options',1,True),('gold_silver_options',2,True)]:
 for h in [1,3]:SPECS[f'{label}_{"monthly" if h==1 else "quarterly"}']={'h':h,'n':n,'options':opt,'lookback':24,'penalty':0 if label=='gold' else .0002}
SPECS['gold_quarterly_60m']={'h':3,'n':1,'options':False,'lookback':60,'penalty':0}
for h in [1,3]:SPECS[f'risk_matched_{"monthly" if h==1 else "quarterly"}']={'h':h,'n':1,'options':False,'lookback':36,'penalty':0,'risk':True}
COST=.0002;BORROW=.005;OPTION_SPREAD=.05

def load(stock,spec):
 keys=[stock,'GLD','BIL']+(['SLV'] if spec['n']==2 else [])+(['^GVZ'] if spec['options'] else [])
 series={}
 for key in keys:
  folder='snapshot_20261003' if key in STOCKS[:7]+['GLD','BIL'] else ('expanded_20261003' if key in ['SLV','^GVZ'] else 'v3_history_20261003')
  a=pd.read_csv(ROOT.parent/'data'/folder/f'{key}.csv',parse_dates=['date']).set_index('date')
  series[key]=a.adj_close
 d=pd.DataFrame(series)
 if '^GVZ' in d:d['^GVZ']=d['^GVZ'].ffill()
 d=d.dropna()
 # Only the last common observed daily session supplies each month's mark.
 m=d.resample('ME').last();counts=d.resample('ME').size();m=m.loc[counts>0]
 assert m.notna().all().all() and m.index.is_monotonic_increasing
 return m

def bs(s,k,t,v,r,put=False):
 if t<=1e-12:return max(k-s,0) if put else max(s-k,0)
 z=max(v,.01)*np.sqrt(t);d1=(np.log(s/k)+(r+.5*v*v)*t)/z;d2=d1-z
 return k*np.exp(-r*t)*ndtr(-d2)-s*ndtr(-d1) if put else s*ndtr(d1)-k*np.exp(-r*t)*ndtr(d2)

def prepared(m,spec):
 a=m[['GLD']+(['SLV'] if spec['n']==2 else [])].to_numpy();cp=m.BIL.to_numpy()
 dates=m.index;dt=np.diff(dates.asi8)/86400e9/365.25
 rate=np.r_[0,np.log(cp[1:]/cp[:-1])*12]
 vol=m['^GVZ'].to_numpy()/100 if spec['options'] else np.zeros(len(m))
 out={'prices':a,'cp':cp,'vol':vol,'rate':rate,'dt':dt,'dates':dates}
 if spec['options']:
  marks=np.zeros((len(m),spec['h']+1,2))
  for entry in range(len(m)-1):
   expirydate=next_expiry(dates[entry],spec)
   expiry=int(dates.searchsorted(expirydate))
   for j in range(entry,min(expiry,len(m)-1)+1):
    t=(expirydate-dates[j]).days/365.25
    marks[entry,j-entry]=[bs(a[j,0],a[entry,0],t,vol[j],rate[max(entry-1,0)],put) for put in [False,True]]
  out['optionmarks']=marks
 return out

def simulate(p,spec,weights,start,end,cost=COST,liquidate=True,collect=False):
 """Weights keyed by entry row; scalar cash/share/option accounting, unchanged quantities."""
 n=spec['n'];h=spec['h'];opt=spec['options'];a=p['prices'];cp=p['cp'];dates=p['dates']
 cash=1.;q=np.zeros(n);oq=np.zeros(2);expiry=None;optionentry=None;strike=0.;nav=1.;navs=[1.];rets=[];turn=0.;fees=0.;trades=[];wcur=None
 def marks(i):
  if not opt or expiry is None:return np.zeros(2)
  return p['optionmarks'][optionentry,i-optionentry]
 for i in range(start,end):
  mark=marks(i)
  if expiry is not None and i>=expiry:
   cash+=oq@mark;oq=np.zeros(2);expiry=None;mark=np.zeros(2)
  opening=cash+q@a[i]+oq@mark
  if i==start or i in weights:
   wcur=weights.get(i,weights[start]);oldq=q.copy();exitfee=OPTION_SPREAD*np.abs(oq)@mark
   cash+=oq@mark;oq=np.zeros(2)
   q=opening*wcur[:n]/a[i];dollars=np.abs(q-oldq)@a[i];fee=cost*dollars+exitfee
   cash=opening-q@a[i]-fee;turn+=dollars/opening;fees+=fee/opening
   if opt:
    expiry=int(dates.searchsorted(next_expiry(dates[i],spec)));optionentry=i;strike=a[i,0];oq=opening*wcur[n:]/strike;mark=marks(i)
    premium=oq@mark;cash-=premium*(1+OPTION_SPREAD);fees+=OPTION_SPREAD*premium/opening
   trades.append(i)
  cash*=cp[i+1]/cp[i]
  if cash<0:cash*=1+BORROW*p['dt'][i]
  nextmarks=marks(i+1);value=cash+q@a[i+1]+oq@nextmarks
  if i==end-1 and liquidate:
   fee=cost*np.abs(q)@a[i+1]
   if opt and expiry is not None and i+1<expiry:fee+=OPTION_SPREAD*np.abs(oq)@nextmarks
   value-=fee;fees+=fee/max(value,1e-12)
  if value<=0:return None
  rets.append(value/nav-1);nav=value;navs.append(nav)
 return np.array(rets),np.array(navs),turn,trades,fees

def next_expiry(date,spec):
 return date+pd.offsets.MonthEnd(1 if spec['h']==1 else (3-date.month%3))

def rebalance_indices(p,spec,start,end):
 return [start]+[i for i in range(start+1,end) if spec['h']==1 or p['dates'][i].month%3==0]

def constant_weights(start,end,spec,w,p):
 return {i:np.array(w) for i in rebalance_indices(p,spec,start,end)}

_COMMON={}
def common_entry(stock):
 if stock not in _COMMON:
  opt=load(stock,SPECS['gold_silver_options_monthly']);risk=load(stock,SPECS['risk_matched_monthly'])
  _COMMON[stock]=max(opt.index[25],risk.index[37])
 return _COMMON[stock]

def fit(p,spec,target,entry,base=None):
 L=spec['lookback'];end=entry-1;start=end-L
 assert start>=0 and end<entry
 y=(target[start+1:end+1]/target[start:end]-1).copy()
 y[0]=(1+y[0])*(1-COST)-1;y[-1]=(1+y[-1])*(1-COST)-1
 def residual(w):
  result=simulate(p,spec,constant_weights(start,end,spec,w,p),start,end)
  return np.full(len(y),1e3) if result is None else result[0]-y
 def mse(w):return float(np.mean(residual(w)**2))
 if base is None:
  result=minimize_scalar(lambda x:mse([x]),bounds=(0,3),method='bounded',options={'xatol':1e-6})
  w=np.array([result.x]);return w,{'baseline_mse':mse(w),'unpenalized_mse':mse(w),'deployed_mse':mse(w),'baseline_weight':w[0],'optimizer_success':bool(result.success)}
 pcount=spec['n']+2*spec['options'];initial=np.r_[base,np.zeros(pcount-1)]
 bounds=[(0,3)]+[(0,1)]*(pcount-1)
 baseline=mse(initial)
 raw=minimize(mse,initial,bounds=bounds,method='L-BFGS-B',options={'ftol':1e-11,'maxiter':80})
 best=raw.x if np.isfinite(raw.fun) and raw.fun<=baseline else initial.copy()
 def objective(w):return mse(w)+spec['penalty']*float(np.dot(w[1:],w[1:]))
 stable=minimize(objective,initial,bounds=bounds,method='L-BFGS-B',options={'ftol':1e-11,'maxiter':80})
 deployed=stable.x if np.isfinite(stable.fun) and stable.fun<=baseline else initial.copy()
 assert mse(best)<=baseline+1e-12
 return deployed,{'baseline_mse':baseline,'unpenalized_mse':mse(best),'deployed_mse':mse(deployed),'deployed_penalized_objective':objective(deployed),'baseline_weight':base,'optimizer_success':bool(raw.success),'stable_optimizer_success':bool(stable.success),'unpenalized_weights':best.tolist()}

def schedule(m,spec,stock):
 p=prepared(m,spec);target=m[stock].to_numpy();start=max(spec['lookback']+1,int(m.index.searchsorted(common_entry(stock))));weights={};diagnostics=[]
 goldspec={**spec,'n':1,'options':False,'penalty':0}
 goldp=prepared(m,goldspec)
 for i in rebalance_indices(p,spec,start,len(m)-1):
  if spec.get('risk'):
   e=i-1;b=e-spec['lookback'];s=target[b+1:e+1]/target[b:e]-1;g=m.GLD.to_numpy();r=g[b+1:e+1]/g[b:e]-1
   w=np.array([min(3,np.std(s,ddof=1)/np.std(r,ddof=1))]);diag={}
  else:
   bw,bdiag=fit(goldp,goldspec,target,i)
   if spec['n']==1 and not spec['options']:w,diag=bw,bdiag
   else:w,diag=fit(p,spec,target,i,bw[0])
  weights[i]=w;diagnostics.append({'month':str(m.index[i].to_period('M')),'cutoff':str(m.index[i-1].to_period('M')),**diag})
 return p,start,weights,diagnostics

def metrics(r,s):
 nav=np.r_[1,np.cumprod(1+r)];sn=np.r_[1,np.cumprod(1+s)];years=len(r)/12
 return {'tracking_r2':float(1-np.sum((r-s)**2)/np.sum((s-s.mean())**2)),'tracking_error':float(np.std(r-s,ddof=1)*np.sqrt(12)),'replica_cagr':float(nav[-1]**(1/years)-1),'stock_cagr':float(sn[-1]**(1/years)-1),'replica_vol':float(np.std(r,ddof=1)*np.sqrt(12)),'stock_vol':float(np.std(s,ddof=1)*np.sqrt(12)),'max_drawdown':float(np.min(nav/np.maximum.accumulate(nav)-1))}

def stock_returns(m,stock,start,end,cost=COST):
 s=m[stock].to_numpy();r=s[start+1:end+1]/s[start:end]-1;r=r.copy()
 r[0]=(1+r[0])*(1-cost)-1;r[-1]=(1+r[-1])*(1-cost)-1
 return r

def export_csv(name,rows):pd.DataFrame(rows).to_csv(OUT/f'{name}.csv',index=False)

def main():
 summary=[];paths=[];nesting=[];hz=[];windows=[];costsens=[];common=[];uncertainty=[];universe=[]
 for stock,name,color in zip(STOCKS,NAMES,COLORS):
  allruns={}
  for model,spec in SPECS.items():
   m=load(stock,spec);p,start,weights,diag=schedule(m,spec,stock);end=len(m)-1
   if start>=end:continue
   result=simulate(p,spec,weights,start,end);assert result is not None
   r,nav,turn,trades,fees=result;s=stock_returns(m,stock,start,end);stocknav=np.r_[1,np.cumprod(1+s)]
   row={'stock':stock,'model':model,'months':len(r),'start':str(m.index[start+1].to_period('M')),'end':str(m.index[end].to_period('M')),'trading_dates':len(trades),'annual_turnover':turn/(len(r)/12),'fee_fraction_sum':fees,**metrics(r,s)};summary.append(row)
   for j,i in enumerate(range(start,end)):
    keys=[k for k in weights if k<=i];w=weights[max(keys)];wr={'gold_weight':float(w[0]),'silver_weight':float(w[1]) if spec['n']==2 else 0,'call_weight':float(w[spec['n']]) if spec['options'] else 0,'put_weight':float(w[spec['n']+1]) if spec['options'] else 0}
    paths.append({'stock':stock,'model':model,'month':str(m.index[i+1].to_period('M')),'replica_return':float(r[j]),'stock_return':float(s[j]),'replica_nav':float(nav[j+1]),'stock_nav':float(stocknav[j+1]),**wr})
   nesting.extend({'stock':stock,'model':model,**x} for x in diag)
   allruns[model]=(m,p,start,end,weights,r,s)
   # Windows preserve every outcome; reset cash/share/option quantities and pay costs.
   for h in [1,3,6,12,36,60,120]:
    outcome=[]
    for a in range(start,end-h+1):
     active=max(k for k in weights if k<=a);ww={k:v for k,v in weights.items() if a<=k<a+h};ww[a]=weights[active]
     rr=simulate(p,spec,ww,a,a+h);assert rr is not None
     sr=stock_returns(m,stock,a,a+h);rn=rr[1][-1];sn=float(np.prod(1+sr));rc=rn**(12/h)-1;sc=sn**(12/h)-1
     item={'stock':stock,'model':model,'horizon_months':h,'start':str(m.index[a].to_period('M')),'end':str(m.index[a+h].to_period('M')),'replica_cagr':float(rc),'stock_cagr':float(sc),'stock_minus_replica_cagr':float(sc-rc),'replica_total_return':float(rn-1),'stock_total_return':float(sn-1)}
     windows.append(item);outcome.append(item)
    if outcome:
     hz.append({'stock':stock,'model':model,'horizon_months':h,'windows':len(outcome),'nonoverlapping_windows':(end-start)//h,'median_stock_minus_replica_cagr':float(np.median([o['stock_minus_replica_cagr'] for o in outcome])),'stock_win_fraction':float(np.mean([o['stock_minus_replica_cagr']>0 for o in outcome])),'median_replica_cagr':float(np.median([o['replica_cagr'] for o in outcome])),'median_stock_cagr':float(np.median([o['stock_cagr'] for o in outcome]))})
   for c in [0,.0002,.001]:
    rr=simulate(p,spec,weights,start,end,cost=c);costsens.append({'stock':stock,'model':model,'cost_bps':c*10000,**metrics(rr[0],stock_returns(m,stock,start,end,c))})
  pairedstart=max(run[0].index[run[2]] for model,run in allruns.items() if model!='gold_quarterly_60m')
  for model,(m,p,start,end,weights,r,s) in allruns.items():
   a=max(start,int(m.index.searchsorted(pairedstart)));active=max(k for k in weights if k<=a);ww={k:v for k,v in weights.items() if k>=a};ww[a]=weights[active]
   rr=simulate(p,SPECS[model],ww,a,end);ss=stock_returns(m,stock,a,end)
   common.append({'stock':stock,'model':model,'start':str(m.index[a+1].to_period('M')),'end':str(m.index[end].to_period('M')),'months':end-a,**metrics(rr[0],ss)})
   rng=np.random.default_rng(20261003);z=np.log1p(ss)-np.log1p(rr[0]);samples=[]
   for _ in range(500):
    ii=(rng.integers(len(z),size=int(np.ceil(len(z)/12)))[:,None]+np.arange(12))%len(z);samples.append(float(np.mean(z[ii.ravel()[:len(z)]])*12))
   uncertainty.append({'stock':stock,'model':model,'annual_relative_log_growth':float(np.mean(z)*12),'block_months':12,'resamples':500,'lower95':float(np.quantile(samples,.025)),'upper95':float(np.quantile(samples,.975))})
  m,_,start,end,_,_,_=allruns['gold_monthly'];universe.append({'ticker':stock,'name':name,'type':'streamer/royalty' if stock in ['FNV','WPM','RGLD','OR'] else 'producer','color':color,'history_start':str(m.index[0].date()),'evaluation_start':str(m.index[start+1].date()),'months':end-start})
  print(stock,'complete',flush=True)
 for name,rows in [('summary',summary),('paths',paths),('horizons',hz),('window_details',windows),('nesting',nesting),('cost_sensitivity',costsens),('common_summary',common),('uncertainty',uncertainty)]:export_csv(name,rows)
 meta={'version':3,'created_at':datetime.now(timezone.utc).isoformat(),'cutoff':'2026-09-30','implementation':'funded GLD/BIL bullion proxy; not futures P&L','options_status':'hypothetical Black-Scholes/GVZ premiums and expiry; not observed option quotes','costs':{'fund_bps':2,'annual_borrow_spread_bps':50,'option_premium_spread_fraction':.05},'limitations':['revised vendor histories','selected surviving stocks','hypothetical option surface','no actual futures rolls or margin','monthly mark drawdown','overlapping windows are not independent','candidate families evaluated after historical period; not live forward evidence'],'design_sha256':hashlib.sha256((ROOT/'METHODS.md').read_bytes()).hexdigest(),'engine_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'candidate_count':len(SPECS),'stock_count':len(STOCKS),'monthly_schedule_cutoff':'one full month before entry','quarterly_calendar':'March/June/September/December; initial fresh entry to next quarter','shared_start':'common first eligible entry per stock across 24m replicas/options and36m risk;60m sensitivity later','calendar_correction':'prior relative-phase results preserved as phase_confounded_data.json'}
 models=[{'id':k,'label':k.replace('_',' '),'instruments':['GLD','BIL']+(['SLV'] if v['n']==2 else [])+(['illustrative ATM call','illustrative ATM put'] if v['options'] else []),'rebalance_months':v['h'],'lookback_months':v['lookback'],'options_kind':'hypothetical' if v['options'] else 'none','primary':k=='gold_quarterly',**v} for k,v in SPECS.items()]
 data={'meta':meta,'universe':universe,'models':models,'summary':summary,'common_summary':common,'paths':paths,'horizons':hz,'window_details':windows,'nesting':nesting,'cost_sensitivity':costsens,'uncertainty':uncertainty}
 (ROOT/'public'/'data.json').write_text(json.dumps(data,separators=(',',':'),allow_nan=False)+'\n');(OUT/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
 print(pd.DataFrame(common).pivot(index='stock',columns='model',values='tracking_r2').round(3).to_string())
if __name__=='__main__':main()
