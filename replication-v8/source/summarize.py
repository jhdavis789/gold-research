"""Paid-account evidence, same-date ablations and overlapping NAV windows."""
import run as r
import numpy as np,pandas as pd,json,gzip,csv,hashlib
LABELS={
'gold_daily':'Gold tracking control','metals_daily':'Gold + silver · daily fit',
'rates_daily':'Metals + rates · daily fit','conditional_rates_daily':'Changing metals + rates · daily fit',
'rates_balanced':'Metals + rates · 50/25/25','conditional_rates_balanced':'Changing metals + rates · 50/25/25',
'options_daily':'Metals + rates + options · daily fit','conditional_options_daily':'Changing metals + rates + options · daily fit',
'options_balanced':'Metals + rates + options · 50/25/25','conditional_options_balanced':'Changing metals + rates + options · 50/25/25',
'equity_conditional_options_balanced':'Add broad equities · 50/25/25',
'conditional_rates_daily_priority':'Changing metals + rates · 80/10/10',
'conditional_options_daily_priority':'Changing metals + rates + options · 80/10/10',
'volatility_gold':'Gold past-volatility control'}
PAIRS=[('rates_daily','metals_daily','Rates'),('conditional_rates_daily','rates_daily','Changing exposure'),
       ('options_daily','rates_daily','Options'),('conditional_options_daily','conditional_rates_daily','Conditional options'),
       ('conditional_rates_daily_priority','conditional_rates_daily','80/10/10 horizon blend'),
       ('conditional_rates_balanced','conditional_rates_daily','50/25/25 horizon blend'),
       ('conditional_options_daily_priority','conditional_options_daily','80/10/10 option blend'),
       ('conditional_options_balanced','conditional_options_daily','50/25/25 option blend'),
       ('equity_conditional_options_balanced','conditional_options_balanced','Broad equities')]

def read(path):return json.loads(gzip.decompress(path.read_bytes()))
def bootstrap(dates,y,b,n,block=12):
 z=pd.DataFrame({'base':(y-b)**2,'new':(y-n)**2},index=pd.DatetimeIndex(dates)).groupby(pd.DatetimeIndex(dates).to_period('M')).sum().to_numpy()
 rng=np.random.default_rng(20261007);draws=[];count=len(z)
 for _ in range(1200):
  ix=(rng.integers(count,size=int(np.ceil(count/block)))[:,None]+np.arange(block))%count;s=z[ix.ravel()[:count]].sum(axis=0);draws.append(1-s[1]/s[0])
 return {'sse_reduction':float(1-z[:,1].sum()/z[:,0].sum()),'interval95':np.quantile(draws,[.025,.975]).tolist(),'block_months':block,'months':count,'resamples':1200,'interpretation':'Conditional on fitted paths; no refitting/model-selection uncertainty.'}

def greeks(d,row):
 i=int(d.index.get_loc(pd.Timestamp(row['date'])));w=np.array(row['weights']);rate=float(d.rate.iloc[max(i-1,0)]);vol=d[['gold_vol','silver_vol']].iloc[i].to_numpy();delta=w[:2].copy();gamma=np.zeros(2);vega=np.zeros(2)
 for weight,(metal,kind,tenor,strike) in zip(w[4:],r.OPTIONS):
  t=(d.index[i]+pd.DateOffset(months=tenor)-d.index[i]).days/365.25;v=vol[metal];root=v*np.sqrt(t)
  for side,k,sign in r.legs(kind,strike):
   d1=(np.log(1/k)+(rate+.5*v*v)*t)/root;pdf=np.exp(-.5*d1*d1)/np.sqrt(2*np.pi)
   delta[metal]+=weight*sign*(r.ndtr(d1)-(side=='put'));gamma[metal]+=weight*sign*pdf/root;vega[metal]+=weight*sign*pdf*np.sqrt(t)*.01
 return {'date':row['date'],'gold_delta':float(delta[0]),'silver_delta':float(delta[1]),'gold_gamma':float(gamma[0]),'silver_gamma':float(gamma[1]),'gold_vega_1pp':float(vega[0]),'silver_vega_1pp':float(vega[1]),'treasury_weight':float(w[2]),'equity_weight':float(w[3]),'option_premium':row['option_premium_fraction'],'cash_weight':row['cash_after_trade']/row['opening_nav'],'active_option_structures':int((w[4:]>1e-6).sum())}

