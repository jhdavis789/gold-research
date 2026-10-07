"""Past-only volatility targeting; same paid cash ledger, no tracking fit."""
import run as r
import numpy as np,pandas as pd,json,gzip,hashlib
def main():
 out=[]
 for comp in r.c.v5.OLD['universe']:
  stock=comp['ticker'];d,state=r.load(stock);first=max(1008,int(d.index.searchsorted(pd.Timestamp(comp['start']))));mi=d.groupby(d.index.to_period('M')).tail(1).index;first=int(d.index.get_indexer(mi[mi>=d.index[first]])[0])
  y=d[stock].to_numpy()[first:];y=y/y[0];y[1:]*=.9998;y[-1]*=.9998;sy=d[stock].to_numpy()[first:];sy=sy/sy[0];sy[1:]*=.999;sy[-1]*=.999
  rr=d[[stock,'GLD','BIL']].pct_change();runs=[]
  for h in [1,3]:
   p=r.bank(d,state,first,h);weights={};decisions=[]
   for i in r.c.trade_dates(d,first,h):
    sample=rr.iloc[i-252:i];target=(sample[stock]-sample.BIL).std(ddof=1);gold=(sample.GLD-sample.BIL).std(ddof=1);unbounded=float(target/gold);w=np.zeros(r.N);w[0]=np.clip(unbounded,0,3);weights[i]=w
    decisions.append({'date':str(d.index[i].date()),'cutoff':str(d.index[i-1].date()),'weights':w.tolist(),'past_stock_excess_vol':float(target*np.sqrt(252)),'past_gold_excess_vol':float(gold*np.sqrt(252)),'uncapped_gold_weight':unbounded,'gold_cap_binding':bool(unbounded>3)})
   nav,ledger,settlements=r.replay(p,weights);stress,_,_=r.replay(p,weights,.001,.1)
   runs.append({'id':'volatility_gold'+('_m' if h==1 else '_q'),'h':h,'nav':nav.tolist(),'metrics':r.metrics(d.index[first:],nav,y),'stress':r.metrics(d.index[first:],stress,sy),'decisions':decisions,'ledger':ledger,'settlements':settlements})
  out.append({'company':comp,'dates':[str(t.date()) for t in d.index[first:]],'stock_nav':y.tolist(),'runs':runs});print(stock,'risk control',flush=True)
 with gzip.open(r.R/'results/risk-controls.json.gz','wt') as f:json.dump(out,f,separators=(',',':'),allow_nan=False)
 (r.R/'risk-control-receipt.json').write_text(json.dumps({'source_hashes':{n:hashlib.sha256((r.R/n).read_bytes()).hexdigest() for n in ['risk_control.py','RISK-CONTROL-DESIGN.md','run.py','data.py','cost_training.py']},'companies':len(out),'accounts':len(out)*2},indent=2)+'\n')
if __name__=='__main__':main()
