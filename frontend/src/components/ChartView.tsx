import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

interface ChartConfig {
  chart_type: string
  title: string
  labels: string[]
  datasets: { label: string; data: number[] }[]
}

const COLORS = ['#6366f1', '#22d3ee', '#f59e0b', '#10b981', '#f43f5e', '#a78bfa']

// Convert backend chart_config to Recharts-compatible data format
function toRechartsData(config: ChartConfig) {
  return config.labels.map((label, i) => {
    const point: Record<string, string | number> = { name: label }
    config.datasets.forEach(ds => { point[ds.label] = ds.data[i] ?? 0 })
    return point
  })
}

function formatValue(value: number) {
  if (value >= 1_000_000) return `₹${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `₹${(value / 1_000).toFixed(0)}K`
  return `₹${value}`
}

export default function ChartView({ config }: { config: ChartConfig }) {
  const data = toRechartsData(config)
  const type = config.chart_type.toLowerCase()

  const commonProps = { data, margin: { top: 8, right: 16, left: 8, bottom: 4 } }

  const renderChart = () => {
    if (type === 'line') {
      return (
        <LineChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
          <YAxis tickFormatter={formatValue} tick={{ fill: '#94a3b8', fontSize: 11 }} />
          <Tooltip formatter={(v: number) => formatValue(v)} contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
          <Legend />
          {config.datasets.map((ds, i) => (
            <Line key={ds.label} type="monotone" dataKey={ds.label} stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={{ r: 4 }} />
          ))}
        </LineChart>
      )
    }

    if (type === 'pie') {
      const pieData = config.labels.map((label, i) => ({
        name: label,
        value: config.datasets[0]?.data[i] ?? 0,
      }))
      return (
        <PieChart>
          <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={110} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
            {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
          </Pie>
          <Tooltip formatter={(v: number) => formatValue(v)} contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
        </PieChart>
      )
    }

    if (type === 'scatter') {
      const scatterData = config.labels.map((_, i) => ({
        x: i,
        y: config.datasets[0]?.data[i] ?? 0,
        name: config.labels[i],
      }))
      return (
        <ScatterChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="x" tick={{ fill: '#94a3b8', fontSize: 12 }} />
          <YAxis dataKey="y" tickFormatter={formatValue} tick={{ fill: '#94a3b8', fontSize: 11 }} />
          <Tooltip formatter={(v: number) => formatValue(v)} contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
          <Scatter data={scatterData} fill={COLORS[0]} />
        </ScatterChart>
      )
    }

    // Default: bar chart
    return (
      <BarChart {...commonProps}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
        <YAxis tickFormatter={formatValue} tick={{ fill: '#94a3b8', fontSize: 11 }} />
        <Tooltip formatter={(v: number) => formatValue(v)} contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
        <Legend />
        {config.datasets.map((ds, i) => (
          <Bar key={ds.label} dataKey={ds.label} fill={COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} />
        ))}
      </BarChart>
    )
  }

  return (
    <div className="mt-3 bg-slate-800 rounded-xl p-4 border border-slate-700">
      <p className="text-slate-300 text-sm font-medium mb-3">{config.title}</p>
      <ResponsiveContainer width="100%" height={260}>
        {renderChart()}
      </ResponsiveContainer>
    </div>
  )
}