def row_metrics(stock,run,dates,y):
 m=run['metrics'];x=np.array(run['nav']);xr=np.diff(x)/x[:-1];yr=np.diff(y)/y[:-1];valid=np.diff(dates.asi8)/86400e9<=4
 z={'stock':stock,'model':run['id'],'cadence_months':run['h'],'start':m['start'],'end':m['end'],'sessions':m['daily']['n'],'daily_r2':m['daily']['r2'],'daily_regression_r2':m['daily']['regression_r2'],'daily_rmse':m['daily']['rmse'],'daily_gap_pp':float(np.median(abs(xr[valid]-yr[valid]))*100),'replica_cagr':m['portfolio_cagr'],'stock_cagr':m['stock_cagr'],'replica_vol':float(np.std(xr[valid],ddof=1)*np.sqrt(252)),'stock_vol':float(np.std(yr[valid],ddof=1)*np.sqrt(252)),'terminal_replica':float(x[-1]),'terminal_stock':float(y[-1]),'stress_replica_cagr':run['stress']['portfolio_cagr'],'mean_option_premium':float(np.mean([a['option_premium_fraction'] for a in run['ledger']])),'mean_abs_rates_weight':float(np.mean([abs(a['weights'][2]) for a in run['ledger']])),'solver_failures':sum(not z.get('optimizer_success',True) for z in run['decisions']),'fallbacks':sum(z.get('fallback',False) for z in run['decisions']),'decisions':len(run['decisions'])}
 z['volatility_cap_decisions']=sum(v.get('gold_cap_binding',False) for v in run['decisions'])
 for a in m['horizons']:
  h=a['months'];z[f'r2_{h}m']=a['tracking_r2'];z[f'gap_{h}m_pp']=a['median_absolute_gap_pp'];z[f'n_{h}m']=a['n']
 return z

