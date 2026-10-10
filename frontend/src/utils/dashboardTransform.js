// These names come from optimize_farm_plan in tools.py. No inferred metrics.
export const PLAN_OPTIONS = [
  { key: 'balanced_plan', label: 'الخطة المتوازنة' },
  { key: 'highest_margin_plan', label: 'أعلى هامش تقديري' },
  { key: 'best_water_efficiency_plan', label: 'أفضل كفاءة مياه' },
];

const isObject = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
const numberOrNull = (value) => typeof value === 'number' && Number.isFinite(value) ? value : null;

export function getPlan(dashboard, planKey = 'balanced_plan') {
  return isObject(dashboard) && dashboard.success !== false && isObject(dashboard[planKey])
    ? dashboard[planKey] : null;
}

function cropData(plan, field) {
  if (!isObject(plan?.allocation)) return [];
  return Object.entries(plan.allocation)
    .filter(([, data]) => isObject(data) && numberOrNull(data[field]) !== null)
    .map(([crop, data]) => ({ crop, value: data[field] }));
}

export const getCropAllocationData = (plan) => cropData(plan, 'dunums');
export const getWaterData = (plan) => cropData(plan, 'water_m3');
export const getProductionData = (plan) => cropData(plan, 'expected_production_kg');

export function transformDashboard(dashboard, planKey = 'balanced_plan') {
  const plan = getPlan(dashboard, planKey);
  return {
    available: plan !== null,
    status: dashboard?.success === false ? 'failed' : plan ? 'ready' : 'empty',
    metrics: {
      margin: numberOrNull(plan?.estimated_margin_jod),
      water: numberOrNull(plan?.total_water_m3),
      cost: numberOrNull(plan?.total_cost_jod),
      remaining: numberOrNull(plan?.remaining_budget_jod),
      efficiency: numberOrNull(plan?.water_efficiency_jod_per_m3),
    },
    allocation: getCropAllocationData(plan),
    water: getWaterData(plan),
    production: getProductionData(plan),
    plansEvaluated: numberOrNull(dashboard?.plans_evaluated),
    ignoredCrops: Array.isArray(dashboard?.ignored_crops)
      ? dashboard.ignored_crops.filter((item) => typeof item?.crop === 'string').map((item) => item.crop)
      : [],
  };
}
