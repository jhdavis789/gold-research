"""Exact paid, constant-weight, slow-trading templates and analytic derivatives.

Weights are refitted for live evaluation; this training template holds the
candidate allocation constant across the historical training roll schedule.
No terminal liquidation at an artificial training cutoff.
"""
import numpy as np,pandas as pd
from pathlib import Path
import importlib.util
spec=importlib.util.spec_from_file_location('gold_v8_cash',Path(__file__).with_name('cash_kernel.py'));kernel=importlib.util.module_from_spec(spec);spec.loader.exec_module(kernel)

def blocks(engine,p):
 if 'paid_blocks' in p:return p['paid_blocks']
 d=p['d'];anchors,mi=engine.calendar(d,p['first'],p['h']);prices=d[engine.ASSETS].to_numpy();all=[];previous=None
 for z,a in enumerate(anchors):
  end=anchors[z+1] if z+1<len(anchors) else len(d)-1
  if end<=a:continue
  rows=np.arange(a,end+1);marks=engine.option_marks(d,a,rows);fees=engine.option_marks(d,a,rows,fee_basis=True)
  metal=[o[0] for o in engine.OPTIONS];op=marks/prices[a,metal];fe=fees/prices[a,metal];fr=prices[rows]/prices[a]
  settled,payout=engine.settlement_terms(d,a);cf=np.zeros_like(op)
  for k,j in enumerate(settled):
   if a<j<=end:cf[j-a,k]=payout[k]/prices[a,metal[k]]
  item={'a':a,'end':end,'fund_ratio':fr,'option_ratio':op,'fee_ratio':fe,'cf':cf,'premium':op[0],'old_fund_ratio':np.zeros(4) if previous is None else previous['fund_ratio'][-1],'old_fee_ratio':np.zeros(len(engine.OPTIONS)) if previous is None else previous['fee_ratio'][-1]}
  all.append(item);previous=item
 p['paid_blocks']=all;return all

def paid_returns(engine,p,w,begin,end,cost=.0002,spread=.05,borrow=.005,short=.01):
 d=p['d'];bil=d.BIL.to_numpy();N=len(w);NO=N-4;identity=np.eye(N);episodes=[b for b in blocks(engine,p) if begin<=b['a']<end]
 assert episodes
 output=[];jacobian=[];indices=[];previous_value=1.;previous_grad=np.zeros(N);old=np.zeros(N);oldD=np.zeros((N,N));first=True
 for b in episodes:
  a=b['a'];stop=min(b['end'],end);count=stop-a+1;premium=b['premium'];e=w.copy();D=identity.copy()
  amount=w[4:]@premium
  if amount>.3:
   scale=.3/amount;e[4:]*=scale;D[4:,4:]=scale*np.eye(NO)-(.3/amount**2)*np.outer(w[4:],premium)
  fund_old=np.zeros(4) if first else old[:4]*b['old_fund_ratio']/previous_value
  fund_delta=e[:4]-fund_old
  fundD=D[:4].copy()
  if not first:
   fundD-=oldD[:4]*b['old_fund_ratio'][:,None]/previous_value
   fundD+=np.outer(old[:4]*b['old_fund_ratio']/previous_value**2,previous_grad)
  sell=0. if first else old[4:]@b['old_fee_ratio']/previous_value
  sellD=np.zeros(N) if first else oldD[4:].T@b['old_fee_ratio']/previous_value-sell/previous_value*previous_grad
  buy=e[4:]@b['fee_ratio'][0];buyD=D[4:].T@b['fee_ratio'][0]
  entry_fee=cost*np.abs(fund_delta).sum()+spread*(sell+buy)
  entryD=cost*np.sign(fund_delta)@fundD+spread*(sellD+buyD)
  cash=1.-e[:4].sum()-e[4:]@premium-entry_fee
  cashD=-D[:4].sum(axis=0)-D[4:].T@premium-entryD
  underlying=np.column_stack([b['fund_ratio'][:count],b['option_ratio'][:count]])
  exposure=underlying@e
  direct=underlying if amount<=.3 else underlying@D
  cashflows=b['cf'][:count]@e[4:]
  flowD=np.column_stack([np.zeros((count,4)),b['cf'][:count]]) if amount<=.3 else b['cf'][:count]@D[4:]
  years=np.r_[0,np.diff(d.index[a:stop+1].asi8)/86400e9/365.25];growth=np.r_[1,bil[a+1:stop+1]/bil[a:stop]]
  sf=short*np.r_[0,b['fund_ratio'][:count-1,2]]*years
  cashvalues,cashgrads=kernel.path(cash,cashD,growth,years,sf,min(e[2],0),D[2] if e[2]<0 else np.zeros(N),cashflows,flowD,borrow)
  values=cashvalues+exposure;grads=cashgrads+direct;values[0]=1.;grads[0]=0.
  if min(values.min(),previous_value)<=.05:
   return None,None,None
  rr=values[1:]/values[:-1]-1;J=grads[1:]/values[:-1,None]-(values[1:]/values[:-1]**2)[:,None]*grads[:-1]
  output.append(rr);jacobian.append(J);indices.append(np.arange(a+1,stop+1));previous_value=values[-1];previous_grad=grads[-1].copy();old=e;oldD=D;first=False
 return np.concatenate(output),np.vstack(jacobian),np.concatenate(indices)

