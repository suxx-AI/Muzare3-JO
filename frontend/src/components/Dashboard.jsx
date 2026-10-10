import { useState } from 'react';
import { PLAN_OPTIONS, transformDashboard } from '../utils/dashboardTransform.js';
import BarChart from './BarChart.jsx';

const formatter = new Intl.NumberFormat('ar-JO', { maximumFractionDigits: 3 });
const metrics = [
  { key: 'margin', label: 'الهامش المالي التقديري', unit: 'دينار أردني', symbol: '↗', featured: true },
  { key: 'water', label: 'إجمالي استهلاك المياه', unit: 'م³', symbol: '≈' },
  { key: 'cost', label: 'التكلفة المرجعية الإجمالية', unit: 'دينار أردني', symbol: '▤' },
  { key: 'remaining', label: 'الميزانية المتبقية', unit: 'دينار أردني', symbol: '◷' },
  { key: 'efficiency', label: 'كفاءة المياه', unit: 'دينار / م³', symbol: '◇' },
];

export default function Dashboard({ dashboard }) {
  const [planKey, setPlanKey] = useState('balanced_plan');
  const view = transformDashboard(dashboard, planKey);
  return <section className="dashboard-column"><div className="dashboard-heading"><div><span className="eyebrow">نظرة على الاستثمار</span><h2>لوحة القرار الزراعي</h2></div><span className={`data-status ${view.available ? 'ready' : ''}`}><i />{view.available ? 'بيانات الخطة' : 'بانتظار خطة'}</span></div><div className="plan-selection"><label htmlFor="plan">الخطة المعروضة</label><select id="plan" value={planKey} onChange={(event) => setPlanKey(event.target.value)}>{PLAN_OPTIONS.map((option) => <option value={option.key} key={option.key}>{option.label}</option>)}</select><span>اختيار العرض مستقل عن توصية المحادثة</span></div><div className="metrics-grid">{metrics.map((metric) => <article className={`panel metric-card ${metric.featured ? 'featured' : ''}`} key={metric.key}><div className="metric-top"><span>{metric.label}</span><span className="metric-symbol" aria-hidden="true">{metric.symbol}</span></div><strong className="metric-value">{view.metrics[metric.key] === null ? '—' : formatter.format(view.metrics[metric.key])}</strong><span className="metric-unit">{metric.unit}</span></article>)}</div>{view.status === 'failed' && <div className="dashboard-notice" role="status">لم يُنتج المحسّن خطة قابلة للعرض. راجع رد ميزان لمعرفة السبب.</div>}{view.status === 'empty' && <div className="dashboard-notice">ستظهر المؤشرات بعد أن ينتج المحسّن خطة. البيانات غير المتاحة تظهر بعلامة —.</div>}<div className="charts-grid"><BarChart title="توزيع المحاصيل" unit="دونم" data={view.allocation} index={1} /><BarChart title="المياه حسب المحصول" unit="م³" data={view.water} index={2} /><BarChart title="الإنتاج المتوقع" unit="كغ" data={view.production} index={3} /></div><div className="dashboard-footnote"><span className="note-symbol">ⓘ</span><p>الهامش تقدير تخطيطي يستند إلى التكاليف المرجعية والأسعار المتاحة، وليس ضماناً للعائد. {view.plansEvaluated !== null && `تم تقييم ${formatter.format(view.plansEvaluated)} خطة ضمن الميزانية.`}</p></div>{view.ignoredCrops.length > 0 && <p className="ignored-crops">محاصيل مستبعدة من التحسين: {view.ignoredCrops.join('، ')}</p>}</section>;
}
