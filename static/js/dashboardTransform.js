export const PLAN_OPTIONS = [{key:'balanced_plan',label:'الخطة المتوازنة'},{key:'highest_margin_plan',label:'أعلى هامش تقديري'},{key:'best_water_efficiency_plan',label:'أفضل كفاءة مياه'}];
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
export const finite = value => typeof value === 'number' && Number.isFinite(value) ? value : null;
export function getPlan(data,key='balanced_plan') { return object(data) && data.success !== false && object(data[key]) ? data[key] : null; }
function cropData(plan,field) { return object(plan?.allocation) ? Object.entries(plan.allocation).filter(([,data]) => object(data) && finite(data[field]) !== null).map(([crop,data]) => ({crop,value:data[field]})) : []; }
export const getCropAllocationData = plan => cropData(plan,'dunums');
export const getWaterData = plan => cropData(plan,'water_m3');
export const getProductionData = plan => cropData(plan,'expected_production_kg');
function metrics(plan) { return {margin:finite(plan?.estimated_margin_jod),cost:finite(plan?.total_cost_jod),remaining:finite(plan?.remaining_budget_jod),water:finite(plan?.total_water_m3),efficiency:finite(plan?.water_efficiency_jod_per_m3)}; }
export function transformDashboard(data,key='balanced_plan') {
  const plan=getPlan(data,key);
  return {available:!!plan,failed:data?.success === false,metrics:metrics(plan),allocation:getCropAllocationData(plan),water:getWaterData(plan),production:getProductionData(plan),crops:object(plan?.allocation) ? Object.entries(plan.allocation).filter(([,value]) => object(value)).map(([crop,value]) => ({crop,dunums:finite(value.dunums),water:finite(value.water_m3),production:finite(value.expected_production_kg),cost:finite(value.reference_cost_jod)})) : [],comparison:{highest:getPlan(data,'highest_margin_plan') ? metrics(getPlan(data,'highest_margin_plan')) : null,balanced:getPlan(data,'balanced_plan') ? metrics(getPlan(data,'balanced_plan')) : null},evaluated:finite(data?.plans_evaluated),ignored:Array.isArray(data?.ignored_crops) ? data.ignored_crops.filter(item => typeof item?.crop === 'string').map(item => item.crop) : []};
}
export function getMarketRows(crops,marketData) {
  return crops.map(crop => { const amman=finite(marketData?.amman?.crops?.[crop]?.representative_price_jod_per_kg);const irbid=finite(marketData?.irbid?.crops?.[crop]?.representative_price_jod_per_kg);return {crop,amman,irbid,preferred:amman !== null && irbid !== null ? amman === irbid ? 'متساويان سعرياً' : amman > irbid ? 'عمّان' : 'إربد' : 'غير متوفر للمقارنة'}; });
}
