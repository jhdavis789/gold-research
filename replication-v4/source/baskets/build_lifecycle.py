"""Private vendor histories -> aggregate lifecycle cohort research; no raw public panel."""
from pathlib import Path
import sys,json,gzip,hashlib
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'model_v5'))
import run as engine
SITE=Path(sys.argv[1])
BASE=Path(sys.argv[2])
D=json.loads(gzip.decompress((BASE/'daily-data.json.gz').read_bytes()))
L=json.loads((R/'lifecycle.json').read_text())
cal=engine.series('GLD').loc['2009-01-01':'2026-09-30'].index
cash=engine.series('BIL').reindex(cal)
rows=[]
for p in (R/'data/raw/api').glob('*/request.json'):
 req=json.loads(p.read_text())
 if any('P_TOTAL_RETURN(01/01/2007,09/30/2026,D)' in x for x in req['payload']['data']['formulas']):rows+=json.loads((p.parent/'response.json').read_text()).get('data',[])
def close(s,date):
 if s=='PAAS':
  j=json.loads((R/'data/yahoo/PAAS.json').read_text())['chart']['result'][0]
  a=pd.Series(j['indicators']['quote'][0]['close'],index=pd.to_datetime(j['timestamp'],unit='s',utc=True).tz_convert(None).normalize())
 else:
  p=next((R.parent/'data').glob('*/'+s+'.csv'));a=pd.read_csv(p,parse_dates=['date']).set_index('date')['close']
 return float(a.loc[date])
allpaths={};checks=[];ledger=[]
for c in L:
 a=[x for x in rows if x.get('requestId')==c['id']];names=[x for x in a if x.get('name')];assert len(names)==1 and c['name_check'] in names[0]['name'];c['fsymId']=names[0]['fsymId']
 frame=pd.DataFrame([x for x in a if x.get('price') is not None]).set_index('date').sort_index();frame.index=pd.to_datetime(frame.index)
 frame=frame.loc[c['listing']:];assert len(frame)>750
 tr=frame.tr.fillna(0)/100;assert tr.min()>-1
 stock=(1+tr).cumprod();stock/=stock.iloc[0]
 end=pd.Timestamp(c['exit']);prev=frame.index[frame.index<end][-1]
 marks={s:close(s,end) for s in c['shares']}
 payout=c['cash']+sum(c['shares'][s]*v for s,v in marks.items())
 terminal=stock.loc[prev]*payout/float(frame.loc[prev,'price'])
 lastquote=float(stock.loc[frame.index[frame.index<=end][-1]])
 terminal_record={'ticker':c['ticker'],'date':c['exit'],'previous_date':str(prev.date()),'previous_price':float(frame.loc[prev,'price']),'payout':payout,'acquirer_close':marks,'terminal_ratio':float(terminal/stock.loc[prev]),'last_quote_nav':lastquote}
 ledger.append(terminal_record)
 # Fit only to actual pre-event observations; no synthetic zero in the estimation target.
 train=stock.loc[:prev]
 d=pd.DataFrame({**{k:engine.series(k) for k in engine.ASSETS+['BIL','^GVZ']},c['ticker']:train});d['^GVZ']=d['^GVZ'].ffill();d=d.dropna().loc[:prev]
 months=d.groupby(d.index.to_period('M')).tail(1).index;first=int(d.index.get_loc(months[37]));p=engine.prepare(d,first)
 start=d.index[first];c['history_start']=str(d.index[0].date());c['start']=str(start.date());c['end']=c['exit']
 dates=cal[(cal>=start)];active=dates[dates<end]
 y=stock.reindex(active);assert y.notna().all();y=y/y.iloc[0];base_norm=float(stock.loc[start]);y*=.9998;y.iloc[0]=1
 extended=pd.Series(index=dates,dtype=float);extended.loc[active]=y
 post=dates[dates>=end];extended.loc[post]=terminal/base_norm*.9998*.9998*cash.loc[post]/cash.loc[end]
 alternate=extended.copy()
 if c['ticker']=='GBG':alternate.loc[post]=lastquote/base_norm*.9998*.9998*cash.loc[post]/cash.loc[end]
 models={}
 for mid,spid in [('daily_metals_quarterly','metals_ewq'),('daily_metals_market_quarterly','market_q'),('unlevered_gold',None)]:
  if spid:
   spec=next(s for s in engine.SPECS if s['id']==spid)
  else:spec={'id':mid,'funds':1,'window':756,'h':3,'half':126,'lag':'day','option':None,'blend':False}
  inds=[first]+[int(i) for i in p['quarter'] if first<i<len(d)-1];weights={}
  for i in inds:
   if spid:w,info=engine.fit(p,c['ticker'],spec,i);assert info['cutoff']<str(d.index[i].date())
   else:w=np.array([1.])
   weights[i]=w
  v,detail=engine.simulate(p,spec,weights)
  # engine's final close liquidation occurs on last pre-event session, not the announcement date.
  vp=pd.Series(v,index=d.index[first:]);ex=pd.Series(index=dates,dtype=float);ex.loc[vp.index]=vp
  tail=dates[dates>vp.index[-1]];ex.loc[tail]=vp.iloc[-1]*cash.loc[tail]/cash.loc[vp.index[-1]]
  assert ex.notna().all() and np.isfinite(ex).all()
  models[mid]=ex
 allpaths[c['ticker']]={'stock':extended,'alternate':alternate,'models':models,'exit':end,'start':start,'addition':True}
 checks.append({'ticker':c['ticker'],'start':str(start.date()),'end':c['exit'],'sessions':len(d),'stock_to_event':float(terminal/base_norm-1),'terminal_case':'assumed zero and last quote' if c['ticker']=='GBG' else 'contractual consideration marked at close'})
 print(checks[-1],flush=True)
