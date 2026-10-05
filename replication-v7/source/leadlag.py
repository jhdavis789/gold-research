"""Lag-aware hourly beta estimates, used only in slow-trading portfolios."""
import common as c,intraday as intr
import numpy as np,pandas as pd,json
def estimate(stock,rows,d,nf,date,blend=False):
 train=[s for s in rows if s['date']<date][-126:];assert len(train)==126
 X=[];Y=[];W=[]
 dw=2.**(-np.arange(125,-1,-1)/63);dw/=dw.sum()
 for wt,s in zip(dw,train):
  marks=np.vstack([s['open'],s['close']]);r=marks[1:]/marks[:-1]-1
  X.extend(np.column_stack([r[:-2,:nf],r[1:-1,:nf],r[2:,:nf]]));Y.extend(r[1:-1,-1]);W.extend([wt]*5)
 X=np.array(X);Y=np.array(Y);W=np.array(W);yy=float(np.sum(W*Y*Y));G=np.einsum('ni,n,nj->ij',X,W,X)+np.eye(X.shape[1])*.01*yy;b=np.einsum('ni,n,n->i',X,W,Y)
 coef=np.linalg.solve(G,b);summed=coef.reshape(3,nf).sum(axis=0);w=np.clip(summed,[0]*nf,[3,1.5,1][:nf]);info={'cutoff':str(train[-1]['date'].date()),'raw_summed_weights':summed.tolist(),'lag_current_lead_coefficients':coef.reshape(3,nf).tolist(),'complete_days':126}
 if blend:
  daily,_=intr.estimate(d,stock,rows,'daily',nf,date);w=.5*w+.5*daily
 return w,info
def main():
 output=[]
 for comp in c.v5.OLD['universe']:
  stock=comp['ticker'];d=c.panel(stock);rows,_=intr.sessions(stock,'60m');rows=[s for s in rows if s['date'] in d.index]
  saved=json.loads(__import__('gzip').decompress((c.R/'results'/f'{stock}-hourly.json.gz').read_bytes()));first=int(d.index.get_loc(pd.Timestamp(saved['dates'][0])));runs=[]
  for blend in [False,True]:
   for nf in [2,3]:
    for h in [1,3]:
     decisions=[];weights={}
     for i in c.trade_dates(d,first,h):
      w,info=estimate(stock,rows,d,nf,d.index[i],blend);weights[i]=w;decisions.append({'date':str(d.index[i].date()),'weights':w.tolist(),**info})
     nav,y,ledger=c.account(d,stock,weights,nf);stress,sy,_=c.account(d,stock,weights,nf,.001);mid=('leadlag_blend' if blend else 'leadlag')+('_metals' if nf==2 else '_market')+('_m' if h==1 else '_q')
     runs.append({'id':mid,'metrics':c.metrics(d.index[first:],nav,y),'stress':c.metrics(d.index[first:],stress,sy),'nav':nav.tolist(),'decisions':decisions,'ledger':ledger})
  c.save(stock+'-leadlag.json.gz',{'company':comp,'dates':saved['dates'],'stock_nav':y.tolist(),'runs':runs});output.append({'company':comp,'runs':[{k:v for k,v in r.items() if k not in ['nav','decisions','ledger']} for r in runs]});print(stock,'leadlag',flush=True)
 (c.R/'results/leadlag-summary.json').write_text(json.dumps(output,separators=(',',':'),allow_nan=False))
if __name__=='__main__':main()
