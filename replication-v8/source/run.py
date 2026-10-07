"""Price-only conditional exposure and paid option-basis research.

No observed option execution history; all option marks are hypothetical.
Training ratios/long horizons are exact pre-cost holding-segment returns.
Paid replay includes financing, borrow and trading costs separately.
"""
from pathlib import Path
import sys,json,gzip,hashlib,argparse,time,importlib.util
import numpy as np,pandas as pd
from scipy.special import ndtr
from scipy.optimize import minimize
R=Path(__file__).resolve().parent
adapter=importlib.util.spec_from_file_location('gold_v8_data',R/'data.py');c=importlib.util.module_from_spec(adapter);adapter.loader.exec_module(c)
paid_adapter=importlib.util.spec_from_file_location('gold_v8_paid',R/'cost_training.py');paid=importlib.util.module_from_spec(paid_adapter);paid_adapter.loader.exec_module(paid)
ASSETS=['GLD','SLV','TLT','SPY']
OPTIONS=[(metal,kind,tenor,strike) for metal in [0,1] for kind in ['call','put'] for tenor in [3,12,24] for strike in [.8,1.,1.2]]
OPTIONS += [(metal,kind,tenor,strikes) for metal in [0,1] for kind,strikes in [('callspread',(.8,1.)),('callspread',(1.,1.2)),('putspread',(1.,.8)),('putspread',(1.2,1.))] for tenor in [3,12,24]]
LEGCOUNT=np.array([2 if 'spread' in o[1] else 1 for o in OPTIONS])
N=4+len(OPTIONS)
SPECS=[dict(id=id,conditional=cond,balanced=bal,options=opts,funds=funds) for id,cond,bal,opts,funds in [
 ('gold_daily',False,False,False,1),
 ('metals_daily',False,False,False,2),('rates_daily',False,False,False,3),
 ('conditional_rates_daily',True,False,False,3),('rates_balanced',False,True,False,3),
 ('conditional_rates_balanced',True,True,False,3),('options_daily',False,False,True,3),
 ('conditional_options_daily',True,False,True,3),('options_balanced',False,True,True,3),
 ('conditional_options_balanced',True,True,True,3),('equity_conditional_options_balanced',True,True,True,4)]]
SPECS += [dict(id=id,conditional=True,balanced=True,options=opts,funds=3,daily_weight=.8) for id,opts in [('conditional_rates_daily_priority',False),('conditional_options_daily_priority',True)]]

def bs(s,k,t,v,rate,kind='call'):
 t=np.maximum(t,0);root=np.maximum(v,.01)*np.sqrt(np.maximum(t,1e-12));d1=(np.log(s/k)+(rate+.5*v*v)*t)/root;d2=d1-root
 call=s*ndtr(d1)-k*np.exp(-rate*t)*ndtr(d2)
 value=call if kind=='call' else call-s+k*np.exp(-rate*t)
 return np.where(t<=0,np.maximum(s-k,0) if kind=='call' else np.maximum(k-s,0),value)

def load(stock):
 d=pd.DataFrame({k:c.ohlc(k).close for k in ASSETS+[stock,'BIL']}).dropna();d.index=d.index.as_unit('ns')
 rv=d[ASSETS[:2]].pct_change().rolling(63,min_periods=40).std()*np.sqrt(252)
 gv=c.v5.series('^GVZ').reindex(d.index,method='ffill')/100
 gold=gv.fillna(rv.GLD*1.25).fillna(.2);silver=(rv.SLV*1.25).fillna(.3)
 d['gold_vol']=gold.clip(lower=.05);d['silver_vol']=silver.clip(lower=.05)
 rate=np.log(d.BIL/d.BIL.shift(21))/pd.Series(d.index,index=d.index).diff(21).dt.days*365.25
 d['rate']=rate.fillna(0)
 gr=d.GLD.pct_change();yr=d[stock].pct_change();beta=yr.rolling(126,min_periods=63).cov(gr)/gr.rolling(126,min_periods=63).var()
 state=pd.DataFrame({'trend':np.log(d.GLD/d.GLD.shift(126)),'vol':rv.GLD,'cash_yield':d.rate,'stock_gold_beta':beta},index=d.index).fillna(0)
 return d,state

def legs(kind,strike):
 return [(kind,strike,1)] if 'spread' not in kind else [(kind.replace('spread',''),strike[0],1),(kind.replace('spread',''),strike[1],-1)]

