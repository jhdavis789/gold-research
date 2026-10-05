"""Leave-target-out PCA of residual company moves; explanatory, never invested."""
import common as c
import numpy as np,pandas as pd,json
def ols(X,Y):
 gram=np.einsum('ni,nj->ij',X,X);cross=np.einsum('ni,nk->ik',X,Y)
 return np.linalg.solve(gram+np.eye(X.shape[1])*1e-12,cross)
def main():
 output=[]
 for label,stocks in [('original14',c.STOCKS[:14]),('original7',c.STOCKS[:7])]:
  close=pd.DataFrame({k:c.ohlc(k).close for k in c.FUNDS+stocks+['BIL']}).dropna();rr=close.pct_change().dropna()
  gaps=np.diff(close.index.asi8)/86400e9;rr=rr.iloc[np.flatnonzero(gaps<=4)]
  Y=rr[stocks].to_numpy()-rr.BIL.to_numpy()[:,None];X=np.column_stack([np.ones(len(rr)),rr[c.FUNDS].to_numpy()-rr.BIL.to_numpy()[:,None]])
  mi=rr.groupby(rr.index.to_period('M')).tail(1).index;first=int(rr.index.get_loc(next(t for t in mi if rr.index.get_loc(t)>=504)))
  trades=[first]+[int(i) for i in rr.index.get_indexer(mi) if first<i<len(rr) and rr.index[i].month%3==0]
  base=np.zeros((len(rr)-first,len(stocks)));pc1=base.copy();pc3=base.copy();ledgers=[]
  for a,z in enumerate(trades):
   end=trades[a+1] if a+1<len(trades) else len(rr);tr=slice(z-504,z);test=slice(z,end)
   B=ols(X[tr],Y[tr]);rt=Y[tr]-X[tr]@B;rf=Y[test]-X[test]@B;base[z-first:end-first]=X[test]@B
   for j,stock in enumerate(stocks):
    peers=[k for k in range(len(stocks)) if k!=j];std=np.std(rt[:,peers],axis=0,ddof=1);Z=rt[:,peers]/std;cov=Z.T@Z/len(Z);eig,U=np.linalg.eigh(cov);order=np.argsort(eig)[::-1];U=U[:,order];eig=eig[order]
    # Stable sign convention for display; fitted product is sign invariant.
    for k in range(U.shape[1]):
     if U[np.argmax(abs(U[:,k])),k]<0:U[:,k]*=-1
    for k,target in [(1,pc1),(3,pc3)]:
     scores=Z@U[:,:k];beta=ols(scores,rt[:,j,None]);testscore=(rf[:,peers]/std)@U[:,:k];prediction=base[z-first:end-first,j]+(testscore@beta).ravel();target[z-first:end-first,j]=prediction
    ledgers.append({'target':stock,'date':str(rr.index[z].date()),'cutoff':str(rr.index[z-1].date()),'peer_inputs':[stocks[k] for k in peers],'train_rows':504,'first_pc_share':float(eig[0]/eig.sum()),'three_pc_share':float(eig[:3].sum()/eig.sum()),'first_pc_loadings':{stocks[p]:float(U[t,0]) for t,p in enumerate(peers)},'factor_coefficients':B[:,j].tolist()})
  actual=Y[first:];dates=rr.index[first:];rows=[]
  for j,stock in enumerate(stocks):
   rows.append({'stock':stock,'baseline':c.stats(base[:,j],actual[:,j]),'one_peer_pc':c.stats(pc1[:,j],actual[:,j]),'three_peer_pcs':c.stats(pc3[:,j],actual[:,j]),'residual_sse_reduction_pc1':float(1-np.sum((pc1[:,j]-actual[:,j])**2)/np.sum((base[:,j]-actual[:,j])**2)),'residual_sse_reduction_pc3':float(1-np.sum((pc3[:,j]-actual[:,j])**2)/np.sum((base[:,j]-actual[:,j])**2))})
  c.save(label+'-pca.json.gz',{'stocks':stocks,'dates':[str(t.date()) for t in dates],'actual_excess_returns':actual.tolist(),'baseline_predictions':base.tolist(),'pc1_predictions':pc1.tolist(),'pc3_predictions':pc3.tolist(),'decisions':ledgers,'statistics':rows})
  output.append({'panel':label,'stock_count':len(stocks),'start':str(dates[0].date()),'end':str(dates[-1].date()),'sessions':len(dates),'statistics':rows,'mean_baseline_r2':float(np.mean([r['baseline']['tracking_r2'] for r in rows])),'mean_pc1_r2':float(np.mean([r['one_peer_pc']['tracking_r2'] for r in rows])),'mean_pc3_r2':float(np.mean([r['three_peer_pcs']['tracking_r2'] for r in rows]))})
  print(label,output[-1]['start'],output[-1]['mean_baseline_r2'],output[-1]['mean_pc1_r2'],output[-1]['mean_pc3_r2'],flush=True)
 (c.R/'results/pca-summary.json').write_text(json.dumps(output,separators=(',',':'),allow_nan=False))
if __name__=='__main__':main()
