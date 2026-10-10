import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
const source=await readFile(new URL('../static/js/dashboardTransform.js',import.meta.url),'utf8');
const transform=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
test('missing metrics remain missing, explicit plan selection, and valid zero stays zero',()=>{
  const data={balanced_plan:{estimated_margin_jod:0,total_cost_jod:12,allocation:{'ثوم':{dunums:20,water_m3:0,expected_production_kg:2000}}}};
  const view=transform.transformDashboard(data);
  assert.equal(view.metrics.margin,0);assert.equal(view.metrics.water,null);assert.equal(view.metrics.efficiency,null);
  assert.deepEqual(view.water,[{crop:'ثوم',value:0}]);assert.equal(view.allocation[0].value,20);
  assert.equal(transform.transformDashboard(data,'highest_margin_plan').available,false);
  assert.equal(transform.transformDashboard({success:false,...data}).available,false);
  assert.equal(transform.transformDashboard(null).available,false);
  assert.equal(transform.finite(NaN),null);assert.equal(transform.finite('3'),null);
});
test('real market fields, equal prices, and missing prices are handled without fabrication',()=>{
  const data={amman:{crops:{'بندورة':{representative_price_jod_per_kg:.15},'خيار':{representative_price_jod_per_kg:0}}},irbid:{crops:{'بندورة':{representative_price_jod_per_kg:.15}}}};
  const rows=transform.getMarketRows(['بندورة','خيار','ثوم'],data);
  assert.equal(rows[0].preferred,'متساويان سعرياً');assert.equal(rows[1].amman,0);assert.equal(rows[1].irbid,null);assert.equal(rows[2].amman,null);
});