def price_option(s,initial,kind,strike,t,v,rate,fee_basis=False):
 return sum((abs(sign) if fee_basis else sign)*bs(s,initial*k,t,v,rate,side) for side,k,sign in legs(kind,strike))

def calendar(d,first,h):
 mi=d.groupby(d.index.to_period('M')).tail(1).index;ends=d.index.get_indexer(mi)
 return np.unique(np.r_[0,first,[i for i in ends if h==1 or d.index[i].month%3==0]]).astype(int),ends

def settlement_terms(d,entry):
 dates=d.index;prices=d[ASSETS].to_numpy();settled=[];payoffs=[]
 for metal,kind,tenor,strike in OPTIONS:
  expiry=dates[entry]+pd.DateOffset(months=tenor)
  j=int(dates.searchsorted(expiry,side='right')-1) if expiry<=dates[-1] else len(d)
  settled.append(j)
  payoffs.append(0. if j==len(d) else float(price_option(prices[j,metal],prices[entry,metal],kind,strike,0.,.2,0.)))
 return np.array(settled),np.array(payoffs)

def option_marks(d,entry,rows,carried=False,fee_basis=False):
 p=d[ASSETS].to_numpy();vol=d[['gold_vol','silver_vol']].to_numpy();dates=d.index;marks=[]
 for metal,kind,tenor,strike in OPTIONS:
  expiry=dates[entry]+pd.DateOffset(months=tenor);tt=np.asarray((expiry-dates[rows]).days)/365.25
  marks.append(price_option(p[rows,metal],p[entry,metal],kind,strike,tt,vol[rows,metal],float(d.rate.iloc[max(entry-1,0)]),fee_basis))
 result=np.column_stack(marks);settled,payout=settlement_terms(d,entry);bil=d.BIL.to_numpy()
 for k,j in enumerate(settled):
  after=rows>=j
  if after.any():result[after,k]=payout[k]*bil[rows[after]]/bil[j] if carried else 0.
 return result

def bank(d,state,first,h):
 anchors,mi=calendar(d,first,h);p=d[ASSETS].to_numpy();cash=d.BIL.to_numpy();A=np.zeros((len(d),N));AP=A.copy();base=np.ones(len(d));bp=base.copy();entry=np.zeros(len(d),int)
 for z,a in enumerate(anchors):
  end=anchors[z+1] if z+1<len(anchors) else len(d)-1
  if end<=a:continue
  rows=np.arange(a,end+1);g=cash[rows]/cash[a];mark=option_marks(d,a,rows,carried=True);premium=mark[0]/p[a,[o[0] for o in OPTIONS]]
  X=np.column_stack([p[rows]/p[a]-g[:,None],mark/p[a,[o[0] for o in OPTIONS]]-g[:,None]*premium])
  A[rows[1:]]=X[1:];AP[rows[1:]]=X[:-1];base[rows[1:]]=g[1:];bp[rows[1:]]=g[:-1];entry[rows[1:]]=max(a-1,0)
 return {'d':d,'state':state.to_numpy(),'A':A,'AP':AP,'base':base,'bp':bp,'entry':entry,'monthends':mi,'h':h,'first':first}

def premium_vector(d,i,prior=True):
 vol=d[['gold_vol','silver_vol']].to_numpy()[max(i-1,0) if prior else i];rate=float(d.rate.iloc[max(i-1,0)])
 # Approximate calendar tenor for the decision constraint; execution exact marks.
 return np.array([float(price_option(1.,1.,kind,strike,tenor/12,vol[metal],rate)) for metal,kind,tenor,strike in OPTIONS])

