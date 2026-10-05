"""Overnight complement and session-block uncertainty for the short bar experiment."""
import common as c,intraday as intr
import numpy as np,pandas as pd,json
def block_estimate(a,b,block=3):
 a=np.array(a);b=np.array(b);rng=np.random.default_rng(20261004);n=len(a);v=[]
 for _ in range(1500):
  ix=(rng.integers(n,size=int(np.ceil(n/block)))[:,None]+np.arange(block))%n;j=ix.ravel()[:n];v.append(1-np.sum(a[j]**2)/np.sum(b[j]**2))
 return {'sse_reduction':float(1-np.sum(a*a)/np.sum(b*b)),'interval95':np.quantile(v,[.025,.975]).tolist(),'block_sessions':block,'resamples':1500}
def main():
 p=c.R/'results/five-minute.json';output=json.loads(p.read_text())
 for a in output:
  if not a['results']:continue
  stock=a['stock'];rows,_=intr.sessions(stock,'5m');split=len(rows)//2;dates=pd.DatetimeIndex([s['date'] for s in rows]);d=c.panel(stock);cc,day,night=c.returns(d);overnight=[]
  for nf in [2,3]:
   X=night.loc[dates,c.FUNDS].to_numpy()[:,:nf];y=night.loc[dates,stock].to_numpy();w,_=c.gram_fit([(X[:split],y[:split],1)],np.ones(split)/split,nf)
   overnight.append({'funds':nf,'weights':w.tolist(),'train_days':split,'test_days':len(rows)-split,'test_metrics':c.stats(X[split:]@w,y[split:])})
   baseline=next(r for r in a['results'] if r['funds']==nf and r['minutes']==390);by=np.array([x['stock_day_return']-x['model_day_return'] for x in baseline['test_day_returns']])
   for r in a['results']:
    if r['funds']!=nf:continue
    err=np.array([x['stock_day_return']-x['model_day_return'] for x in r['test_day_returns']]);r['paired_day_error_bootstrap_vs_daytime']=block_estimate(err,by)
  a['overnight']=overnight
  if stock!='WPM':continue
  # Training beta stability: resample entire sessions, retaining all their bars.
  rng=np.random.default_rng(20261004);tr=rows[:split]
  for r in a['results']:
   if r['funds']!=2:continue
   minutes=r['minutes'];ix=np.unique(np.r_[np.arange(minutes//5-1,78,minutes//5),77]);Gs=[];bs=[];ys=[]
   for s in tr:
    marks=np.vstack([s['open'],s['close'][ix]]);ret=marks[1:]/marks[:-1]-1;X=ret[:,:2];y=ret[:,-1];Gs.append(X.T@X);bs.append(X.T@y);ys.append(y@y)
   vals=[]
   for _ in range(300):
    j=(rng.integers(len(tr),size=int(np.ceil(len(tr)/3)))[:,None]+np.arange(3))%len(tr);j=j.ravel()[:len(tr)];w,_=c.fit_cov(np.sum(np.array(Gs)[j],axis=0)/len(tr),np.sum(np.array(bs)[j],axis=0)/len(tr),float(np.sum(np.array(ys)[j])/len(tr)));vals.append(w)
   r['training_weight_bootstrap']={'interval95':np.quantile(vals,[.025,.975],axis=0).tolist(),'resamples':300,'block_sessions':3}
 p.write_text(json.dumps(output,separators=(',',':'),allow_nan=False))
 print('overnight and day-block uncertainty complete')
if __name__=='__main__':main()
