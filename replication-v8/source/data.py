"""Scoped snapshot adapters; avoid generic 'run' module import collisions."""
from pathlib import Path
import importlib.util,json
import numpy as np,pandas as pd
R=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('gold_v8_legacy_v5',R.parent/'model_v5/run.py');v5=importlib.util.module_from_spec(spec);spec.loader.exec_module(v5)
CACHE={}
def ohlc(key):
 if key not in CACHE:
  folders=['v5_costs_20261004','v4_history_20261004','snapshot_20261003','expanded_20261003','v3_history_20261003']
  path=next(R.parent/'data'/f/(key+'.json') for f in folders if (R.parent/'data'/f/(key+'.json')).exists())
  a=json.loads(path.read_text())['chart']['result'][0];q=a['indicators']['quote'][0]
  close=np.array(q['close'],dtype=float);op=np.array(q['open'],dtype=float);adj=np.array(a['indicators']['adjclose'][0]['adjclose'],dtype=float)
  index=pd.to_datetime(a['timestamp'],unit='s',utc=True).tz_localize(None).normalize().as_unit('ns')
  d=pd.DataFrame({'open':op*adj/close,'close':adj},index=index).loc[:'2026-09-30'];d=d.replace([np.inf,-np.inf],np.nan).dropna();d=d[(d>0).all(axis=1)]
  assert not d.index.duplicated().any();CACHE[key]=d
 return CACHE[key]
def trade_dates(d,first,h):
 mi=d.groupby(d.index.to_period('M')).tail(1).index
 return [first]+[int(i) for i in d.index.get_indexer(mi) if first<i<len(d)-1 and (h==1 or d.index[i].month%3==0)]
def metrics(dates,x,y):return v5.metrics(pd.DatetimeIndex(dates).as_unit('ns'),x,y)
def stats(x,y):
 return {'n':len(y),'tracking_r2':float(1-np.sum((y-x)**2)/np.sum((y-y.mean())**2)),'regression_r2':float(np.corrcoef(x,y)[0,1]**2),'rmse':float(np.sqrt(np.mean((y-x)**2)))}