def precost_training(p,stock,i,spec):
 d=p['d'];ix=np.arange(max(1,i-1008),i);A=p['A'][ix];AP=p['AP'][ix];base=p['base'][ix];bp=p['bp'][ix]
 actual=d[stock].pct_change().to_numpy()[ix];sw=2.**(-(i-1-ix)/252)
 ess_before=float(sw.sum()**2/(sw@sw))
 if spec['conditional']:
  states=p['state'][p['entry'][ix]];sd=np.std(states,axis=0);sd=np.maximum(sd,1e-8);current=p['state'][i-1]
  similarity=np.maximum(.25,np.exp(-.5*np.mean(((states-current)/sd)**2,axis=1)));sw*=similarity
 good=np.array([(d.index[j]-d.index[j-1]).days<=4 for j in ix]);daily_sw=sw*good;daily_sw/=daily_sw.sum()
 endpoints=p['monthends'];endpoints=endpoints[(endpoints>=ix[0])&(endpoints<=ix[-1])]-ix[0]
 # Cumulative log products index initial zero, then each daily return.
 horizons=[]
 for months in ([3,12] if spec['balanced'] else []):
  a=endpoints[:-months]+1;b=endpoints[months:]+1
  assert len(a)>10
  target=np.expm1(np.r_[0,np.cumsum(np.log1p(actual))][b]-np.r_[0,np.cumsum(np.log1p(actual))][a])
  cum=np.r_[0,np.cumsum(sw)];weights=(cum[b]-cum[a])/(b-a);weights/=weights.sum()
  variance=max(float(weights@((target-weights@target)**2)),1e-8)
  horizons.append((a,b,target,weights,variance))
 variance=max(float(daily_sw@((actual-daily_sw@actual)**2)),1e-8)
 penalty=np.r_[0,np.ones(3),LEGCOUNT**2*2]*.01
 def evaluate(w,raw=False):
  v=base+np.einsum('ij,j->i',A,w);vp=bp+np.einsum('ij,j->i',AP,w)
  if min(v.min(),vp.min())<=.05:
   bad=np.minimum(v-.05,0);badp=np.minimum(vp-.05,0)
   return 1e4+1e4*float(bad@bad+badp@badp),2e4*(np.einsum('i,ij->j',bad,A)+np.einsum('i,ij->j',badp,AP))
  rr=v/vp-1;J=A/vp[:,None]-(v/vp**2)[:,None]*AP;error=rr-actual
  dw=.5 if spec['balanced'] else 1.;loss=dw*float(daily_sw@(error**2))/variance;grad=dw*2*np.einsum('i,ij->j',daily_sw*error,J)/variance
  if horizons:
   log=np.r_[0,np.cumsum(np.log1p(rr))];derivative=np.vstack([np.zeros(N),np.cumsum(J/(1+rr)[:,None],axis=0)])
   for a,b,target,weights,var in horizons:
    pred=np.expm1(log[b]-log[a]);PJ=(1+pred)[:,None]*(derivative[b]-derivative[a]);err=pred-target
    loss+=.25*float(weights@(err**2))/var;grad+=.5*np.einsum('i,ij->j',weights*err,PJ)/var
  if not raw:loss+=float(penalty@(w*w));grad+=2*penalty*w
  return loss,grad
 return evaluate,{'cutoff':str(d.index[i-1].date()),'observations':len(ix),'effective_daily_n':float(1/(daily_sw@daily_sw)),'unconditional_recency_effective_n':ess_before,'horizon_observations':[len(a) for a,b,t,w,v in horizons]}

def training(p,stock,i,spec):
 return paid.training(sys.modules[__name__],p,stock,i,spec)

def estimate(p,stock,i,spec,previous=None,parent=None):
 fun,info=training(p,stock,i,spec);d=p['d'];opt=spec['options'];nf=spec['funds']
 lo=np.zeros(N);hi=np.zeros(N);hi[:2]=[3,1.5]
 if nf==1:hi[1]=0.
 if nf>=3:lo[2]=-.75;hi[2]=.75
 if nf==4:hi[3]=1
 if opt:hi[4:]=2
 premium=np.r_[np.zeros(4),premium_vector(d,i)]
 gross=np.r_[np.ones(4),LEGCOUNT];gross[2]=1;gross2=gross.copy();gross2[2]=-1
 M=np.vstack([gross,gross2,premium]);upper=np.array([5.,5.,.3])
 constraints={'type':'ineq','fun':lambda w:upper-np.einsum('ij,j->i',M,w),'jac':lambda w:-M}
 valid=lambda w:bool(np.isfinite(w).all() and np.all(w>=lo-1e-7) and np.all(w<=hi+1e-7) and np.all(M@w<=upper+1e-7))
 gold=np.zeros(N);daily=p['d'][[stock,'GLD','BIL']].pct_change().iloc[max(1,i-1008):i];x=(daily.GLD-daily.BIL).to_numpy();y=(daily[stock]-daily.BIL).to_numpy();gold[0]=np.clip(x@y/max(x@x,1e-12),0,3)
 candidates=[gold]
 for old in [previous,parent]:
  if old is not None and valid(old):candidates.append(old)
 start=min(candidates,key=lambda w:fun(w)[0]);result=minimize(fun,start,jac=True,bounds=list(zip(lo,hi)),constraints=constraints,method='SLSQP',options={'ftol':1e-8,'maxiter':120})
 if valid(result.x):candidates.append(result.x)
 w=min(candidates,key=lambda w:fun(w)[0]);goldloss=fun(gold)[0];loss=fun(w)[0]
 assert loss<=goldloss+1e-8
 info.update({'optimizer_success':bool(result.success),'optimizer_message':str(result.message),'iterations':int(result.nit),'feasible_result':valid(result.x),'fallback':not np.array_equal(w,result.x),'objective':float(loss),'raw_objective':float(fun(w,True)[0]),'gold_objective':float(goldloss),'gold_embedding_ok':True,'parent_embedding_ok':parent is None or not valid(parent) or loss<=fun(parent)[0]+1e-8})
 return w.copy(),info

