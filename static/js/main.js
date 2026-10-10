import { postJson } from './mazarejoApi.js';
const root = document.getElementById('setupApp');
const server = JSON.parse(document.getElementById('saved-setup').textContent);
const error = document.getElementById('setupError');
let draft = {};
try { draft = JSON.parse(localStorage.getItem('mazarejo-draft') || '{}'); } catch { /* Invalid local draft: use saved server state. */ }
if (!draft || typeof draft !== 'object') draft = {};
if (draft.boot_id !== server.boot_id) {
  draft = {};
  try { localStorage.removeItem('mazarejo-draft'); } catch {}
}
const state = {boot_id:server.boot_id, farm: {...(server.farm || {}), ...(draft.farm || {})}, setup: {...(server.setup || {}), ...(draft.setup || {})}};
const labels = {balanced:'خطة متوازنة',margin:'أعلى هامش مالي تقديري',water_efficiency:'أفضل كفاءة مياه'};
const number = new Intl.NumberFormat('ar-JO', {maximumFractionDigits:2});
function save() { try { localStorage.setItem('mazarejo-draft', JSON.stringify(state)); } catch {} }
function showError(text) { error.textContent = text; error.hidden = false; }
function farmIsValid() { return state.farm.location && Number.isFinite(state.farm.land) && state.farm.land > 0 && state.farm.land % 10 === 0 && Number.isFinite(state.farm.budget) && state.farm.budget > 0 && (state.farm.water == null || (Number.isFinite(state.farm.water) && state.farm.water >= 0)); }

const farmForm = document.getElementById('farmForm');
if (farmForm) {
  for (const key of ['land','water','budget']) if (Number.isFinite(state.farm[key])) document.getElementById(key).value = state.farm[key];
  if (state.farm.location) document.getElementById('farmLocation').value = state.farm.location;
  farmForm.addEventListener('submit', event => {
    event.preventDefault();
    state.farm = {location:document.getElementById('farmLocation').value};
    for (const key of ['land','budget']) state.farm[key] = Number(document.getElementById(key).value);
    const water = document.getElementById('water').value.trim();
    state.farm.water = water === '' ? null : Number(water);
    if (!farmIsValid()) return showError('أدخل معلومات صالحة. المساحة يجب أن تكون من مضاعفات ١٠ دونم.');
    save(); location.href = root.dataset.crops;
  });
}
const cropsForm = document.getElementById('cropsForm');
if (cropsForm) {
  const goal = document.querySelector(`input[name="goal"][value="${['balanced','margin','water_efficiency'].includes(state.setup.goal) ? state.setup.goal : 'balanced'}"]`);
  goal.checked = true;
  document.querySelectorAll('input[name="crop"]').forEach(input => { input.checked = Array.isArray(state.setup.crops) && state.setup.crops.includes(input.value); });
  cropsForm.addEventListener('submit', event => {
    event.preventDefault();
    state.setup = {goal:document.querySelector('input[name="goal"]:checked').value, crops:[...document.querySelectorAll('input[name="crop"]:checked')].map(input => input.value)};
    save(); location.href = root.dataset.ready;
  });
}
const summary = document.getElementById('setupSummary');
if (summary) {
  const entries = [['الموقع',state.farm.location],['المساحة',Number.isFinite(state.farm.land) ? number.format(state.farm.land)+' دونم' : 'لم تدخل بعد'],['الميزانية',Number.isFinite(state.farm.budget) ? number.format(state.farm.budget)+' دينار' : 'لم تدخل بعد'],['المياه المتاحة',Number.isFinite(state.farm.water) ? number.format(state.farm.water)+' م³' : 'غير محددة · سيُحسب احتياج الخطة'],['الهدف',labels[state.setup.goal] || labels.balanced],['المحاصيل',Array.isArray(state.setup.crops) && state.setup.crops.length ? state.setup.crops.join('، ') : 'مقارنة المحاصيل المتاحة']];
  for (const [label,value] of entries) { const row=document.createElement('div'); const title=document.createElement('span');title.textContent=label;const detail=document.createElement('strong');detail.textContent=value || 'لم يدخل بعد';row.append(title,detail);summary.append(row); }
  document.getElementById('startButton').addEventListener('click', async event => {
    if (!farmIsValid()) return showError('أكمل معلومات المزرعة أولاً من الخطوة الأولى.');
    state.setup.goal ||= 'balanced'; state.setup.crops ||= [];
    const button=event.currentTarget;button.disabled=true;button.textContent='جارٍ تجهيز مساحة القرار…';
    try { await postJson(root.dataset.start,state); try { localStorage.removeItem('mazarejo-draft'); } catch {} location.href=root.dataset.home; }
    catch(failure) { showError(failure.message);button.disabled=false;button.textContent='ابدأ مع مزارع جو'; }
  });
}
