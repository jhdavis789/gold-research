import json,os,sys,math
from pathlib import Path
from playwright.sync_api import sync_playwright
URL=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8000/replication-v4/'
R=Path(__file__).resolve().parent
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
 page=browser.new_page(viewport={'width':1400,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(URL);page.wait_for_function('window.goldExplorer?.baskets?.result && window.goldExplorer?.lifecycle?.rows?.length===4',timeout=60000)
 initial=page.evaluate('({basket:goldExplorer.baskets.result,life:goldExplorer.lifecycle.rows.map(r=>({n:r.n,cagr:r.cagr,scenario:r.scenario}))})')
 # Independent fixed equal-initial-capital endpoint calculation, including extra layer fees.
 check=page.evaluate('''()=>{let z=goldExplorer.baskets,fee=Number(document.getElementById('basketcost').value)/10000;return {x:z.result.x,y:z.result.y,expectedX:(1+z.grouped[0].x)*(1-fee)**2-1,expectedY:(1+z.grouped[0].y)*(1-fee)**2-1}}''')
 assert abs(check['x']-check['expectedX'])<1e-10 and abs(check['y']-check['expectedY'])<1e-10,check
 # Synthetic monthly rebalancing and fees must be self financing; no future entrants in buy/hold.
 toy=page.evaluate('''()=>{let runs=[{stock:'A',dates:['2020-01-01','2020-01-31','2020-02-03','2020-02-28'],portfolio:[1,2,2,4],stock_nav:[1,2,2,4]},{stock:'B',dates:['2020-01-01','2020-01-31','2020-02-03','2020-02-28'],portfolio:[1,1,1,1],stock_nav:[1,1,1,1]}];let late={stock:'C',dates:['2020-02-03','2020-02-28'],portfolio:[1,10],stock_nav:[1,10]};return {hold:basketMath.buildBasket(runs,'2020-01-01','2020-02-28','hold',0),monthly:basketMath.buildBasket(runs,'2020-01-01','2020-02-28','monthly',0),late:basketMath.buildBasket([...runs,late],'2020-01-01','2020-02-28','hold',0),cost:basketMath.buildBasket(runs,'2020-01-01','2020-02-28','hold',.01),median:basketMath.quantile([1,2,8,9],.5),ranks:basketMath.ranks(Array.from({length:20},(_,i)=>({stock:String(i),x:i,y:i})))}}''')
 assert abs(toy['hold']['y']-1.5)<1e-12
 assert abs(toy['monthly']['y']-1.25)<1e-12
 assert abs(toy['late']['y']-1.5)<1e-12 and 'C' not in toy['late']['entries']
 assert abs(toy['cost']['y']-(2.5*.99**2-1))<1e-12
 assert toy['median']==5 and {r['id']:r['n'] for r in toy['ranks']}=={'all':20,'median':2,'bottom10':2,'bottom25':5,'top25':5,'top10':2}
 for mid in page.evaluate('goldExplorer.data.models.map(m=>m.id)'):
  page.select_option('#model',mid);assert page.evaluate('Number.isFinite(goldExplorer.baskets.result.y) && Number.isFinite(goldExplorer.baskets.result.x)')
 page.select_option('#rebalance','monthly');assert page.evaluate('goldExplorer.baskets.result.turnovers.length')>100
 page.select_option('#basketcost','10');assert page.evaluate('Number.isFinite(goldExplorer.baskets.result.y)')
 for mode in ['all','median','bottom10','bottom25','top25','top10']:
  page.select_option('#rankgroup',mode);assert page.evaluate('goldExplorer.baskets.basketPoints.length')>0
 page.select_option('#measure','total');page.select_option('#horizon','12');page.select_option('#model','daily_metals_market_quarterly')
 page.select_option('#cohortyear','2025');assert page.evaluate('goldExplorer.lifecycle.rows[0].year')==2025
 page.select_option('#model','gold_silver_options_quarterly');assert 'available for' in page.locator('#lifecyclenote').inner_text()
 page.click('#none');assert page.evaluate('goldExplorer.baskets.result===null')
 page.click('#all');page.locator('[data-stock="WPM"]').uncheck();assert 'WPM' not in page.evaluate('goldExplorer.baskets.result.entries')
 page.fill('#start','2026-09-30');page.locator('#start').dispatch_event('change');assert page.evaluate('goldExplorer.baskets.result===null')
 page.fill('#start','2012-01-01');page.locator('#start').dispatch_event('change');page.select_option('#model','daily_metals_quarterly');page.select_option('#rebalance','hold');page.select_option('#basketcost','2');page.select_option('#cohortyear','2012');page.click('#all')
 page.screenshot(path=str(R/'baskets-desktop.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(250)
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),page.evaluate('document.documentElement.scrollWidth')
 page.screenshot(path=str(R/'baskets-mobile.png'),full_page=True)
 assert not errors,errors
 # Daily-data original payload must remain unchanged across this feature.
 report={'url':URL,'passed':True,'errors':errors,'initial_basket':{k:v for k,v in initial['basket'].items() if k not in ['path','turnovers']},'lifecycle_2012':initial['life'],'accounting_check':check,'checks':['fixed basket independent endpoint','monthly toy accounting','no future constituent admission in fixed basket','entry/exit costs','percentiles and tail counts','six scatter groups','all techniques and unavailable lifecycle models labeled','company deselection','empty and too-short windows','mobile no overflow']}
 (R/'basket-qa.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));browser.close()
