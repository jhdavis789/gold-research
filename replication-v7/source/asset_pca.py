"""PCA coordinates mapped back to permitted tradable fund positions."""
import common as c
import numpy as np,pandas as pd,json
from scipy.optimize import minimize,LinearConstraint
ASSETS=c.v5.ASSETS
def estimate(d,stock,i,k):
 cc=d.pct_change();ix=np.arange(i-756,i);ix=ix[ix>0];rf=cc.BIL.to_numpy()[ix];X=cc[ASSETS].to_numpy()[ix]-rf[:,None];y=cc[stock].to_numpy()[ix]-rf
 valid=np.diff(d.index.asi8)[ix-1]/86400e9<=4;X=X[valid];y=y[valid];ix=ix[valid];sw=2.**(-(i-1-ix)/126);sw/=sw.sum();sd=np.sqrt(np.sum(sw[:,None]*X[:,1:]**2,axis=0));Z=X[:,1:]/sd
 C=np.einsum('ni,n,nj->ij',Z,sw,Z);e,U=np.linalg.eigh(C);U=U[:,np.argsort(e)[::-1]][:,:k];physical=U/sd[:,None];physical/=np.linalg.norm(physical,axis=0)
 B=np.zeros((7,k+1));B[0,0]=1;B[1:,1:]=physical
 yy=float(np.sum(sw*y*y));G=np.einsum('ni,n,nj->ij',X,sw,X)+np.diag(np.r_[0,np.ones(6)*.01*yy]);b=np.einsum('ni,n,n->i',X,sw,y);H=B.T@G@B;cross=B.T@b;scale=max(yy,1e-12)
 # Auxiliary t >= abs(physical weights) makes the gross cap a linear constraint.
 dims=k+1;mapping=np.column_stack([B,np.zeros((7,7))]);lo=np.array([0,0,0,-.5,-.5,-.5,-.5]);hi=np.array([3,1.5,1,.5,.5,.5,.5]);a=np.zeros(dims+7);a[0]=np.clip(b[0]/G[0,0],0,3);a[dims:]=np.abs(B@a[:dims]);base=a.copy()
 A=np.vstack([mapping,np.column_stack([-B,np.eye(7)]),np.column_stack([B,np.eye(7)]),np.r_[np.zeros(dims),np.ones(7)][None,:]])
 lower=np.r_[lo,np.zeros(14),0];upper=np.r_[hi,np.full(14,np.inf),5]
 objective=lambda t:float((t[:dims]@H@t[:dims]-2*cross@t[:dims])/scale)
 def jac(t):return np.r_[2*(H@t[:dims]-cross)/scale,np.zeros(7)]
 opt=minimize(objective,a,jac=jac,constraints=LinearConstraint(A,lower,upper),method='SLSQP',options={'ftol':1e-11,'maxiter':1000})
 valid=bool(np.all(A@opt.x>=lower-1e-7) and np.all(A@opt.x<=upper+1e-7) and np.isfinite(opt.fun))
 a=opt.x if valid and objective(opt.x)<=objective(base)+1e-10 else base;w=B@a[:dims]
 return w,{'cutoff':str(d.index[i-1].date()),'components':k,'optimizer_success':bool(opt.success),'fallback':bool(np.array_equal(a,base)),'gold_embedding_ok':objective(a)<=objective(base)+1e-10,'gross':float(abs(w).sum()),'retained_covariance_share':float(np.sort(e)[::-1][:k].sum()/e.sum()),'pca_physical_map':B.tolist()}
def main():
 output=[]
 for comp in c.v5.OLD['universe']:
  stock=comp['ticker'];d=pd.DataFrame({k:c.ohlc(k).close for k in ASSETS+[stock,'BIL']}).dropna();first=int(d.index.get_loc(pd.Timestamp(comp['start'])));runs=[]
  p={'d':d,'price':d[ASSETS].to_numpy(),'cash':d.BIL.to_numpy(),'dt':np.r_[0,np.diff(d.index.asi8)/86400e9/365.25],'first':first}
  y=d[stock].to_numpy()[first:];y=y/y[0];y[1:]*=.9998;y[-1]*=.9998
  for k in [2,4,6]:
   weights={};decisions=[]
   for i in c.trade_dates(d,first,3):
    w,info=estimate(d,stock,i,k);weights[i]=w;decisions.append({'date':str(d.index[i].date()),'weights':w.tolist(),**info})
   spec={'id':f'asset_pca{k}','funds':7,'option':None};nav,info=c.v5.simulate(p,spec,weights);stress,_=c.v5.simulate(p,spec,weights,cost=.001)
   # Stress both owned and replicated accounts at the same ten-basis-point rate.
   sy=d[stock].to_numpy()[first:];sy=sy/sy[0];sy[1:]*=.999;sy[-1]*=.999
   runs.append({'id':spec['id'],'metrics':c.metrics(d.index[first:],nav,y),'stress':c.metrics(d.index[first:],stress,sy),'nav':nav.tolist(),'decisions':decisions,**info})
  c.save(stock+'-asset-pca.json.gz',{'company':comp,'dates':[str(t.date()) for t in d.index[first:]],'stock_nav':y.tolist(),'runs':runs});output.append({'company':comp,'runs':[{k:v for k,v in r.items() if k not in ['nav','decisions']} for r in runs]});print(stock,'asset PCA',flush=True)
 (c.R/'results/asset-pca-summary.json').write_text(json.dumps(output,separators=(',',':'),allow_nan=False))
if __name__=='__main__':main()
