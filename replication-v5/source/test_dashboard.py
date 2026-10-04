from pathlib import Path
import json,sys
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parent
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
 page=browser.new_page(viewport={'width':1280,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8795',wait_until='networkidle');page.wait_for_function('window.companyResearch?.state!==null',timeout=90000)
 assert page.locator('#company option').count()==20 and page.locator('#model option').count()==29
 for model in ['metals_ewq','market_q','calls_24itm_raw','metals_stale_cap1','adaptive_metals','v4_gold_quarterly']:
  page.select_option('#model',model)
  for period in ['full','confirmation','recent']:
   page.select_option('#period',period)
   for frequency in ['daily','monthly']:
    page.select_option('#frequency',frequency)
    page.wait_for_function('([id,period,f])=>companyResearch.state.id===id&&companyResearch.state.period===period&&companyResearch.state.frequency===f',arg=[model,period,frequency])
    state=page.evaluate('companyResearch.state');assert state['points']==state['metric'][frequency]['n'],state
 for ticker in ['EQX','SSRM','NG','FNV','NEM']:
  page.select_option('#company',ticker);page.wait_for_function('(ticker)=>companyResearch.state.ticker===ticker',arg=ticker)
  assert page.locator('#trials tbody tr').count()==29
 page.select_option('#company','WPM');page.select_option('#model','market_q');page.select_option('#frequency','daily');page.select_option('#period','full');page.select_option('#cost','stress');page.wait_for_function('companyResearch.state.cost==="stress"&&companyResearch.state.period==="full"&&companyResearch.state.ticker==="WPM"')
 assert page.evaluate('companyResearch.state.metric.daily.r2')<page.evaluate('companyResearch.summary.companies.find(c=>c.company.ticker==="WPM").runs.market_q.full.daily.r2')
 page.select_option('#cost','base');page.select_option('#model','metals_ewq');page.wait_for_function('companyResearch.state.id==="metals_ewq"&&companyResearch.state.cost==="base"')
 page.screenshot(path=str(R/'desktop.png'),full_page=True);page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(R/'mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
 assert not errors,errors
 (R/'dashboard-qa.json').write_text(json.dumps({'passed':True,'companies':20,'models':29,'period_frequency_checks':36,'cost_control':True,'mobile_overflow':False,'page_errors':errors},indent=2))
 print('PASS: 29-model controls; 36 period/frequency numeric counts; company selection; costs; mobile and JS checks.')
 browser.close()
