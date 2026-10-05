"""Synchronized bar calibration; monthly/quarterly financed portfolios."""
import common as c
import numpy as np,pandas as pd,json
DATA=c.R.parent/'data/v7_intraday_20261004'
BARCACHE={}
def bars(symbol,interval):
 key=(symbol,interval)
 if key not in BARCACHE:
  d=pd.read_csv(DATA/interval/(symbol+'.csv'));d.index=pd.DatetimeIndex(pd.to_datetime(d.timestamp,utc=True)).tz_convert('America/New_York');d=d.drop(columns='timestamp')
  d=d[(d.volume>0)&(d.open>0)&(d.close>0)]
  BARCACHE[key]=d
 return BARCACHE[key]
def sessions(stock,interval):
 keys=c.FUNDS+[stock];a=pd.concat({k:bars(k,interval) for k in keys},axis=1,sort=True).dropna()
 expected=np.arange(570,960,60 if interval=='60m' else 5);rows=[];rejected=0
 for day,z in a.groupby(a.index.normalize()):
  minutes=z.index.hour*60+z.index.minute
  if not np.array_equal(minutes,expected):rejected+=1;continue
  op=z.xs('open',axis=1,level=1).iloc[0].to_numpy();cl=z.xs('close',axis=1,level=1).to_numpy()
  if not np.isfinite(cl).all() or not np.isfinite(op).all():rejected+=1;continue
  rows.append({'date':day.tz_localize(None),'open':op,'close':cl})
 return rows,{'common_complete_days':len(rows),'rejected_common_days':rejected,'all_factor_days':len(bars('GLD',interval).index.normalize().unique()),'interval':interval}
def estimate(d,stock,rows,name,nf,date):
 train=[s for s in rows if s['date']<date][-126:];assert len(train)==126
 dates=pd.DatetimeIndex([s['date'] for s in train]);sw=2.**(-np.arange(125,-1,-1)/63);sw/=sw.sum()
 cc,day,night=c.returns(d);X=cc.loc[dates,c.FUNDS].to_numpy();y=cc.loc[dates,stock].to_numpy()
 dayG=np.einsum('ni,n,nj->ij',X[:,:nf],sw,X[:,:nf]);dayb=np.einsum('ni,n,n->i',X[:,:nf],sw,y);dayy=float(np.sum(sw*y*y))
 G=np.zeros((nf,nf));b=np.zeros(nf);yy=0.
 for wt,s in zip(sw,train):
  marks=np.vstack([s['open'],s['close']]);r=marks[1:]/marks[:-1]-1;xx=r[:,:nf];z=r[:,-1]
  G+=wt*np.einsum('ni,nj->ij',xx,xx);b+=wt*np.einsum('ni,n->i',xx,z);yy+=wt*float(np.sum(z*z))
 if name in ['realized','blend']:
  X=night.loc[dates,c.FUNDS].to_numpy()[:,:nf];y=night.loc[dates,stock].to_numpy()
  G+=np.einsum('ni,n,nj->ij',X,sw,X);b+=np.einsum('ni,n,n->i',X,sw,y);yy+=float(np.sum(sw*y*y))
 if name=='daily':G,b,yy=dayG,dayb,dayy
 if name=='blend':G,b,yy=.5*(G+dayG),.5*(b+dayb),.5*(yy+dayy)
 w,info=c.fit_cov(G,b,yy);info.update(cutoff=str(dates[-1].date()),first_training_day=str(dates[0].date()),complete_days=126)
 return w,info
