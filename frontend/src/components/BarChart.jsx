const formatter = new Intl.NumberFormat('ar-JO', { maximumFractionDigits: 2 });
const colors = ['#74cda5', '#81afbe', '#c2b980', '#8f9fd0', '#b093b9'];

export default function BarChart({ title, unit, data, index }) {
  const max = Math.max(0, ...data.map((row) => row.value));
  return <section className="panel chart-panel"><div className="chart-heading"><div><span className="chart-index">0{index}</span><h3>{title}</h3></div><span className="unit">{unit}</span></div>{data.length ? <div className="bar-chart" role="img" aria-label={`${title}: ${data.map((row) => `${row.crop} ${formatter.format(row.value)} ${unit}`).join('، ')}`}>{data.map((row, i) => <div className="bar-row" key={row.crop}><div className="bar-label"><span>{row.crop}</span><strong>{formatter.format(row.value)}</strong></div><div className="bar-track"><div className="bar-fill" style={{ width: `${max > 0 ? Math.max(0, row.value / max * 100) : 0}%`, background: colors[i % colors.length] }} /></div></div>)}</div> : <div className="chart-empty"><div className="chart-placeholder" aria-hidden="true"><i /><i /><i /><i /></div><p>بانتظار بيانات الخطة</p></div>}</section>;
}
