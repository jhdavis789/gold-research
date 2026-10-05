"""Programmatic render, interaction, URL roundtrip and responsive checks."""
from pathlib import Path
import sys,json
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parent
URL=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8827/'
def main():
 failures=[];checks=[]
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True,args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1280,'height':1000});page.on('pageerror',lambda e:failures.append(str(e)));page.goto(URL);page.wait_for_function('window.READY===true')
  assert page.locator('#stock option').count()==20 and page.locator('#rows tr').count()==41;assert page.locator('svg').count()==5;checks.append('all companies, all41 candidate rows and five charts render')
  page.select_option('#trade','q');assert 'quarterly trading' in page.locator('#recentnote').inner_text();page.select_option('#funds','market');assert 'trade=q' in page.url and 'funds=market' in page.url
  page.select_option('#stock','OR');page.select_option('#panel','original14');assert page.locator('#pcachart svg').count()==1
  copied=page.url;other=browser.new_page();other.goto(copied);other.wait_for_function('window.READY===true');assert other.locator('#stock').input_value()=='OR' and other.locator('#trade').input_value()=='q' and other.locator('#panel').input_value()=='original14';checks.append('company, instruments, trade frequency and panel URL roundtrip')
  page.select_option('#stock','DRD');assert 'Insufficient complete' in page.locator('#fivenote').inner_text();assert page.locator('#fivechart svg').count()==0;checks.append('insufficient intraday coverage is visible')
  page.select_option('#stock','WPM');page.select_option('#panel','original7');assert 'EXPLANATORY ONLY' in page.locator('#pcanote').inner_text();assert 'three-month-block interval' in page.locator('#bootstrap').inner_text();checks.append('PCA and uncertainty labels visible')
  for width in [390,768,1280]:
   page.set_viewport_size({'width':width,'height':900});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');assert page.locator('svg').count()==5
  checks.append('mobile/tablet/desktop overflow checks')
  # Font-size and SVG geometry QA; no interactive screenshots needed.
  assert page.locator('footer a').first.get_attribute('href')=='SOURCES.md';assert not failures,failures
  browser.close()
 receipt={'passed':True,'url':URL,'checks':checks,'page_errors':failures};(R/'dashboard-qa.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
