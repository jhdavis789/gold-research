'use strict';
let lifecycleData;
const quantile=(a,p)=>{if(!a.length)return NaN;const b=[...a].sort((x,y)=>x-y),j=(b.length-1)*p,k=Math.floor(j);return b[k]+(b[Math.min(k+1,b.length-1)]-b[k])*(j-k);};
function ranks(rows){const sorted=[...rows].sort((a,b)=>a.y-b.y||a.stock.localeCompare(b.stock)),n=rows.length,out=[];if(!n)return out;
 for(const [id,label,f,top] of [['all','All at entry',1,false],['bottom10','Bottom 10% (decile)',.1,false],['bottom25','Bottom 25% (quartile)',.25,false],['top25','Top 25% (quartile)',.25,true],['top10','Top 10% (decile)',.1,true]]){let k=Math.ceil(n*f),group=top?sorted.slice(-k):sorted.slice(0,k);out.push({id,label,n:k,x:mean(group.map(x=>x.x)),y:mean(group.map(x=>x.y)),members:group.map(x=>x.stock)});}const middle=n%2?[sorted[Math.floor(n/2)]]:sorted.slice(n/2-1,n/2+1);out.splice(1,0,{id:'median',label:'Median · middle company/companies',n:middle.length,x:mean(middle.map(p=>p.x)),y:mean(middle.map(p=>p.y)),members:middle.map(p=>p.stock)});return out;
}
function buildBasket(runs,lo,hi,rebalance,fee){
 const dates=[...new Set(runs.flatMap(r=>r.dates.filter(d=>d>=lo&&d<=hi)))].sort();if(dates.length<2)return null;
 const maps=runs.map(r=>new Map(r.dates.map((d,i)=>[d,i]))),marks=runs.map(()=>null),qx=runs.map(()=>0),qy=runs.map(()=>0),entries={},path=[],turnovers=[];let cx=1,cy=1,started=false;
 for(let di=0;di<dates.length;di++){const date=dates[di];for(let j=0;j<runs.length;j++){const k=maps[j].get(date);if(k!==undefined)marks[j]={x:runs[j].portfolio[k],y:runs[j].stock_nav[k]};}
  const eligible=runs.map((r,j)=>j).filter(j=>maps[j].has(date)&&marks[j].x>0&&marks[j].y>0);
  let x=cx+qx.reduce((s,q,j)=>s+q*(marks[j]?.x||0),0),y=cy+qy.reduce((s,q,j)=>s+q*(marks[j]?.y||0),0);
  const atMonthEnd=di+1<dates.length&&date.slice(0,7)!==dates[di+1].slice(0,7),trade=eligible.length&&(!started||(rebalance==='monthly'&&atMonthEnd&&di<dates.length-1));
  // Mark before a close rebalance. Its fee is paid by the account and appears in the next return.
  if(!started&&eligible.length){path.push({date,x:1,y:1,n:eligible.length});started=true;}else if(started)path.push({date,x,y,n:qx.filter(q=>q!==0).length});
  if(trade){let tx=0,ty=0,dx=eligible.length?x/eligible.length:0,dy=eligible.length?y/eligible.length:0;
   for(let j=0;j<runs.length;j++){const on=eligible.includes(j),vx=on?dx:0,vy=on?dy:0;tx+=Math.abs(vx-qx[j]*(marks[j]?.x||0));ty+=Math.abs(vy-qy[j]*(marks[j]?.y||0));qx[j]=on?vx/marks[j].x:0;qy[j]=on?vy/marks[j].y:0;if(on&&!entries[runs[j].stock])entries[runs[j].stock]=date;}
   // Reduce all target dollars to fund costs, preventing borrowing or external cash.
   const fx=1-fee*tx/x,fy=1-fee*ty/y;qx.forEach((q,j)=>qx[j]*=fx);qy.forEach((q,j)=>qy[j]*=fy);cx=0;cy=0;turnovers.push({date,tx,ty});
  }
 }
 if(path.length<2)return null;let last=path[path.length-1];last.x*=1-fee;last.y*=1-fee;
 let years=(Date.parse(last.date)-Date.parse(path[0].date))/86400000/365.25,points=path.slice(1).map((p,i)=>({x:p.x/path[i].x-1,y:p.y/path[i].y-1}));
 return {path,entries,turnovers,start:path[0].date,end:last.date,years,x:last.x-1,y:last.y-1,xcagr:last.x**(1/years)-1,ycagr:last.y**(1/years)-1,stats:stats(points)};
}
function basketWealth(result){const c=$('basketwealth'),box=c.getBoundingClientRect(),w=box.width,h=box.height,ratio=devicePixelRatio||1;c.width=w*ratio;c.height=h*ratio;const ctx=c.getContext('2d');ctx.scale(ratio,ratio);ctx.clearRect(0,0,w,h);ctx.font='12px system-ui';if(!result){ctx.fillText('Choose eligible companies and dates.',24,40);return;}
 const path=result.path,max=Math.max(...path.flatMap(p=>[p.x,p.y]))*1.05,X=i=>60+i/(path.length-1)*(w-80),Y=v=>h-45-v/max*(h-80);
 ctx.fillStyle='#496479';for(let j=0;j<=4;j++){const v=max*j/4;ctx.fillText('$'+(100*v).toFixed(0),4,Y(v)+4);ctx.strokeStyle='#e2e9ed';ctx.beginPath();ctx.moveTo(60,Y(v));ctx.lineTo(w-20,Y(v));ctx.stroke();}
 for(const [key,color] of [['y','#005f9e'],['x','#b8860b']]){ctx.strokeStyle=color;ctx.lineWidth=2;ctx.beginPath();path.forEach((p,i)=>i?ctx.lineTo(X(i),Y(p[key])):ctx.moveTo(X(i),Y(p[key])));ctx.stroke();}
 ctx.fillStyle='#00294b';ctx.fillText(result.start,60,h-15);ctx.textAlign='right';ctx.fillText(result.end,w-20,h-15);ctx.textAlign='left';ctx.fillText('Value of $100 · blue: stock basket · gold: matched replica basket',60,18);
}
function updateBaskets(){if(!D||!$('basketstats'))return;const runs=D.runs.filter(r=>r.model===$('model').value&&visible.has(r.stock)),fee=+$('basketcost').value/10000,lo=$('start').value,hi=$('end').value;
 const result=buildBasket(runs,lo,hi,$('rebalance').value,fee);basketWealth(result);
 if(result){table('basketstats',['Account','Total return','CAGR','Ending $100','Daily tracking R²'],[['Company basket',pct(result.y),pct(result.ycagr),'$'+(100*(1+result.y)).toFixed(2),'—'],['Matched replica basket',pct(result.x),pct(result.xcagr),'$'+(100*(1+result.x)).toFixed(2),dec(result.stats?.tracking)]]);
 $('basketnote').textContent=`${result.start} → ${result.end}. ${Object.keys(result.entries).length} distinct companies entered. ${result.turnovers.length} allocations, including initial entry. ${$('rebalance').value==='monthly'?'Equal weights reset at month-end; newly eligible names join then.':'Equal dollars at entry; quantities then drift, with no later entrants.'} Extra basket trading cost: ${$('basketcost').value} bp each dollar bought or sold, including entry/exit. Internal replica costs remain embedded.`;
 $('basketmembers').textContent=Object.entries(result.entries).map(([s,d])=>`${s}: ${d}`).join(' · ');
 }else{table('basketstats',['Result'],[['No eligible basket for these dates.']]);$('basketnote').textContent='';$('basketmembers').textContent='';}
 // Fixed entry cross-section uses initial eligible names, independently of the dynamic basket setting.
 let endpoint=[];if(result){for(const r of runs){let a=r.dates.indexOf(result.start),b=r.dates.indexOf(result.end);if(a>=0&&b>a)endpoint.push({stock:r.stock,x:r.portfolio[b]/r.portfolio[a]-1,y:r.stock_nav[b]/r.stock_nav[a]-1});}}
 const grouped=ranks(endpoint),transform=v=>$('measure').value==='cagr'&&result?(1+v)**(1/result.years)-1:v;
 table('distribution',['Realized rank group','Names','Company '+($('measure').value==='cagr'?'CAGR':'total'),'Same-name replica','Members'],grouped.map(g=>[g.label,g.n,pct(transform(g.y)),pct(transform(g.x)),g.members.join(', ')]));
 table('percentiles',['Percentile threshold','Company '+($('measure').value==='cagr'?'CAGR':'total')],[10,25,50,75,90].map(q=>['P'+q+(q===50?' · median':''),pct(transform(quantile(endpoint.map(p=>p.y),q/100)))]));
 const byWindow=new Map();for(const p of holding){let k=p.start+'|'+p.end;if(!byWindow.has(k))byWindow.set(k,[]);byWindow.get(k).push(p);}
 const basketPoints=[];const chosen=$('rankgroup').value;for(const [key,ps] of byWindow){
  // Reverse the display annualization before averaging equally funded terminal wealth.
  const exponent=$('measure').value==='cagr'?+$('horizon').value/12:1,raw=ps.map(p=>({...p,x:(1+p.x)**exponent-1,y:(1+p.y)**exponent-1})),g=ranks(raw).find(g=>g.id===chosen);if(!g)continue;
  const [start,end]=key.split('|'),exp=1/exponent;basketPoints.push({stock:g.label,start,end,x:(1+g.x)**exp-1,y:(1+g.y)**exp-1,n:g.n});colors[g.label]='#005f9e';
 }draw('basketscatter',basketPoints,'Matched replica basket · '+($('measure').value==='cagr'?'annualized':'total')+' return');
 $('basketscattercount').textContent=`${basketPoints.length} rolling cohorts. Equal dollars at each window’s start; ${chosen==='all'?'all eligible selected names':'realized company returns determine ranks after the window ends (hindsight)'}. Costs inside original paths only; the extra basket cost and rebalance controls above apply to the ownership account, not this diagnostic.`;
 window.goldExplorer.baskets={result,endpoint,grouped,basketPoints};updateLifecycle();
}
function updateLifecycle(){if(!lifecycleData||!D||!window.goldExplorer)return;const year=+$('cohortyear').value,rows=lifecycleData.cohorts.filter(c=>c.year===year),model=$('model').value,labels={survivors:'Original surviving sample',acquired:'+ five acquired companies',failed_zero:'+ Great Basin · zero recovery',failed_last_quote:'+ Great Basin · last quote scenario'};
 table('lifecyclecohorts',['Fixed entry cohort','Names','Company total','Company CAGR','Replica CAGR','Daily tracking R²','P50 total','Bottom 10% total','Top 10% total'],rows.map(r=>[labels[r.scenario],r.n,pct(r.total),pct(r.cagr),pct(r.models[model]?.cagr),dec(r.models[model]?.daily_tracking_r2),pct(r.percentiles['50']),pct(r.groups.bottom10.total),pct(r.groups.top10.total)]));
 $('lifecyclenote').textContent=rows.length?`${rows[0].start} → ${rows[0].end}. Fixed initial equal weights; names unavailable or already acquired at entry are excluded. This supplemental study uses its own full sample and the year selector; company checkboxes and top date/holding-period controls do not change it. ${rows[0].models[model]?'Replica uses the x-axis technique selected above.':'Replica columns are available for unlevered gold and the two daily-calibrated techniques only.'}`:'';
 $('lifemembers').textContent=rows.length?rows.map(r=>labels[r.scenario]+': '+r.members.join(', ')).join('\n'):'';
 window.goldExplorer.lifecycle={year,rows};
}
async function initBaskets(){for(const id of ['rebalance','basketcost','rankgroup'])$(id).onchange=updateBaskets;$('cohortyear').onchange=updateLifecycle;
 $('downloadbasket').onclick=()=>{const b=window.goldExplorer.baskets?.result;if(!b)return;const a=document.createElement('a'),u=URL.createObjectURL(new Blob([['date,company_nav,replica_nav,positions',...b.path.map(p=>[p.date,p.y,p.x,p.n].join(','))].join('\n')],{type:'text/csv'}));a.href=u;a.download='gold-selected-basket.csv';a.click();URL.revokeObjectURL(u);};
 try{let r=await fetch('lifecycle-summary.json');if(!r.ok)throw Error('Lifecycle study unavailable');lifecycleData=await r.json();for(const y of [...new Set(lifecycleData.cohorts.map(c=>c.year))])$('cohortyear').add(new Option(y,y));$('cohortyear').value='2012';table('lifecyclecompanies',['Company','Outcome date','Treatment / evidence','Model eligibility'],lifecycleData.companies.map(c=>[`${c.ticker} · ${c.name}`,c.exit,`<a href="${c.source}">${c.status}</a>: ${c.terms}`,c.start]));updateLifecycle();}catch(e){$('lifecyclenote').textContent=e.message;console.error(e);}if(D)updateBaskets();
}
window.basketMath={quantile,ranks,buildBasket};initBaskets();