def replay(p,weights,cost=.0002,spread=.05,financing_spread=.005,short_fee_rate=.01,liquidate=True):
 d=p['d'];prices=d[ASSETS].to_numpy();bil=d.BIL.to_numpy();first=p['first'];q=np.zeros(4);oq=np.zeros(len(OPTIONS));cash=1.;nav=1.;values=[1.];ledger=[];settlements=[];active=None;markmatrix=None;feematrix=None
 trade=sorted(weights);trade_end={a:(trade[z+1] if z+1<len(trade) else len(d)-1) for z,a in enumerate(trade)}
 for i in range(first,len(d)-1):
  oldmarks=np.zeros(len(OPTIONS)) if active is None else markmatrix[i-active]
  oldfee=np.zeros(len(OPTIONS)) if active is None else feematrix[i-active]
  if i in weights:
   opening=cash+q@prices[i]+oq@oldmarks;assert abs(opening-nav)<1e-8
   active=i;rows=np.arange(i,trade_end[i]+1);markmatrix=option_marks(d,i,rows);feematrix=option_marks(d,i,rows,fee_basis=True);settled,payout=settlement_terms(d,i);newmarks=markmatrix[0];w=weights[i].copy()
   pr=newmarks/prices[i,[o[0] for o in OPTIONS]];premium=float(w[4:]@pr);scale=min(1.,.3/max(premium,1e-16));w[4:]*=scale
   nq=opening*w[:4]/prices[i];noq=opening*w[4:]/prices[i,[o[0] for o in OPTIONS]]
   fee=cost*np.abs(nq-q)@prices[i]+spread*(oq@oldfee+noq@feematrix[0])
   cash=opening-nq@prices[i]-noq@newmarks-fee;q=nq;oq=noq
   ledger.append({'date':str(d.index[i].date()),'weights':w.tolist(),'estimated_weights':weights[i].tolist(),'option_premium_fraction':float(noq@newmarks/opening),'execution_premium_scale':scale,'fund_quantities':q.tolist(),'option_quantities':oq.tolist(),'opening_nav':float(opening),'cash_after_trade':float(cash),'fee':float(fee)})
  days=(d.index[i+1]-d.index[i]).days;cash*=bil[i+1]/bil[i]
  if cash<0:cash*=1+financing_spread*days/365.25
  short_fee=short_fee_rate*(np.maximum(-q,0)@prices[i])*days/365.25;cash-=short_fee
  mature=settled==i+1
  if mature.any():
   amount=float(oq[mature]@payout[mature]);cash+=amount
   if np.any(oq[mature]>0):settlements.append({'date':str(d.index[i+1].date()),'entry_date':str(d.index[active].date()),'option_indices':np.flatnonzero(mature).tolist(),'quantities':oq[mature].tolist(),'payoff_per_unit':payout[mature].tolist(),'cash_payout':amount,'sale_fee':0.})
   oq[mature]=0.
  nextmarks=markmatrix[i+1-active];nav=cash+q@prices[i+1]+oq@nextmarks
  if liquidate and i==len(d)-2:nav-=cost*np.abs(q)@prices[i+1]+spread*oq@feematrix[i+1-active]
  if nav<=0:raise ValueError(('nonpositive paid account',str(d.index[i+1]),nav))
  values.append(float(nav))
 return np.array(values),ledger,settlements

