const tools = [
  { name: 'الطقس', symbol: '☀' },
  { name: 'بيانات السوق', symbol: '↗' },
  { name: 'موارد المحاصيل', symbol: '≋' },
  { name: 'محسّن الخطط', symbol: '◇' },
];

export default function AgentActivity({ loading }) {
  return <aside className="panel activity-panel"><div className="activity-heading"><h3>أدوات اتخاذ القرار</h3><span>عرض توضيحي</span></div><div className="activity-tools">{tools.map((tool) => <div className="activity-tool" key={tool.name}><span className="tool-symbol" aria-hidden="true">{tool.symbol}</span><span>{tool.name}</span></div>)}</div><p>{loading ? 'الطلب قيد المعالجة. حالة كل أداة غير متاحة في هذا العرض.' : 'الأدوات المتاحة للوكيل · هذا العرض لا يتتبع تشغيلها الفعلي.'}</p></aside>;
}
