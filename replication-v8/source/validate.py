"""Numerical and causal validation before release; no model selection."""
import run as r
import json,gzip,hashlib,argparse,time
import numpy as np,pandas as pd
def load_saved(stock):return json.loads(gzip.decompress((r.R/'results'/f'{stock}.json.gz').read_bytes()))
def load_saved_controls():
 saved=json.loads(gzip.decompress((r.R/'results/risk-controls.json.gz').read_bytes()));count=0
 for item in saved:
  stock=item['company']['ticker'];d,state=r.load(stock);dates=pd.DatetimeIndex(item['dates']);first=int(d.index.get_loc(dates[0]));y=np.array(item['stock_nav']);rr=d[[stock,'GLD','BIL']].pct_change()
  for run in item['runs']:
   weights={}
   for z in run['decisions']:
    i=int(d.index.get_loc(pd.Timestamp(z['date'])));sample=rr.iloc[i-252:i];ratio=(sample[stock]-sample.BIL).std(ddof=1)/(sample.GLD-sample.BIL).std(ddof=1)
    assert abs(z['weights'][0]-np.clip(ratio,0,3))<1e-10 and np.all(np.array(z['weights'])[1:]==0) and z['cutoff']<z['date'];weights[i]=np.array(z['weights'])
   p=r.bank(d,state,first,run['h']);nav,ledger,settlements=r.replay(p,weights);assert np.max(abs(nav-run['nav']))<1e-10 and ledger==run['ledger'] and r.metrics(dates,nav,y)==run['metrics'];count+=1
 return {'accounts':count,'status':'passed'}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--unit-only',action='store_true');parser.add_argument('--wait-batch',action='store_true');args=parser.parse_args()
 checks=[]
 def check(name,detail=True):checks.append({'check':name,'passed':True,'details':detail})
 # Closed-form option identities, intrinsic and bounded spread payoffs.
 s=np.array([.5,.8,1.,1.2,2.]);v=.3;t=.7;rate=.04
 assert np.allclose(r.bs(s,1,t,v,rate)-r.bs(s,1,t,v,rate,'put'),s-np.exp(-rate*t),atol=1e-12)
 for metal,kind,tenor,k in r.OPTIONS:
  value=r.price_option(s,1,kind,k,0,v,rate)
  assert np.all(value>=-1e-12)
  if 'spread' in kind:assert np.all(value<=abs(k[1]-k[0])+1e-12)
 check('Put-call parity, intrinsic value and bounded spread payoffs')
 d,state=r.load('WPM');first=max(1008,int(d.index.searchsorted('2011-07-29')));p=r.bank(d,state,first,3)
 # A quarter-end Fri Dec29 option expires Mar29 before the next quarter's Mar30.
 entry=int(d.index.searchsorted('2017-12-29'));rows=np.arange(entry,int(d.index.searchsorted('2018-04-05'))+1)
 settled,payout=r.settlement_terms(d,entry);marks=r.option_marks(d,entry,rows);carried=r.option_marks(d,entry,rows,carried=True)
 tested=0
 for k,j in enumerate(settled):
  if j>=rows[-1]:continue
  after=rows>=j;assert np.all(marks[after,k]==0)
  assert np.allclose(carried[after,k],payout[k]*d.BIL.to_numpy()[rows[after]]/d.BIL.iloc[j],atol=1e-12)
  shocked=d.copy();shocked.loc[shocked.index>d.index[j],r.ASSETS[:2]]*=1.8
  actual=r.option_marks(shocked,entry,rows,carried=True)
  assert np.allclose(actual[after,k],carried[after,k],atol=1e-12)
  tested+=1
 assert tested>0;check('Expired contracts fix payoff and become cash; later spot moves cannot resurrect them',tested)
 # Pre-cost holding-template NAV exactly matches a no-fee, no-spread replay.
 trade=r.c.trade_dates(d,first,3);w=np.zeros(r.N);w[:3]=[1.,.2,-.1];w[4:]=.0005
 nav,ledger,settlements=r.replay(p,{i:w for i in trade},0.,0.,0.,0.)
 ix=np.arange(first+1,len(d));v=p['base'][ix]+p['A'][ix]@w;vp=p['bp'][ix]+p['AP'][ix]@w
 predicted=np.r_[1,np.cumprod(v/vp)];assert np.max(abs(predicted-nav))<1e-10
 assert all(z['sale_fee']==0 for z in settlements);check('Exact pre-cost daily template compounds to paid-engine replay when all fees are zero',float(np.max(abs(predicted-nav))))
 # Analytic derivatives independently checked at an interior point, both losses.
 rng=np.random.default_rng(20261007);errors=[]
 for balanced in [False,True]:
  spec={'conditional':True,'balanced':balanced};fun,info=r.training(p,'WPM',first+500,spec)
  z=np.zeros(r.N);z[:4]=[.8,.2,.1,.1];z[4:]=.001;value,grad=fun(z)
  for _ in range(5):
   direction=rng.normal(size=r.N);direction/=np.linalg.norm(direction);eps=1e-6
   finite=(fun(z+eps*direction)[0]-fun(z-eps*direction)[0])/(2*eps);analytic=grad@direction
   error=abs(finite-analytic);errors.append(error);assert error<2e-6,(balanced,error,finite,analytic)
 check('Daily and compounded multi-horizon analytic gradients',max(errors))
 # Future values cannot alter past bank rows, state estimates or fitted weights.
 i=first+500;altered=d.copy();altered.iloc[i:,altered.columns.get_indexer(r.ASSETS+['WPM'])]*=1.5
 altered_state=state.copy() # Recompute the same rolling features from shocked prices.
 rv=altered[r.ASSETS[:2]].pct_change().rolling(63,min_periods=40).std()*np.sqrt(252)
 gr=altered.GLD.pct_change();yr=altered.WPM.pct_change()
 altered_state['trend']=np.log(altered.GLD/altered.GLD.shift(126));altered_state['vol']=rv.GLD
 altered_state['stock_gold_beta']=yr.rolling(126,min_periods=63).cov(gr)/gr.rolling(126,min_periods=63).var();altered_state=altered_state.fillna(0)
 pp=r.bank(altered,altered_state,first,3);assert np.allclose(pp['A'][:i],p['A'][:i]);assert np.allclose(pp['state'][:i],p['state'][:i])
 spec=next(s for s in r.SPECS if s['id']=='conditional_options_balanced');wa,ia=r.estimate(p,'WPM',i,spec);wb,ib=r.estimate(pp,'WPM',i,spec)
 assert np.max(abs(wa-wb))<1e-9;check('Execution-day and future shocks cannot change earlier estimates',float(np.max(abs(wa-wb))))
 if args.unit_only:
  print(json.dumps({'status':'unit_checks_passed','checks':checks},indent=2));return
 files=[r.R/'results'/f"{z['ticker']}.json.gz" for z in r.c.v5.OLD['universe']];assert args.wait_batch or all(p.exists() for p in files)
 accounts=0;decisions=0;solver_failures=0
 for file in files:
  if not file.exists():print('Waiting for atomic batch result',file.name,flush=True)
  while not file.exists():time.sleep(5)
  saved=json.loads(gzip.decompress(file.read_bytes()));dates=pd.DatetimeIndex(saved['dates']);stock=saved['company']['ticker'];d,state=r.load(stock);first=int(d.index.get_loc(dates[0]));y=np.array(saved['stock_nav'])
  assert len(saved['runs'])==26
  banks={h:r.bank(d,state,first,h) for h in [1,3]}
  for run in saved['runs']:
   accounts+=1;nav=np.array(run['nav']);assert np.isfinite(nav).all() and np.all(nav>0)
   original=r.metrics(dates,nav,y);assert original==run['metrics']
   weights={int(d.index.get_loc(pd.Timestamp(z['date']))):np.array(z['weights']) for z in run['decisions']}
   p=banks[run['h']];rr,ll,ss=r.replay(p,weights)
   assert np.max(abs(rr-nav))<1e-10 and ll==run['ledger'] and ss==run['settlements']
   expected=r.c.trade_dates(d,first,run['h']);assert list(weights)==expected
   for z in run['decisions']:
    decisions+=1;assert pd.Timestamp(z['cutoff'])<pd.Timestamp(z['date']);assert z['gold_embedding_ok'] and z['parent_embedding_ok']
    solver_failures+=not z['optimizer_success']
   for z in run['ledger']:
    w=np.array(z['weights']);assert 0<=w[0]<=3+1e-7 and 0<=w[1]<=1.5+1e-7 and abs(w[2])<=.75+1e-7
    assert np.sum(abs(w[:4]))+r.LEGCOUNT@w[4:]<=5+1e-7;assert z['option_premium_fraction']<=.3+1e-7
   assert run['stress']['portfolio_cagr']<=run['metrics']['portfolio_cagr']+1e-10
  print(stock,'retained accounts validated',flush=True)
 check('All retained accounts: horizon/statistic reproduction, cutoffs, calendars, nested criteria, limits, premiums and cost stress',{'accounts':accounts,'fits':decisions,'solver_failures':solver_failures})
 manifest=json.loads((r.R/'results/manifest.json').read_text())
 while len(manifest.get('runs',[]))!=20:
  assert args.wait_batch;time.sleep(2);manifest=json.loads((r.R/'results/manifest.json').read_text())
 assert all(z['exit_code']==0 for z in manifest['runs'])
 for name,digest in manifest['provenance'].items():assert hashlib.sha256((r.R/name).read_bytes()).hexdigest()==digest
 risk=load_saved_controls()
 check('Past-volatility controls: same-date arithmetic, causal weights and paid replay',risk)
 receipt={'status':'passed','checks':checks,'engine_sha256':hashlib.sha256((r.R/'run.py').read_bytes()).hexdigest(),'accounts':accounts,'fits':decisions,'solver_failures':solver_failures}
 (r.R/'validation.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
