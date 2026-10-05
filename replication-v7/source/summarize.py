"""Derived paired statistics, block uncertainty and retained trial catalogue."""
import common as c
import json,gzip,hashlib
import numpy as np,pandas as pd
def read(stock,suffix):return json.loads(gzip.decompress((c.R/'results'/f'{stock}-{suffix}.json.gz').read_bytes()))
def bootstrap(dates,y,base,new,block,resamples=1200):
 dates=pd.DatetimeIndex(dates);a=pd.DataFrame({'base':(y-base)**2,'new':(y-new)**2},index=dates).groupby(dates.to_period('M')).sum().to_numpy();n=len(a);rng=np.random.default_rng(20261004);vals=[]
 for _ in range(resamples):
  ix=(rng.integers(n,size=int(np.ceil(n/block)))[:,None]+np.arange(block))%n;s=a[ix.ravel()[:n]].sum(axis=0);vals.append(1-s[1]/s[0])
 return {'sse_reduction':float(1-a[:,1].sum()/a[:,0].sum()),'interval95':np.quantile(vals,[.025,.975]).tolist(),'month_blocks':block,'months':n,'resamples':resamples}
def main():
 groups={name:json.loads((c.R/'results'/f'{name}-summary.json').read_text()) for name in ['session','hourly','leadlag','asset-pca']};rows=[];win=[];rolling=[];perstock={}
 for comp in c.v5.OLD['universe']:
  stock=comp['ticker'];packages={s:read(stock,s) for s in ['sessions','hourly','leadlag','asset-pca']};perstock[stock]=packages
  for group,p in packages.items():
   for run in p['runs']:
    met=run['metrics'];rows.append({'stock':stock,'group':group,'model':run['id'],'start':met['start'],'end':met['end'],'sessions':met['daily']['n'],'daily_r2':met['daily']['r2'],'monthly_r2':met['monthly']['r2'],'portfolio_cagr':met['portfolio_cagr'],'stock_cagr':met['stock_cagr'],'stress_daily_r2':run['stress']['daily']['r2']})
    if group!='sessions':continue
    dates=pd.DatetimeIndex(p['dates']).as_unit('ns');nav=np.array(run['nav']);y=np.array(p['stock_nav']);mi=pd.Series(np.arange(len(dates)),index=dates).groupby(dates.to_period('M')).last().to_numpy();mi=np.unique(np.r_[0,mi])
    for h in [36,60]:
     outcomes=[]
     for a,b in zip(mi[:-h],mi[h:]):
      yrs=(dates[b]-dates[a]).days/365.25;sc=(y[b]/y[a])**(1/yrs)-1;rc=(nav[b]/nav[a])**(1/yrs)-1
      outcomes.append({'stock':stock,'model':run['id'],'horizon_months':h,'start':str(dates[a].date()),'end':str(dates[b].date()),'stock_cagr':float(sc),'replica_cagr':float(rc),'gap':float(sc-rc)})
     rolling.extend(outcomes)
  # Paired uncertainty on Wheaton, not pooled across unequal company date ranges.
  if stock=='WPM':
   for group in ['sessions','hourly']:
    p=packages[group];runs={r['id']:r for r in p['runs']};dates=pd.DatetimeIndex(p['dates']).as_unit('ns');y=np.diff(p['stock_nav'])/p['stock_nav'][:-1];valid=np.diff(dates.asi8)/86400e9<=4
    other=packages['leadlag']['runs'] if group=='hourly' else []
    for run in list(runs.values())+other:
     id=run['id'];ref=('daily_ew_'+id.split('_')[-1]) if group=='sessions' else 'daily_'+('_'.join(id.split('_')[-2:]))
     if ref not in runs or id==ref:continue
     base=np.diff(runs[ref]['nav'])/runs[ref]['nav'][:-1];new=np.diff(run['nav'])/run['nav'][:-1]
     win.append({'stock':stock,'group':group,'model':id,'baseline':ref,**bootstrap(dates[1:][valid],y[valid],base[valid],new[valid],12 if group=='sessions' else 3)})
 a=pd.DataFrame(rows);aggregates=[]
 for (group,model),z in a.groupby(['group','model']):
  if group in ['hourly','leadlag']:ref='daily_'+'_'.join(model.split('_')[-2:]);refgroup='hourly'
  elif group=='sessions':ref='daily_ew_'+model.split('_')[-1];refgroup='sessions'
  else:ref='asset_pca6';refgroup='asset-pca'
  b=a[(a.group==refgroup)&(a.model==ref)].set_index('stock');pair=z.set_index('stock').join(b[['daily_r2']],rsuffix='_baseline')
  aggregates.append({'group':group,'model':model,'companies':len(z),'mean_daily_r2':float(z.daily_r2.mean()),'mean_monthly_r2':float(z.monthly_r2.mean()),'mean_delta_daily_r2':float((pair.daily_r2-pair.daily_r2_baseline).mean()),'wins':int((pair.daily_r2>pair.daily_r2_baseline+1e-9).sum()),'baseline':ref})
 pca=json.loads((c.R/'results/pca-summary.json').read_text());pcab=[]
 for panel in pca:
  p=json.loads(gzip.decompress((c.R/'results'/f"{panel['panel']}-pca.json.gz").read_bytes()));j=p['stocks'].index('WPM');y=np.array(p['actual_excess_returns'])[:,j];b=np.array(p['baseline_predictions'])[:,j]
  for key in ['pc1_predictions','pc3_predictions']:pcab.append({'panel':panel['panel'],'diagnostic':key,**bootstrap(p['dates'],y,b,np.array(p[key])[:,j],12)})
 five=json.loads((c.R/'results/five-minute.json').read_text());sources=json.loads((c.R.parent/'data/v7_intraday_20261004/receipt.json').read_text());access=json.loads((c.R/'factset-access.json').read_text())
 data={'cutoff':'2026-09-30','portfolio_rules':41,'portfolio_accounts':len(rows),'companies':c.v5.OLD['universe'],'aggregates':aggregates,'metrics':rows,'session_summaries':groups['session'],'hourly_summaries':groups['hourly'],'leadlag_summaries':groups['leadlag'],'asset_pca_summaries':groups['asset-pca'],'five_minute':five,'pca':pca,'wpm_portfolio_bootstrap':win,'wpm_pca_bootstrap':pcab,'intraday_sources':[{k:r.get(k) for k in ['symbol','interval','rows','start','end','http_status']} for r in sources['requests']],'factset_probe':{k:access[k] for k in ['http_status','content_type','response_bytes','docs']},'caveats':['Historical exploration after earlier results, not an untouched holdout.','Bullion funds, not validated rolled futures.','PCA peer factors are explanations, never portfolio holdings.','Hourly testing covers a recent metal-price regime; company start dates may differ.','Five-minute complete positive-volume sessions are shorter than raw coverage; DRD has insufficient complete sessions.','Long-horizon accounts are ongoing NAV ratios, with overlapping windows.']}
 (c.R/'public').mkdir(exist_ok=True);(c.R/'public/evidence.json').write_text(json.dumps(data,separators=(',',':'),allow_nan=False)+'\n');a.to_csv(c.R/'public/all-results.csv',index=False);pd.DataFrame(rolling).to_csv(c.R/'public/rolling-results.csv',index=False)
 manifest={'created_at':pd.Timestamp.now(tz='UTC').isoformat(),'rules':41,'portfolio_accounts':len(rows),'design_hashes':{n:hashlib.sha256((c.R/n).read_bytes()).hexdigest() for n in ['DESIGN.md','FOLLOWUP.md']},'engine_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in c.R.glob('*.py')},'intraday_receipt_hash':hashlib.sha256((c.R.parent/'data/v7_intraday_20261004/receipt.json').read_bytes()).hexdigest()}
 (c.R/'results/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(a[(a.stock=='WPM')].round(4).to_string(index=False));print(pd.DataFrame(aggregates).round(4).to_string(index=False))
if __name__=='__main__':main()
