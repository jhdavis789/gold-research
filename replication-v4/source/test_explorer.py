from pathlib import Path
import json,gzip,sys,numpy as np
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parent
with gzip.open(R/'public/daily-data.json.gz','rt') as f:d=json.load(f)
assert len(d['universe'])==20 and len(d['runs'])==140
summary={(r['stock'],r['model']):r for r in json.loads((R/'statistics.json').read_text())}
for r in d['runs']:
 x=np.array(r['portfolio']);y=np.array(r['stock_nav']);ix=r['monthends'];assert len(x)==len(y)==len(r['dates']) and np.all(x>0) and len(ix)>12
 assert len(set(r['dates']))==len(x) and sorted(r['dates'])==r['dates']
 daily=x[1:]/x[:-1]-1
 for a,b in zip(ix[:-1],ix[1:]):assert abs(np.prod(1+daily[a:b])-x[b]/x[a])<1e-10
 for freq,ind in [('daily',np.arange(len(x))),('monthly',ix)]:
  a=x[ind];b=y[ind];xx=np.diff(a)/a[:-1];yy=np.diff(b)/b[:-1]
  if freq=='daily':
   valid=np.diff(np.array(r['dates'],dtype='datetime64[D]')).astype(int)<=4;xx=xx[valid];yy=yy[valid]
  expected=1-np.sum((yy-xx)**2)/np.sum((yy-yy.mean())**2)
  assert abs(expected-summary[(r['stock'],r['model'])][freq]['tracking_r2'])<1e-7
assert all(s['start']<=s['end'] for s in d['universe'])
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
 page=b.new_page(viewport={'width':1280,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8794',wait_until='networkidle');page.wait_for_function('window.goldExplorer!==undefined',timeout=120000)
 assert page.locator('#stocks input').count()==20
 assert page.locator('#model option').count()==7
 page.click('#none');assert len(page.evaluate('goldExplorer.state.holding'))==0
 page.locator('[data-stock="WPM"]').check()
 for model in d['models']:
  page.select_option('#model',model['id'])
  for frequency in ['daily','monthly']:
   page.select_option('#frequency',frequency)
   r=page.evaluate('goldExplorer.state.statistics[0]');ref=summary[('WPM',model['id'])][frequency]
   assert abs(r['tracking']-ref['tracking_r2'])<1e-7,(model,frequency,r,ref)
   assert abs(r['r2']-ref['regression_r2'])<1e-7
 for h in ['1','12','36','60','120']:
  page.select_option('#horizon',h);assert page.evaluate('goldExplorer.state.holding.length')>0
 page.select_option('#measure','total');page.select_option('#fits','on');page.click('#added');assert page.locator('#stocks input:checked').count()==6
 page.click('#streamers');assert page.locator('#stocks input:checked').count()==4
 page.click('#all');assert page.locator('#stocks input:checked').count()==20
 page.fill('#start','2025-01-01');page.locator('#start').dispatch_event('change');assert page.evaluate('goldExplorer.state.holding.length')==0
 page.fill('#start','2009-01-01');page.locator('#start').dispatch_event('change');page.select_option('#horizon','60');page.select_option('#frequency','daily');page.select_option('#measure','cagr');page.select_option('#fits','off')
 page.screenshot(path=str(R/'desktop.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(R/'mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
 assert not errors,errors
 (R/'qa.json').write_text(json.dumps({'passed':True,'companies':20,'techniques':7,'daily_monthly_statistics_checked':140,'all_controls_checked':True,'mobile_overflow':False,'console_errors':errors},indent=2))
 print('PASS: 140 path/accounting/statistic checks, 14 live WPM frequency/method comparisons, all controls, mobile overflow, no JS errors.')
 b.close()