def training(engine,p,stock,i,spec):
 d=p['d'];eligible=[b for b in blocks(engine,p) if max(0,i-1008)<=b['a']<i-1]
 assert eligible;begin=eligible[0]['a'];ix=np.arange(begin+1,i)
 actual=d[stock].pct_change().to_numpy()[ix];sw=2.**(-(i-1-ix)/252)
 if spec['conditional']:
  states=p['state'][p['entry'][ix]];sd=np.maximum(np.std(states,axis=0),1e-8);current=p['state'][i-1]
  sw*=np.maximum(.25,np.exp(-.5*np.mean(((states-current)/sd)**2,axis=1)))
 good=np.array([(d.index[j]-d.index[j-1]).days<=4 for j in ix]);daily_sw=sw*good;daily_sw/=daily_sw.sum()
 endpoints=p['monthends'];endpoints=endpoints[(endpoints>=ix[0])&(endpoints<=ix[-1])]-ix[0]
 horizons=[];targetlog=np.r_[0,np.cumsum(np.log1p(actual))]
 for months in ([3,12] if spec['balanced'] else []):
  a=endpoints[:-months]+1;b=endpoints[months:]+1;assert len(a)>10
  target=np.expm1(targetlog[b]-targetlog[a]);cum=np.r_[0,np.cumsum(sw)];weights=(cum[b]-cum[a])/(b-a);weights/=weights.sum()
  variance=max(float(weights@((target-weights@target)**2)),1e-8);horizons.append((a,b,target,weights,variance))
 variance=max(float(daily_sw@((actual-daily_sw@actual)**2)),1e-8);penalty=np.r_[0,np.ones(3),engine.LEGCOUNT**2*2]*.01
 def evaluate(w,raw=False):
  rr,J,jj=paid_returns(engine,p,w,begin,i-1)
  if rr is None:return 1e6+float(w@w),2*w
  assert np.array_equal(jj,ix)
  error=rr-actual;dw=spec.get('daily_weight',.5) if spec['balanced'] else 1.;hw=(1-dw)/2
  loss=dw*float(daily_sw@(error**2))/variance;grad=dw*2*np.einsum('i,ij->j',daily_sw*error,J)/variance
  if horizons:
   log=np.r_[0,np.cumsum(np.log1p(rr))];derivative=np.vstack([np.zeros(engine.N),np.cumsum(J/(1+rr)[:,None],axis=0)])
   for a,b,target,weights,var in horizons:
    pred=np.expm1(log[b]-log[a]);PJ=(1+pred)[:,None]*(derivative[b]-derivative[a]);err=pred-target
    loss+=hw*float(weights@(err**2))/var;grad+=2*hw*np.einsum('i,ij->j',weights*err,PJ)/var
  if not raw:loss+=float(penalty@(w*w));grad+=2*penalty*w
  return loss,grad
 return evaluate,{'cutoff':str(d.index[i-1].date()),'observations':len(ix),'effective_daily_n':float(1/(daily_sw@daily_sw)),'horizon_observations':[len(a) for a,b,t,w,v in horizons],'training_costs':'Paid constant-allocation rolling replay; no artificial cutoff liquidation','first_training_entry':str(d.index[begin].date())}