def main():
 summary=[];coverage=[];metrics=[]
 for comp in c.v5.OLD['universe']:
  stock=comp['ticker'];d=c.panel(stock);rows,cover=sessions(stock,'60m');coverage.append({'stock':stock,**cover})
  dates=set(d.index);rows=[s for s in rows if s['date'] in dates]
  assert len(rows)>126,(stock,len(rows))
  eligible=rows[126]['date'];mi=d.groupby(d.index.to_period('M')).tail(1).index;start=next(t for t in mi if t>=eligible);first=int(d.index.get_loc(start));runs=[]
  for name in ['daily','intraday','realized','blend']:
   for nf in [2,3]:
    for h in [1,3]:
     decisions=[];weights={}
     for i in c.trade_dates(d,first,h):
      w,info=estimate(d,stock,rows,name,nf,d.index[i]);weights[i]=w;decisions.append({'date':str(d.index[i].date()),'weights':w.tolist(),**info})
     nav,y,ledger=c.account(d,stock,weights,nf);stress,sy,_=c.account(d,stock,weights,nf,.001);met=c.metrics(d.index[first:],nav,y);mid=name+('_metals' if nf==2 else '_market')+('_m' if h==1 else '_q')
     runs.append({'id':mid,'metrics':met,'stress':c.metrics(d.index[first:],stress,sy),'nav':nav.tolist(),'decisions':decisions,'ledger':ledger});metrics.append({'stock':stock,'model':mid,'start':str(start.date()),'daily_r2':met['daily']['r2'],'monthly_r2':met['monthly']['r2'],'portfolio_cagr':met['portfolio_cagr'],'stock_cagr':met['stock_cagr']})
  c.save(stock+'-hourly.json.gz',{'company':comp,'coverage':cover,'dates':[str(t.date()) for t in d.index[first:]],'stock_nav':y.tolist(),'runs':runs})
  summary.append({'company':comp,'coverage':cover,'runs':[{k:v for k,v in a.items() if k not in ['nav','decisions','ledger']} for a in runs]})
  print(stock,'hourly',len(rows),flush=True)
 pd.DataFrame(metrics).to_csv(c.R/'results/hourly-summary.csv',index=False);(c.R/'results/hourly-summary.json').write_text(json.dumps(summary,separators=(',',':'),allow_nan=False));(c.R/'results/hourly-coverage.json').write_text(json.dumps(coverage,indent=2))
def five_minute():
 output=[]
 for stock in c.STOCKS:
  rows,coverage=sessions(stock,'5m')
  if len(rows)<10:
   output.append({'stock':stock,'coverage':coverage,'results':[],'status':'Insufficient complete positive-volume sessions; no estimate reported.'});continue
  split=len(rows)//2;train=rows[:split];test=rows[split:];result=[]
  for minutes in [5,15,30,60,390]:
   # Final thirty minutes are retained in the 60-minute grid; no cross-day return.
   ix=np.r_[np.arange(minutes//5-1,78,minutes//5),77];ix=np.unique(ix)
   if minutes==390:ix=np.array([77])
   for nf in [2,3]:
    X=[];y=[]
    for s in train:
     marks=np.vstack([s['open'],s['close'][ix]]);r=marks[1:]/marks[:-1]-1;X.extend(r[:,:nf]);y.extend(r[:,-1])
    X=np.array(X);y=np.array(y);w,_=c.gram_fit([(X,y,1)],np.ones(len(y))/len(train),nf)
    tx=[];ty=[];perday=[]
    for s in test:
     marks=np.vstack([s['open'],s['close'][ix]]);rel=marks/marks[0];nav=1+(rel[:,:nf]-1)@w;pred=nav[1:]/nav[:-1]-1;actual=marks[1:,-1]/marks[:-1,-1]-1
     tx.extend(pred);ty.extend(actual);perday.append({'date':str(s['date'].date()),'stock_day_return':float(marks[-1,-1]/marks[0,-1]-1),'model_day_return':float(nav[-1]-1)})
    result.append({'minutes':minutes,'funds':nf,'weights':w.tolist(),'train_days':len(train),'test_days':len(test),'training_end':str(train[-1]['date'].date()),'test_start':str(test[0]['date'].date()),'bar_metrics':c.stats(np.array(tx),np.array(ty)),'day_metrics':c.stats(np.array([x['model_day_return'] for x in perday]),np.array([x['stock_day_return'] for x in perday])),'test_day_returns':perday})
  output.append({'stock':stock,'coverage':coverage,'results':result});print(stock,'5m',len(rows),flush=True)
 (c.R/'results/five-minute.json').write_text(json.dumps(output,separators=(',',':'),allow_nan=False))
if __name__=='__main__':
 main();five_minute()
