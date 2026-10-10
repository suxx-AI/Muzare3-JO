import { sendMessage, postJson, checkHealth } from './mazarejoApi.js';
import { transformDashboard, getMarketRows, finite } from './dashboardTransform.js';
const root=document.getElementById('decisionApp');
const state=JSON.parse(document.getElementById('initial-state').textContent);
const $=id=>document.getElementById(id);
const formatter=new Intl.NumberFormat('ar-JO',{maximumFractionDigits:3});
const format=value=>finite(value)===null?'غير متوفر':formatter.format(value);
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const selector=$('planSelector');
selector.value={balanced:'balanced_plan',margin:'highest_margin_plan',water_efficiency:'best_water_efficiency_plan'}[state.setup.goal] || 'balanced_plan';
let busy=false,activityTimer;
function element(tag,className,text) {const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node;}
function empty(parent,text='البيانات غير متوفرة حالياً') {parent.replaceChildren(element('p','empty-state',text));}
function scrollChat() {$('messages').scrollTop=$('messages').scrollHeight;}
function appendMessage(role,text) {
  $('chatWelcome')?.remove();
  const wrapper=element('article',`message message-${role}`);
  wrapper.append(element('div','message-label',role==='user'?'أنت':'مزارع جو'));
  const body=element('div','message-body');
  if(role==='assistant') {
    // Text comes from Gemini; only a sanitized Markdown rendering reaches the DOM.
    body.innerHTML=DOMPurify.sanitize(marked.parse(text.replace(/\\n/g,'\n'),{gfm:true,breaks:true}),{FORBID_TAGS:['img','iframe','style'],FORBID_ATTR:['style']});
    body.querySelectorAll('a').forEach(link=>{link.target='_blank';link.rel='noopener noreferrer';});
  } else body.textContent=text;
  wrapper.append(body);$('messages').append(wrapper);scrollChat();
}
function farmOverview() {
  const entries=[['الموقع',state.farm.location,'location'],['المساحة',`${format(state.farm.land)} دونم`,'leaf'],['ميزانية الموسم',`${format(state.farm.budget)} دينار`,'wallet'],['المياه المتاحة',finite(state.farm.water)===null?'غير محددة':`${format(state.farm.water)} م³`,'water']];
  for(const [label,value,icon] of entries) {
    const card=element('div','farm-stat');
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.classList.add('icon');
    const use=document.createElementNS('http://www.w3.org/2000/svg','use');use.setAttribute('href',`#i-${icon}`);svg.append(use);
    const copy=element('div');copy.append(element('span','muted',label),element('strong','',value));card.append(svg,copy);$('farmOverview').append(card);
  }
}
const numberAnimations=new WeakMap();
function animateNumber(node,value) {
  cancelAnimationFrame(numberAnimations.get(node));
  if(value===null){node.textContent='لم يتم حسابه';node.classList.add('missing-value');delete node.dataset.value;return;}
  node.classList.remove('missing-value');const previous=Number(node.dataset.value);const from=Number.isFinite(previous)?previous:0;node.dataset.value=value;
  if(reduced){node.textContent=format(value);return;}
  const start=performance.now();function frame(now){const progress=Math.min((now-start)/420,1);node.textContent=format(from+(value-from)*(1-(1-progress)**3));if(progress<1)numberAnimations.set(node,requestAnimationFrame(frame));}numberAnimations.set(node,requestAnimationFrame(frame));
}
function chart(id,rows) {
  const box=$(id);box.replaceChildren();if(!rows.length)return empty(box,'بانتظار خطة محسوبة');
  if(id==='allocationChart') {
    const total=rows.reduce((sum,row)=>sum+Math.max(0,row.value),0);
    if(!total)return empty(box,'لا توجد مساحة موزعة');
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 120 120');svg.setAttribute('role','img');svg.setAttribute('aria-label',`توزيع ${format(total)} دونم حسب المحصول`);svg.classList.add('allocation-donut');
    const colors=['#098958','#31be7c','#8bdb93','#60bdb0','#a3ba64','#5b9e7c'];let offset=0;const circumference=2*Math.PI*43;
    const legend=element('div','donut-legend');
    rows.forEach((row,index)=>{const arc=document.createElementNS('http://www.w3.org/2000/svg','circle');for(const [key,value] of Object.entries({cx:60,cy:60,r:43,fill:'none',stroke:colors[index%colors.length],'stroke-width':17,'stroke-dasharray':`${Math.max(0,row.value)/total*circumference} ${circumference}`,'stroke-dashoffset':-offset,transform:'rotate(-90 60 60)'}))arc.setAttribute(key,String(value));offset+=Math.max(0,row.value)/total*circumference;svg.append(arc);const item=element('div');const dot=element('span','legend-dot');dot.style.backgroundColor=colors[index%colors.length];item.append(dot,element('span','',row.crop),element('strong','',format(row.value)));legend.append(item);});
    const center=element('div','donut-center');center.append(element('strong','',format(total)),element('span','','دونم'));const visual=element('div','donut-visual');visual.append(svg,center);box.append(visual,legend);return;
  }
  const max=Math.max(...rows.map(row=>Math.abs(row.value)),1);
  if(id==='productionChart') {
    box.classList.add('column-chart');
    for(const row of rows){const item=element('div','column-item');item.append(element('strong','column-value',format(row.value)));const track=element('div','column-track');const bar=element('div','column-fill');bar.style.height='0%';track.append(bar);item.append(track,element('span','column-label',row.crop));box.append(item);requestAnimationFrame(()=>{bar.style.height=`${Math.max(0,row.value)/max*100}%`;});}return;
  }
  for(const row of rows){const item=element('div','chart-row');const label=element('div','chart-label');label.append(element('span','',row.crop),element('strong','',format(row.value)));const track=element('div','bar-track');const bar=element('div','bar-fill');bar.style.width='0%';track.append(bar);item.append(label,track);box.append(item);requestAnimationFrame(()=>{bar.style.width=`${Math.max(0,row.value)/max*100}%`;});}
}
function crops(rows) {
  const box=$('cropRows');box.replaceChildren();if(!rows.length)return empty(box,'ستظهر المحاصيل من نتيجة أداة التحسين');
  for(const row of rows){const card=element('article','crop-row');const heading=element('div','crop-heading');heading.append(element('span','crop-dot'),element('strong','',row.crop),element('span','crop-area',`${format(row.dunums)} دونم`));const details=element('div','crop-details');for(const [label,value,unit] of [['الإنتاج المتوقع',row.production,'كغ'],['استهلاك المياه',row.water,'م³'],['التكلفة المرجعية',row.cost,'دينار']]){const item=element('div');item.append(element('span','muted',label),element('strong','',value===null?'غير متوفر':`${format(value)} ${unit}`));details.append(item);}card.append(heading,details);box.append(card);}
}
function comparison(data) {
  const box=$('planComparison');box.replaceChildren();if(!data.highest || !data.balanced)return empty(box,'تظهر المقارنة عند توفر الخطتين');
  for(const [label,metrics] of [['الخطة الأعلى هامشاً',data.highest],['الخطة المتوازنة',data.balanced]]){const card=element('div','comparison-card');card.append(element('h4','',label));for(const [title,key,unit] of [['الهامش التقديري','margin','دينار'],['استهلاك المياه','water','م³'],['التكلفة','cost','دينار']]){const row=element('div','comparison-stat');row.append(element('span','muted',title),element('strong','',metrics[key]===null?'غير متوفر':`${format(metrics[key])} ${unit}`));card.append(row);}box.append(card);}
}
function markets(cropNames) {
  const box=$('marketRows');box.replaceChildren();const rows=getMarketRows(cropNames,state.market_data);
  if(!rows.length){const row=element('tr');const cell=element('td','empty-state','تظهر أسعار محاصيل الخطة بعد التحليل');cell.colSpan=4;row.append(cell);box.append(row);}
  for(const item of rows){const row=element('tr');for(const value of [item.crop,format(item.amman),format(item.irbid),item.preferred])row.append(element('td','',value));box.append(row);}
  const dates=[];for(const [key,name] of [['amman','عمّان'],['irbid','إربد']]){const date=state.market_data?.[key]?.report_date;if(typeof date==='string')dates.push(`${name}: ${date}`);} $('marketDates').textContent=dates.length?`تاريخ بيانات السوق · ${dates.join(' · ')}`:'تاريخ البيانات غير متوفر';
}
function weather(rows) {
  const box=$('weatherRows');box.replaceChildren();$('weatherPanel').hidden=!Array.isArray(rows)||!rows.length;
  for(const item of rows || []){if(typeof item?.location!=='string')continue;const row=element('div','weather-row');row.append(element('strong','',item.location));for(const [label,key,unit] of [['الحرارة','temperature_c','°م'],['الرطوبة','humidity_percent','٪'],['الهطول','precipitation_mm','مم']])row.append(element('span','',`${label}: ${format(item[key])}${finite(item[key])===null?'':` ${unit}`}`));box.append(row);}
}
function renderDashboard() {
  const view=transformDashboard(state.dashboard,selector.value);
  $('dashboardNotice').textContent=view.failed?'لم تجد أداة التحسين خطة صالحة لهذه المدخلات. راجع الميزانية والمساحة والمحاصيل.':view.available?'نتيجة فعلية من أداة التحسين · اختر خطة لمقارنتها':'اطلب تحليل خطة ليظهر توزيع المحاصيل والمؤشرات المحسوبة.';
  $('dashboardNotice').classList.toggle('has-plan',view.available);
  for(const node of document.querySelectorAll('[data-metric]'))animateNumber(node,view.metrics[node.dataset.metric]??null);
  chart('allocationChart',view.allocation);chart('waterChart',view.water);chart('productionChart',view.production);crops(view.crops);comparison(view.comparison);markets(view.crops.map(row=>row.crop));
  $('planDetail').textContent=view.evaluated===null?'توزيع محسوب حسب ميزانيتك':`${format(view.evaluated)} خطة تم تقييمها`;
}
function setBusy(value) {
  busy=value;$('sendButton').disabled=value;$('resetChat').disabled=value;$('messageInput').disabled=value;document.querySelectorAll('[data-prompt]').forEach(button=>button.disabled=value);$('chatForm').setAttribute('aria-busy',String(value));$('analysisActivity').hidden=!value;
  clearInterval(activityTimer);const stages=[...document.querySelectorAll('.activity-stages span')];stages.forEach(node=>node.classList.remove('active'));
  if(value){let index=0;stages[0].classList.add('active');activityTimer=setInterval(()=>{stages[index].classList.remove('active');index=(index+1)%stages.length;stages[index].classList.add('active');},1800);scrollChat();}
}
function showError(message){$('chatError').textContent=message;$('chatError').hidden=false;}
$('chatForm').addEventListener('submit',async event=>{
  event.preventDefault();if(busy)return;const question=$('messageInput').value.trim();if(!question)return;
  $('chatError').hidden=true;appendMessage('user',question);$('messageInput').value='';setBusy(true);
  try {const result=await sendMessage(question,root.dataset.chat);appendMessage('assistant',result.answer);if(result.dashboard!==null && result.dashboard!==undefined){state.dashboard=result.dashboard;renderDashboard();}if(Array.isArray(result.weather))weather(result.weather);}
  catch(error){showError(error.message || 'تعذر إكمال التحليل حالياً. حاول مرة أخرى.');$('messageInput').value=question;}
  finally{setBusy(false);$('messageInput').focus();scrollChat();}
});
$('messageInput').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();if(!busy)$('chatForm').requestSubmit();}});
document.querySelectorAll('[data-prompt]').forEach(button=>button.addEventListener('click',()=>{$('messageInput').value=button.dataset.prompt;$('messageInput').focus();}));
$('resetChat').addEventListener('click',async()=>{if(busy)return;$('resetChat').disabled=true;try{await postJson(root.dataset.reset,{});state.dashboard=null;$('messages').replaceChildren();empty($('messages'),'محادثة جديدة. بيانات المزرعة محفوظة؛ ابدأ بسؤالك.');weather([]);renderDashboard();$('chatError').hidden=true;}catch(error){showError(error.message);}finally{$('resetChat').disabled=false;}});
selector.addEventListener('change',renderDashboard);
function syncNavigation(){const target=location.hash || '#chatPanel';document.querySelectorAll('.nav-item').forEach(link=>link.classList.toggle('active',link.hash===target));}
addEventListener('hashchange',syncNavigation);syncNavigation();
farmOverview();for(const message of state.messages || [])if(['user','assistant'].includes(message.role)&&typeof message.text==='string')appendMessage(message.role,message.text);renderDashboard();weather(state.weather);
checkHealth(root.dataset.health).then(ready=>{$('systemStatus').textContent=ready?'الخادم المحلي جاهز':'تعذر الاتصال بالخادم المحلي';document.querySelector('.status-light').classList.toggle('offline',!ready);});