def metrics(dates,x,y):
 result=c.metrics(dates,x,y);mi=pd.Series(np.arange(len(dates)),index=dates).groupby(dates.to_period('M')).last().to_numpy()
 result['horizons']=[]
 for h in [1,3,12,36,60]:
  if len(mi)<=h+1:continue
  a,b=mi[:-h],mi[h:];xx=x[b]/x[a]-1;yy=y[b]/y[a]-1;z=c.stats(xx,yy)
  result['horizons'].append({'months':h,**z,'median_absolute_gap_pp':float(np.median(abs(xx-yy))*100),'median_signed_gap_pp':float(np.median(yy-xx)*100)})
 return result

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--stocks',nargs='*');parser.add_argument('--limit-fits',type=int);parser.add_argument('--no-manifest',action='store_true');args=parser.parse_args()
 provenance={n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in ['run.py','data.py','cost_training.py','cash_kernel.py','cash.c','DESIGN.md','BASIS-ADDENDUM.md','COST-ADDENDUM.md']}
 (R/'results').mkdir(exist_ok=True);companies=[z for z in c.v5.OLD['universe'] if not args.stocks or z['ticker'] in args.stocks]
 for comp in companies:
  stock=comp['ticker'];d,state=load(stock);first=max(1008,int(d.index.searchsorted(pd.Timestamp(comp['start']))));mi=d.groupby(d.index.to_period('M')).tail(1).index;first=int(d.index.get_indexer(mi[mi>=d.index[first]])[0]);first=min(first,len(d)-2)
  y=d[stock].to_numpy()[first:];y=y/y[0];y[1:]*=.9998;y[-1]*=.9998;sy=d[stock].to_numpy()[first:];sy=sy/sy[0];sy[1:]*=.999;sy[-1]*=.999
  runs=[];banks={h:bank(d,state,first,h) for h in [1,3]};fitcache={};t=time.monotonic()
  for spec in SPECS:
   for h in [1,3]:
    id=spec['id']+('_m' if h==1 else '_q');p=banks[h];trade=[first]+[j for j in c.trade_dates(d,first,h) if j!=first];previous=None;weights={};decisions=[]
    for number,i in enumerate(trade):
     if args.limit_fits and number>=args.limit_fits:break
     key=(i,h,spec['conditional'],spec['balanced']);parent=fitcache.get(key)
     w,info=estimate(p,stock,i,spec,previous,parent);weights[i]=w;previous=w;fitcache[key]=w
     decisions.append({'date':str(d.index[i].date()),'weights':w.tolist(),**info})
    if args.limit_fits:
     print(stock,id,'fit diagnostics',decisions[-1],flush=True);continue
    nav,ledger,settlements=replay(p,weights);stress,_,_=replay(p,weights,.001,.1)
    runs.append({'id':id,'spec':spec,'h':h,'nav':nav.tolist(),'metrics':metrics(d.index[first:],nav,y),'stress':metrics(d.index[first:],stress,sy),'decisions':decisions,'ledger':ledger,'settlements':settlements});print(stock,id,'seconds',round(time.monotonic()-t,1),'solver_failures',sum(not r['optimizer_success'] for r in decisions),flush=True)
  if not args.limit_fits:
   target=R/'results'/f'{stock}.json.gz';temporary=target.with_suffix('.tmp')
   assert provenance=={n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in provenance},'Source changed during run'
   with gzip.open(temporary,'wt') as f:json.dump({'company':comp,'dates':[str(t.date()) for t in d.index[first:]],'stock_nav':y.tolist(),'rates_asset':'TLT','runs':runs,'provenance':provenance},f,separators=(',',':'),allow_nan=False)
   temporary.replace(target)
 manifest={'specs':SPECS,'options':OPTIONS,'cutoff':'2026-09-30','stocks':[z['ticker'] for z in companies],'engine_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'design_sha256':hashlib.sha256((R/'DESIGN.md').read_bytes()).hexdigest(),'timestamp':pd.Timestamp.now(tz='UTC').isoformat()}
 if not args.no_manifest:(R/'results/manifest.json').write_text(json.dumps({**manifest,'provenance':provenance},indent=2)+'\n')
if __name__=='__main__':main()
