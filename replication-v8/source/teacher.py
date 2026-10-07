"""Frozen-coefficient explanatory translation; no portfolio/wealth claim."""
import run as r
import numpy as np,pandas as pd,json,gzip,hashlib

FAMILIES={'metals_rates':[0,1,2], 'metals_rates_equity':[0,1,2,3],
          'metals_rates_options':[0,1,2]+list(range(4,r.N)),
          'metals_rates_equity_options':list(range(r.N))}

def fit(X,y):
 scale=np.maximum(np.sqrt(np.mean(X*X,axis=0)),1e-8)
 Z=np.column_stack([np.ones(len(X)),X/scale]);penalty=np.r_[0.,np.full(X.shape[1],.01)]
 beta=np.linalg.solve(Z.T@Z/len(Z)+np.diag(penalty),Z.T@y/len(Z))
 pred=Z@beta;criterion=float(np.mean((pred-y)**2)+penalty@(beta*beta))
 return beta,scale,criterion

def main():
 source=r.R.parent/'model_v7/results/original7-pca.json.gz'
 old=json.loads(gzip.decompress(source.read_bytes()));dates=pd.DatetimeIndex(old['dates']).as_unit('ns')
 response=np.array(old['pc1_predictions'])-np.array(old['baseline_predictions'])
 for z in old['decisions']:assert z['target'] not in z['peer_inputs'] and z['cutoff']<z['date']
 rows=[];saved=[];nested_checks=0
 for j,stock in enumerate(old['stocks']):
  d,state=r.load(stock);p=r.bank(d,state,1008,3);ix=d.index.get_indexer(dates);assert np.all(ix>=0)
  X=(p['A']-p['AP'])[ix];y=response[:,j]
  mi=pd.Series(np.arange(len(dates)),index=dates).groupby(dates.to_period('M')).last()
  first=int(next(i for i in mi if i>=504));trades=[first]+[int(i) for i in mi if i>first and dates[i].month%3==0]
  predictions={name:np.zeros(len(y)-first) for name in FAMILIES};decisions=[]
  for n,a in enumerate(trades):
   end=trades[n+1] if n+1<len(trades) else len(y);losses={}
   for name,cols in FAMILIES.items():
    beta,scale,loss=fit(X[a-504:a,cols],y[a-504:a]);losses[name]=loss
    predictions[name][a-first:end-first]=np.column_stack([np.ones(end-a),X[a:end,cols]/scale])@beta
    decisions.append({'family':name,'date':str(dates[a].date()),'cutoff':str(dates[a-1].date()),'training_rows':504,'beta':beta.tolist(),'scale':scale.tolist(),'criterion':loss})
    if n==0:
     shocked=y.copy();shocked[a:]+=3
     bb,ss,ll=fit(X[a-504:a,cols],shocked[a-504:a]);assert np.array_equal(beta,bb) and loss==ll
   assert losses['metals_rates_options']<=losses['metals_rates']+1e-12
   assert losses['metals_rates_equity_options']<=losses['metals_rates_equity']+1e-12
   nested_checks+=2
  for name,pred in predictions.items():
   rows.append({'stock':stock,'family':name,'start':str(dates[first].date()),'end':str(dates[-1].date()),**r.c.stats(pred,y[first:])})
  saved.append({'stock':stock,'dates':[str(t.date()) for t in dates[first:]],'response':y[first:].tolist(),'predictions':{k:v.tolist() for k,v in predictions.items()},'decisions':decisions})
  print(stock,'shared-factor translation',flush=True)
 receipt={'status':'passed','nested_training_checks':nested_checks,'target_exclusion_checked':True,'future_response_shocks_checked':True,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'design_sha256':hashlib.sha256((r.R/'TEACHER-DESIGN.md').read_bytes()).hexdigest(),'engine_sha256':hashlib.sha256(__file__.encode()).hexdigest()}
 receipt['engine_sha256']=hashlib.sha256((r.R/'teacher.py').read_bytes()).hexdigest()
 out={'interpretation':'EXPLANATORY ONLY: contemporaneous market increments; signed unconstrained coordinates; intercept; no paid wealth claim.','statistics':rows,'validation':receipt}
 (r.R/'results/teacher-summary.json').write_text(json.dumps(out,indent=2)+'\n')
 with gzip.open(r.R/'results/teacher-paths.json.gz','wt') as f:json.dump(saved,f,separators=(',',':'))
 print(pd.DataFrame(rows).round(4).to_string(index=False))

if __name__=='__main__':main()
