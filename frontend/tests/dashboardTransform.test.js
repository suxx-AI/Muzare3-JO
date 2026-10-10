import test from 'node:test';
import assert from 'node:assert/strict';
import { transformDashboard } from '../src/utils/dashboardTransform.js';

test('empty, failed, and partial optimizer output remains renderable', () => {
  for (const input of [null, {}, { success: false }, { balanced_plan: {} }]) {
    const view = transformDashboard(input);
    assert.deepEqual(view.allocation, []);
    assert.equal(view.metrics.margin, null);
  }
  assert.equal(transformDashboard({ success: false, balanced_plan: { estimated_margin_jod: 100 } }).status, 'failed');
});

test('preserves zero and handles missing individual crop values', () => {
  const view = transformDashboard({ success: true, balanced_plan: {
    estimated_margin_jod: 0, remaining_budget_jod: 0, total_cost_jod: 100,
    total_water_m3: 50, water_efficiency_jod_per_m3: 0,
    allocation: {
      'بندورة': { dunums: 10, water_m3: 50, expected_production_kg: 150 },
      'خيار': { dunums: 0, expected_production_kg: null },
      invalid: null,
    },
  } });
  assert.equal(view.metrics.margin, 0);
  assert.equal(view.metrics.remaining, 0);
  assert.deepEqual(view.allocation, [{ crop: 'بندورة', value: 10 }, { crop: 'خيار', value: 0 }]);
  assert.deepEqual(view.water, [{ crop: 'بندورة', value: 50 }]);
  assert.deepEqual(view.production, [{ crop: 'بندورة', value: 150 }]);
});

test('selects an explicit plan without guessing or falling back', () => {
  const data = { balanced_plan: { estimated_margin_jod: 100 }, highest_margin_plan: { estimated_margin_jod: 200 } };
  assert.equal(transformDashboard(data).metrics.margin, 100);
  assert.equal(transformDashboard(data, 'highest_margin_plan').metrics.margin, 200);
  assert.equal(transformDashboard(data, 'best_water_efficiency_plan').metrics.margin, null);
});
