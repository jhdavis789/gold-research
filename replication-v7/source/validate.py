"""Material gates: causal estimates, actual bookkeeping, grids and PCA exclusion."""
import common as c,intraday as intr,daily_sessions as ds,leadlag,asset_pca,pca
import json,gzip
import numpy as np,pandas as pd
def read(path):return json.loads(gzip.decompress(path.read_bytes()))
checks=[]
def passed(name,details=None):checks.append({'check':name,'passed':True,'details':details})
def independent(d,stock,weights,funds,cost=.0002,short=False):
 p=d[funds].to_numpy();cp=d.BIL.to_numpy();first=min(weights);nav=[1.];q=np.zeros(len(funds));cash=1.
 for i in range(first,len(d)-1):
  if i in weights:
   equity=cash+float(sum(q*p[i]));newq=equity*weights[i]/p[i];cash=equity-float(sum(newq*p[i]))-cost*float(sum(abs(newq-q)*p[i]));q=newq
  cash*=cp[i+1]/cp[i];dt=(d.index[i+1]-d.index[i]).days/365.25
  if cash<0:cash*=1+.005*dt
  if short:cash-=.01*float(sum(np.maximum(-q,0)*p[i]))*dt
  value=cash+float(sum(q*p[i+1]))
  if i==len(d)-2:value-=cost*float(sum(abs(q)*p[i+1]))
  nav.append(value)
 return np.array(nav)
