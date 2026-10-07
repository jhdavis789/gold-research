"""Two isolated numeric workers, unique outputs, one final provenance manifest."""
import run as r
from concurrent.futures import ThreadPoolExecutor,as_completed
import subprocess,json,hashlib,time
def main():
 start=time.monotonic();(r.R/'logs').mkdir(exist_ok=True)
 def worker(stock):
  log=r.R/'logs'/f'{stock}.log'
  with log.open('w') as f:
   process=subprocess.run([r.sys.executable,str(r.R/'run.py'),'--stocks',stock,'--no-manifest'],stdout=f,stderr=subprocess.STDOUT)
  return stock,process.returncode
 results=[]
 with ThreadPoolExecutor(max_workers=2) as pool:
  futures=[pool.submit(worker,z['ticker']) for z in r.c.v5.OLD['universe']]
  for f in as_completed(futures):
   stock,status=f.result();results.append({'stock':stock,'exit_code':status});print(stock,'completed',status,'elapsed_minutes',round((time.monotonic()-start)/60,1),flush=True)
 receipt={'rules':len(r.SPECS)*2,'companies':len(results),'workers':2,'runs':results,'elapsed_seconds':time.monotonic()-start,'provenance':{n:hashlib.sha256((r.R/n).read_bytes()).hexdigest() for n in ['run.py','data.py','cost_training.py','cash_kernel.py','cash.c','DESIGN.md','BASIS-ADDENDUM.md','COST-ADDENDUM.md']},'specs':r.SPECS,'options':r.OPTIONS,'cutoff':'2026-09-30'}
 (r.R/'results/manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
 assert all(z['exit_code']==0 for z in results),results
if __name__=='__main__':main()