# Existing paths unchanged; no extra fitting or future endpoint eligibility screen.
for c in D['universe']:
 rr=[r for r in D['runs'] if r['stock']==c['ticker'] and r['model'] in ['daily_metals_quarterly','daily_metals_market_quarterly','unlevered_gold']]
 allpaths[c['ticker']]={'stock':pd.Series(rr[0]['stock_nav'],index=pd.to_datetime(rr[0]['dates'])),'models':{r['model']:pd.Series(r['portfolio'],index=pd.to_datetime(r['dates'])) for r in rr},'exit':pd.Timestamp('2099-01-01'),'start':pd.Timestamp(c['start']),'addition':False}
cohorts=[]
for year in range(2011,2026):
 start=cal[cal>=f'{year}-01-01'][0];dates=cal[cal>=start];years=(dates[-1]-start).days/365.25
 for scenario in ['survivors','acquired','failed_zero','failed_last_quote']:
  chosen={s:p for s,p in allpaths.items() if p['start']<=start<p['exit'] and (not p['addition'] or scenario!='survivors') and (s!='GBG' or scenario.startswith('failed'))}
  ys=[];xs={m:[] for m in ['unlevered_gold','daily_metals_quarterly','daily_metals_market_quarterly']}
  for s,p in chosen.items():
   y=p['alternate'] if s=='GBG' and scenario=='failed_last_quote' else p['stock'];y=y.reindex(dates);assert y.notna().all();ys.append((y/y.iloc[0]).to_numpy())
   for m in xs:
    x=p['models'][m].reindex(dates);assert x.notna().all();xs[m].append((x/x.iloc[0]).to_numpy())
  if not ys:continue
  arr=np.array(ys);nav=arr.mean(axis=0);total=arr[:,-1]-1;n=len(arr);order=np.argsort(total)
  groups={}
  for name,f,top in [('bottom10',.1,False),('bottom25',.25,False),('top25',.25,True),('top10',.1,True)]:
   count=int(np.ceil(n*f));ix=order[-count:] if top else order[:count];v=float(arr[ix,-1].mean());groups[name]={'n':count,'total':v-1,'cagr':v**(1/years)-1}
  item={'year':year,'scenario':scenario,'start':str(start.date()),'end':str(dates[-1].date()),'n':n,'members':list(chosen),'total':float(nav[-1]-1),'cagr':float(nav[-1]**(1/years)-1),'drawdown':float(np.min(nav/np.maximum.accumulate(nav)-1)),'percentiles':{str(q):float(np.quantile(total,q/100)) for q in [10,25,50,75,90]},'groups':groups,'models':{}}
  for m,xx in xs.items():
   x=np.mean(xx,axis=0);dr=np.diff(x)/x[:-1];sr=np.diff(nav)/nav[:-1]
   item['models'][m]={'total':float(x[-1]-1),'cagr':float(x[-1]**(1/years)-1),'daily_tracking_r2':float(1-np.sum((dr-sr)**2)/np.sum((sr-sr.mean())**2))}
  cohorts.append(item)
(R/'terminal-ledger-private.json').write_text(json.dumps(ledger,indent=2));(R/'lifecycle-validation.json').write_text(json.dumps(checks,indent=2))
out={'companies':L,'cohorts':cohorts,'assumptions':'Fixed initial equal-dollar cohorts; acquisition consideration marked at completion close, liquidated into BIL; failed-company zero and last-quote scenarios; no new entrants after start. Aggregate research only; not a historical industry universe.','source':'Private FactSet Formula daily total return/price input; existing Yahoo proxy and surviving company inputs; primary lifecycle sources. No raw licensed input published.'}
(SITE/'lifecycle-summary.json').write_text(json.dumps(out,separators=(',',':'),allow_nan=False))
# Preserve private normalized analysis for accounting audits, never in site tree.
with gzip.open(R/'private-lifecycle-paths.json.gz','wt') as f:json.dump({s:{'dates':[str(t.date()) for t in p['stock'].index],'nav':p['stock'].tolist(),'models':{m:v.tolist() for m,v in p['models'].items()}} for s,p in allpaths.items() if p['addition']},f)
print('cohorts',len(cohorts))