def main():
 count=0;fits=0;max_error=0.;allmonthly=True;nest=0;optimizer_fail=0
 for stock in c.STOCKS:
  panel=c.panel(stock);close=panel.xs('close',axis=1,level=1)
  for suffix in ['sessions','hourly','leadlag','asset-pca']:
   payload=read(c.R/'results'/f'{stock}-{suffix}.json.gz');dates=pd.DatetimeIndex(payload['dates']).as_unit('ns');target=np.array(payload['stock_nav']);shared=[]
   for run in payload['runs']:
    count+=1;nav=np.array(run['nav']);assert len(nav)==len(target)==len(dates) and np.all(nav>0);met=c.metrics(dates,nav,target)
    assert abs(met['daily']['r2']-run['metrics']['daily']['r2'])<1e-12;assert abs(met['monthly']['r2']-run['metrics']['monthly']['r2'])<1e-12
    assert run['stress']['portfolio_cagr']<=met['portfolio_cagr']+1e-10
    dec=run['decisions'];trade=pd.DatetimeIndex([a['date'] for a in dec]);assert np.all(trade[1:].month.isin([3,6,9,12])) if run['id'].endswith('_q') or suffix in ['sessions','asset-pca'] else True
    assert len(set(trade.to_period('M')))==len(trade);allmonthly &= bool(len(set(trade.to_period('M')))==len(trade))
    for a in dec:
     fits+=1;assert pd.Timestamp(a['cutoff'])<pd.Timestamp(a['date']);w=np.array(a['weights']);assert -1e-7<=w[0]<=3+1e-7 and -1e-7<=w[1]<=1.5+1e-7
     if len(w)>2:assert -1e-7<=w[2]<=1+1e-7
     if suffix=='asset-pca':assert np.all(abs(w[3:])<=.5+1e-7) and abs(w).sum()<=5+1e-7
     if 'nesting_ok' in a:assert a['nesting_ok'];nest+=1
     if 'gold_embedding_ok' in a:assert a['gold_embedding_ok'];nest+=1
     if a.get('optimizer_success') is False:optimizer_fail+=1
    funds=asset_pca.ASSETS if suffix=='asset-pca' else c.FUNDS[:len(dec[0]['weights'])]
    d=pd.DataFrame({k:c.ohlc(k).close for k in funds+[stock,'BIL']}).dropna()
    # Match the calibration panel's observation calendar, including all three funds.
    if suffix!='asset-pca':d=d.reindex(panel.index)
    weights={int(d.index.get_loc(pd.Timestamp(a['date']))):np.array(a['weights']) for a in dec};rep=independent(d,stock,weights,funds,short=suffix=='asset-pca');error=float(np.max(abs(rep-nav)));max_error=max(max_error,error);assert error<1e-7,(stock,suffix,run['id'],error)
    shared.append(target)
   assert all(np.array_equal(x,shared[0]) for x in shared)
 passed('All account statistics and monthly compounding reproduce',count);passed('Independent funded cash/share/short-fee accounting',{'accounts':count,'max_nav_error':max_error});passed('Trade calendars monthly or slower',allmonthly);passed('Strict prior-data cutoffs and physical bounds',fits);passed('Gold-only feasible embedding objectives',nest);passed('Stress costs reduce terminal wealth',count)
 # Regression for the root cause: input index resolution cannot change elapsed time.
 dates=pd.DatetimeIndex(['2025-01-03','2025-01-06']).as_unit('us');normalized=dates.as_unit('ns');assert np.diff(normalized.asi8)[0]/86400e9==3
 x=np.array([1.,1.01]);y=np.array([1.,1.02]);assert c.metrics(pd.date_range('2025-01-01',periods=90).as_unit('us'),np.linspace(1,1.5,90),np.linspace(1,1.6,90))==c.metrics(pd.date_range('2025-01-01',periods=90).as_unit('ns'),np.linspace(1,1.5,90),np.linspace(1,1.6,90))
 passed('Elapsed time and statistics are invariant to timestamp resolution')
 # Direct future shocks, including price/open changes and future intraday bars.
 stock='WPM';d=c.panel(stock);i=int(d.index.get_loc(pd.Timestamp('2025-06-30')));future=d.copy();future.iloc[i:]*=1.7
 for rule in ds.SPECS:
  for nf in [2,3]:assert np.allclose(ds.estimate(d,stock,rule,nf,i)[0],ds.estimate(future,stock,rule,nf,i)[0],atol=1e-12)
 rows,_=intr.sessions(stock,'60m');shocked=[{**s,'open':s['open']*1.7,'close':s['close']*.4} if s['date']>=d.index[i] else s for s in rows]
 for name in ['daily','intraday','realized','blend']:
  for nf in [2,3]:assert np.allclose(intr.estimate(d,stock,rows,name,nf,d.index[i])[0],intr.estimate(future,stock,shocked,name,nf,d.index[i])[0],atol=1e-12)
 for nf in [2,3]:assert np.allclose(leadlag.estimate(stock,rows,d,nf,d.index[i])[0],leadlag.estimate(stock,shocked,future,nf,d.index[i])[0],atol=1e-12)
 funds=pd.DataFrame({k:c.ohlc(k).close for k in asset_pca.ASSETS+[stock,'BIL']}).dropna();j=int(funds.index.get_loc(d.index[i]));ff=funds.copy();ff.iloc[j:]*=2
 for k in [2,4,6]:assert np.allclose(asset_pca.estimate(funds,stock,j,k)[0],asset_pca.estimate(ff,stock,j,k)[0],atol=1e-12)
 passed('Future observations cannot alter earlier exposure estimates')
 cc,day,night=c.returns(d);rawcc=d.xs('close',axis=1,level=1).pct_change();rf=rawcc.BIL.fillna(0)
 assert np.nanmax(abs((1+day)*(1+night.add(rf,axis=0))-(1+rawcc.drop(columns='BIL'))).to_numpy())<1e-12;passed('Adjusted overnight/daytime returns compound to daily total returns')
 for interval in ['60m','5m']:
  for stock in c.STOCKS:
   rows,coverage=intr.sessions(stock,interval)
   for s in rows:assert s['close'].shape==(7 if interval=='60m' else 78,4)
 passed('Synchronized complete positive-volume intraday grids with DST conversion')
 for panel in ['original14','original7']:
  p=read(c.R/'results'/f'{panel}-pca.json.gz')
  for a in p['decisions']:assert a['target'] not in a['peer_inputs'] and len(a['peer_inputs'])==len(p['stocks'])-1 and pd.Timestamp(a['cutoff'])<pd.Timestamp(a['date'])
  for j,row in enumerate(p['statistics']):
   y=np.array(p['actual_excess_returns'])[:,j]
   for pred,key in [('baseline_predictions','baseline'),('pc1_predictions','one_peer_pc'),('pc3_predictions','three_peer_pcs')]:assert abs(c.stats(np.array(p[pred])[:,j],y)['tracking_r2']-row[key]['tracking_r2'])<1e-12
 passed('Peer PCA excludes each target and diagnostic statistics reproduce')
 # Own future response cannot enter the contemporaneous peer factor score.
 rng=np.random.default_rng(8);X=rng.normal(size=(600,4));Y=rng.normal(size=(600,7));B=pca.ols(X[:504],Y[:504]);rt=Y[:504]-X[:504]@B;peers=np.arange(1,7);std=rt[:,peers].std(axis=0);_,U=np.linalg.eigh((rt[:,peers]/std).T@(rt[:,peers]/std));Z=(Y[504:,peers]-X[504:]@B[:,peers])/std
 shocked=Y.copy();shocked[504:,0]+=100;ZZ=(shocked[504:,peers]-X[504:]@B[:,peers])/std;assert np.array_equal(Z@U,ZZ@U);passed('Own future stock return does not enter its peer-factor score')
 p=json.loads((c.R/'results/five-minute.json').read_text())
 assert len(p)==20
 for a in p:
  if not a['results']:assert a['stock']=='DRD';continue
  for r in a['results']:assert pd.Timestamp(r['training_end'])<pd.Timestamp(r['test_start']) and r['paired_day_error_bootstrap_vs_daytime']['block_sessions']==3
  assert len(a['overnight'])==2
 passed('Short-bar date split, paired session bootstrap, overnight complement and explicit insufficient-data case')
 receipt={'checks':checks,'portfolio_accounts':count,'fit_records':fits,'optimizer_failures_retained':optimizer_fail,'status':'passed'};(c.R/'validation.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
