"""Long-history exposure estimation from daytime/overnight versus daily returns."""
import common as c
import numpy as np,pandas as pd,json
SPECS=[('daily126',126,63),('daily504',504,None),('daily_ew',756,126),('daytime',126,63),('overnight',126,63),('realized',126,63),('blend',126,63)]
def estimate(d,stock,rule,nf,i):
 name,window,half=rule;cc,day,night=c.returns(d);end=i-1;ix=np.arange(max(1,end-window+1),end+1)
 ix=ix[np.diff(d.index.asi8)[ix-1]/86400e9<=4];sw=np.ones(len(ix)) if half is None else 2.**(-(end-ix)/half);sw/=sw.sum()
 def pair(r,mix):return (r[c.FUNDS].to_numpy()[ix],r[stock].to_numpy()[ix],mix)
 sets=[pair(cc,1)] if name.startswith('daily') else ([pair(day,1)] if name=='daytime' else ([pair(night,1)] if name=='overnight' else ([pair(day,1),pair(night,1)] if name=='realized' else [pair(cc,.5),pair(day,.5),pair(night,.5)])))
 w,info=c.gram_fit(sets,sw,nf);info.update(cutoff=str(d.index[end].date()),observations=len(ix))
 return w,info
def main():
 rows=[];summary=[]
 for comp in c.v5.OLD['universe']:
  stock=comp['ticker'];d=c.panel(stock);first=int(d.index.searchsorted(comp['start']));assert first>=756
  # Cache session returns once; estimation wrapper still accepts standalone data for audits.
  cc,day,night=c.returns(d);arrays={k:(r[c.FUNDS].to_numpy(),r[stock].to_numpy()) for k,r in [('cc',cc),('day',day),('night',night)]}
  runs=[]
  for name,window,half in SPECS:
   for nf in [2,3]:
    weights={};decisions=[]
    for i in c.trade_dates(d,first,3):
     end=i-1;ix=np.arange(max(1,end-window+1),end+1);ix=ix[np.diff(d.index.asi8)[ix-1]/86400e9<=4]
     sw=np.ones(len(ix)) if half is None else 2.**(-(end-ix)/half);sw/=sw.sum()
     keys=[('cc',1)] if name.startswith('daily') else ([('day',1)] if name=='daytime' else ([('night',1)] if name=='overnight' else ([('day',1),('night',1)] if name=='realized' else [('cc',.5),('day',.5),('night',.5)])))
     sets=[(arrays[k][0][ix],arrays[k][1][ix],mix) for k,mix in keys]
     w,info=c.gram_fit(sets,sw,nf);weights[i]=w;decisions.append({'date':str(d.index[i].date()),'cutoff':str(d.index[end].date()),'weights':w.tolist(),'observations':len(ix),**info})
    nav,y,ledger=c.account(d,stock,weights,nf);stress,sy,_=c.account(d,stock,weights,nf,.001);dates=d.index[first:];mid=name+('_metals' if nf==2 else '_market')
    met=c.metrics(dates,nav,y);run={'id':mid,'metrics':met,'stress':c.metrics(dates,stress,sy),'nav':nav.tolist(),'decisions':decisions,'ledger':ledger}
    runs.append(run);rows.append({'stock':stock,'model':mid,'daily_r2':met['daily']['r2'],'monthly_r2':met['monthly']['r2'],'portfolio_cagr':met['portfolio_cagr'],'stock_cagr':met['stock_cagr']})
  ccx=cc.iloc[first+1:];dy=day.iloc[first+1:];ni=night.iloc[first+1:];valid=np.diff(d.index[first:].asi8)/86400e9<=4
  attributed={}
  for label,r in [('close_to_close',ccx),('daytime',dy),('overnight',ni)]:
   x=r[c.FUNDS].to_numpy()[valid];z=r[stock].to_numpy()[valid];w,_=c.gram_fit([(x,z,1)],np.ones(len(z))/len(z),3);attributed[label]={'gold':float(w[0]),'silver':float(w[1]),'market':float(w[2]),**c.stats(x@w,z),'target_sum_squares':float(np.sum(z*z))}
  c.save(stock+'-sessions.json.gz',{'company':comp,'dates':[str(t.date()) for t in dates],'stock_nav':y.tolist(),'runs':runs,'full_sample_diagnostic':attributed})
  summary.append({'company':comp,'runs':[{k:v for k,v in a.items() if k not in ['nav','decisions','ledger']} for a in runs],'sessions':attributed})
  print(stock,'sessions',flush=True)
 pd.DataFrame(rows).to_csv(c.R/'results/session-summary.csv',index=False);(c.R/'results/session-summary.json').write_text(json.dumps(summary,separators=(',',':'),allow_nan=False))
if __name__=='__main__':main()
