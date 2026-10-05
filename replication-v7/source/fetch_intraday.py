"""Bounded extension of the registered Yahoo chart source. Raw quotes stay private."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import quote
import json, hashlib, time
import pandas as pd

R=Path(__file__).resolve().parent
DATA=R.parent/'data/v7_intraday_20261004'
STOCKS=['NEM','AEM','B','AU','FNV','WPM','RGLD','GFI','KGC','HMY','EGO','IAG','BTG','OR','DRD','SSRM','CDE','EQX','SA','NG']
SETS={'60m':('2024-10-07','2026-10-01'), '5m':('2026-08-10','2026-10-01')}
def main():
 DATA.mkdir(parents=True,exist_ok=True)
 receipt={'retrieved_at':datetime.now(timezone.utc).isoformat(),'source':'Yahoo chart, revised history','requests':[]}
 for interval,(a,b) in SETS.items():
  for symbol in ['GLD','SLV','SPY']+STOCKS:
   folder=DATA/interval;folder.mkdir(exist_ok=True)
   rawpath=folder/(symbol+'.json')
   url='https://query1.finance.yahoo.com/v8/finance/chart/'+quote(symbol)+'?period1='+str(int(pd.Timestamp(a,tz='UTC').timestamp()))+'&period2='+str(int(pd.Timestamp(b,tz='UTC').timestamp()))+'&interval='+interval+'&includePrePost=false&events=div%2Csplits'
   if rawpath.exists():raw=rawpath.read_bytes();status=200
   else:
    try:
     with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=35) as resp:raw=resp.read();status=resp.status
    except HTTPError as exc:raw=exc.read();status=exc.code
    rawpath.write_bytes(raw)
   item={'symbol':symbol,'interval':interval,'url':url,'http_status':status,'sha256':hashlib.sha256(raw).hexdigest()}
   try:
    z=json.loads(raw);res=z['chart']['result'][0];q=res['indicators']['quote'][0]
    name=res['meta'].get('longName') or res['meta'].get('shortName')
    if symbol=='B':assert 'Barrick' in name, name
    d=pd.DataFrame({'timestamp':pd.to_datetime(res['timestamp'],unit='s',utc=True),**{k:q.get(k) for k in ['open','high','low','close','volume']}})
    d=d.dropna(subset=['open','close']);d=d[(d.open>0)&(d.close>0)]
    d=d[d.timestamp<pd.Timestamp(b,tz='UTC')]
    assert not d.timestamp.duplicated().any()
    d.to_csv(folder/(symbol+'.csv'),index=False)
    item.update(name=name,rows=len(d),start=str(d.timestamp.iloc[0]),end=str(d.timestamp.iloc[-1]))
   except Exception as exc:item['error']=str(exc)
   receipt['requests'].append(item)
   (DATA/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
   print(symbol,interval,item.get('rows',0),item.get('error',''),flush=True)
   time.sleep(.1)
if __name__=='__main__':main()