def main():
 manifest=json.loads((r.R/'results/manifest.json').read_text());assert len(manifest.get('runs',[]))==20 and all(z['exit_code']==0 for z in manifest['runs']);prior=[]
 risk={z['company']['ticker']:z for z in read(r.R/'results/risk-controls.json.gz')};rows=[];paths={};exposure={};rolling=[];wpm_boot=[];fits=0
 for comp in r.c.v5.OLD['universe']:
  stock=comp['ticker'];z=read(r.R/'results'/f'{stock}.json.gz');assert z['provenance']==manifest['provenance'];assert z['dates']==risk[stock]['dates']
  d,state=r.load(stock);dates=pd.DatetimeIndex(z['dates']).as_unit('ns');y=np.array(z['stock_nav']);mi=pd.Series(np.arange(len(dates)),index=dates).groupby(dates.to_period('M')).last().to_numpy();assert mi[0]==0
  oldpath=r.R.parent/'model_v7/results'/f'{stock}-sessions.json.gz';old=read(oldpath);ref=next(a for a in old['runs'] if a['id']=='daily_ew_market');od=pd.DatetimeIndex(old['dates']).as_unit('ns');oi=od.get_indexer(dates)
  assert np.all(oi>=0);ox=np.array(ref['nav'])[oi];ox=ox/ox[0]
  prior.append({'stock':stock,'model':'v7_daily_metals_equities_q','same_date_metrics':r.metrics(dates,ox,y),'sample_rebased':bool(oi[0]!=0),'source_sha256':hashlib.sha256(oldpath.read_bytes()).hexdigest(),'interpretation':'Preserved earlier paid path, measured against current stock account; subset rebasing adds no fresh-window entry/exit fees.'})
  paths[stock]={'dates':[str(dates[i].date()) for i in mi],'stock':y[mi].tolist(),'runs':{}};exposure[stock]={};runs=z['runs']+risk[stock]['runs'];lookup={v['id']:v for v in runs}
  for run in runs:
   fits+=len(run['decisions']);rows.append(row_metrics(stock,run,dates,y));x=np.array(run['nav']);paths[stock]['runs'][run['id']]=x[mi].tolist();exposure[stock][run['id']]=[greeks(d,rr) for rr in run['ledger']]
   for h in [12,36,60]:
    for a,b in zip(mi[:-h],mi[h:]):
     yrs=(dates[b]-dates[a]).days/365.25;rx=x[b]/x[a]-1;sy=y[b]/y[a]-1
     rolling.append({'stock':stock,'model':run['id'],'horizon_months':h,'start':str(dates[a].date()),'end':str(dates[b].date()),'replica_return':float(rx),'stock_return':float(sy),'gap_pp':float((sy-rx)*100),'replica_cagr':float((1+rx)**(1/yrs)-1),'stock_cagr':float((1+sy)**(1/yrs)-1)})
  if stock=='WPM':
   for h in [1,3]:
    suffix='_m' if h==1 else '_q'
    for new,base,label in PAIRS:
     xx=np.array(lookup[new+suffix]['nav']);bb=np.array(lookup[base+suffix]['nav']);valid=np.diff(dates.asi8)/86400e9<=4
     yr=np.diff(y)/y[:-1];xr=np.diff(xx)/xx[:-1];br=np.diff(bb)/bb[:-1]
     wpm_boot.append({'new':new+suffix,'base':base+suffix,'horizon_months':0,**bootstrap(dates[1:][valid],yr[valid],br[valid],xr[valid])})
     a,b=mi[:-12],mi[12:];wpm_boot.append({'new':new+suffix,'base':base+suffix,'horizon_months':12,**bootstrap(dates[b],y[b]/y[a]-1,bb[b]/bb[a]-1,xx[b]/xx[a]-1,24)})
 a=pd.DataFrame(rows);aggregate=[];comparisons=[];profit=[]
 rollframe=pd.DataFrame(rolling)
 for (model,h),g in rollframe.groupby(['model','horizon_months'],sort=False):
  bycompany=g.groupby('stock').apply(lambda x:float((x.stock_return>x.replica_return).mean()),include_groups=False)
  profit.append({'model':model,'horizon_months':int(h),'companies':len(bycompany),'windows':len(g),'median_company_stock_win_fraction':float(bycompany.median()),'median_company_return_gap_pp':float(g.groupby('stock').gap_pp.median().median())})
 for model,g in a.groupby('model',sort=False):
  aggregate.append({'model':model,'companies':len(g),**{f'median_{c}':float(g[c].median()) for c in ['daily_r2','r2_1m','r2_3m','r2_12m','r2_36m','r2_60m','replica_cagr','mean_option_premium']},'replica_beats_stock':int((g.replica_cagr>g.stock_cagr).sum())})
 for new,base,label in PAIRS:
  for suffix in ['_m','_q']:
   xx=a[a.model==new+suffix].set_index('stock');bb=a[a.model==base+suffix].set_index('stock');difference=xx[['daily_r2','r2_12m','replica_cagr']]-bb[['daily_r2','r2_12m','replica_cagr']]
   comparisons.append({'test':label,'new':new+suffix,'base':base+suffix,'companies':len(difference),'daily_wins':int((difference.daily_r2>1e-9).sum()),'annual_wins':int((difference.r2_12m>1e-9).sum()),'median_daily_delta':float(difference.daily_r2.median()),'median_annual_delta':float(difference.r2_12m.median()),'median_cagr_delta':float(difference.replica_cagr.median())})
 pre=read(r.R/'review/WPM-precost-60-structures.json.gz');pre_rows=[row_metrics('WPM',v,pd.DatetimeIndex(pre['dates']).as_unit('ns'),np.array(pre['stock_nav'])) for v in pre['runs']]
 out={'cutoff':'2026-09-30','companies':r.c.v5.OLD['universe'],'models':[{'id':k,'label':v} for k,v in LABELS.items()],'accounts':len(rows),'fit_decisions':fits,'metrics':rows,'aggregate':aggregate,'comparisons':comparisons,'profit_by_horizon':profit,'paths':paths,'exposures':exposure,'wpm_bootstrap':wpm_boot,'teacher':json.loads((r.R/'results/teacher-summary.json').read_text()),'wpm_precost_trials':pre_rows,'options_access':json.loads((r.R/'options-access.json').read_text()),'source_provenance':manifest['provenance'],'caveats':['Sequential historical exploration after earlier outcomes; no untouched holdout.','Adjusted bullion/cash/Treasury funds; no verified contract-level futures P&L.','Hypothetical European option marks, not actual option chains or execution prices.','Twenty surviving companies; company samples differ and corporate history can change exposures.','Monthly/quarterly physical quantities; overlap does not create independent annual observations.','Peer PCA diagnostic is explanatory; no peer or miner basket is a portfolio holding.']}
 out['prior_v7']=prior
 for path in out['paths'].values():
  path['stock']=[round(v,10) for v in path['stock']]
  path['runs']={k:[round(v,10) for v in values] for k,values in path['runs'].items()}
 for stocks in out['exposures'].values():
  for values in stocks.values():
   for item in values:
    for key,value in item.items():
     if isinstance(value,float):item[key]=round(value,8)
 out['display_precision']={'monthly_nav_decimals':10,'exposure_decimals':8,'metrics':'full double precision; retained private daily NAVs unchanged'}
 out['exposure_fields']=list(next(iter(next(iter(out['exposures'].values())).values()))[0])
 out['exposures']={stock:{model:[[row[k] for k in out['exposure_fields']] for row in values] for model,values in runs.items()} for stock,runs in out['exposures'].items()}
 P=r.R/'public';P.mkdir(exist_ok=True);(P/'evidence.json').write_text(json.dumps(out,separators=(',',':'),allow_nan=False)+'\n');a.to_csv(P/'all-results.csv',index=False);pd.DataFrame(rolling).to_csv(P/'rolling-results.csv',index=False);pd.DataFrame(pre_rows).to_csv(P/'WPM-precost-comparison.csv',index=False)
 print(a[a.stock=='WPM'][['model','daily_r2','r2_1m','r2_3m','r2_12m','replica_cagr','mean_option_premium']].round(4).to_string(index=False));print(pd.DataFrame(comparisons).round(4).to_string(index=False));print('Accounts',len(rows),'decisions',fits)
if __name__=='__main__':main()
