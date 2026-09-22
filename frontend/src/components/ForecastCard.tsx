import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer,
} from 'recharts'
import type { ForecastResponse, AnomalyItem } from '../api/forecast'

function formatRevenue(v: number) {
  if (v >= 1_000_000) return `₹${(v / 1_000_000).toFixed(2)}M`
  if (v >= 1_000) return `₹${(v / 1_000).toFixed(0)}K`
  return `₹${v}`
}

function TrendBadge({ trend }: { trend: string }) {
  const map: Record<string, string> = {
    upward: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    downward: 'bg-red-500/20 text-red-400 border-red-500/30',
    stable: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  }
  const icon = trend === 'upward' ? '↑' : trend === 'downward' ? '↓' : '→'
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${map[trend] ?? map.stable}`}>
      {icon} {trend}
    </span>
  )
}

function AnomalyRow({ item }: { item: AnomalyItem }) {
  const isAbove = item.type === 'above_average'
  const severityColor = item.severity === 'high' ? 'text-red-400' : 'text-yellow-400'
  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
      <div>
        <span className="text-slate-200 text-sm font-medium">{item.label}</span>
        <span className={`ml-2 text-xs ${severityColor}`}>● {item.severity}</span>
      </div>
      <div className="text-right">
        <p className="text-slate-300 text-sm">{formatRevenue(item.revenue)}</p>
        <p className={`text-xs ${isAbove ? 'text-emerald-400' : 'text-red-400'}`}>
          {isAbove ? '+' : ''}{item.deviation_pct}% vs avg
        </p>
      </div>
    </div>
  )
}

export default function ForecastCard({ data }: { data: ForecastResponse }) {
  const { forecast, anomalies, smart_recommendation } = data

  // Build chart data — historical + one predicted point
  const chartData = [
    ...forecast.historical.map(h => ({
      month: h.month,
      revenue: h.total_revenue,
      predicted: null as number | null,
    })),
    {
      month: 'Next Month',
      revenue: null as number | null,
      predicted: forecast.predicted_revenue,
    },
  ]

  return (
    <div className="space-y-4">

      {/* ── Summary cards ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Predicted Revenue', value: formatRevenue(forecast.predicted_revenue) },
          { label: 'Growth Rate', value: `${forecast.growth_rate}%` },
          { label: 'Trend', value: <TrendBadge trend={forecast.trend} /> },
          { label: 'Based On', value: `${forecast.based_on_months} months` },
        ].map(({ label, value }) => (
          <div key={label} className="bg-slate-800 rounded-xl p-3 border border-slate-700">
            <p className="text-slate-400 text-xs mb-1">{label}</p>
            <p className="text-slate-100 text-sm font-semibold">{value}</p>
          </div>
        ))}
      </div>

      {/* ── Revenue trend chart ── */}
      <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
        <p className="text-slate-300 text-sm font-medium mb-3">Revenue Trend + Prediction</p>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={chartData} margin={{ top: 8, right: 16, left: 8, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis tickFormatter={formatRevenue} tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip formatter={(v: number) => formatRevenue(v)} contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
            <ReferenceLine x="Next Month" stroke="#6366f1" strokeDasharray="4 4" label={{ value: 'Forecast', fill: '#818cf8', fontSize: 11 }} />
            <Line type="monotone" dataKey="revenue" stroke="#22d3ee" strokeWidth={2} dot={{ r: 4 }} connectNulls={false} name="Actual" />
            <Line type="monotone" dataKey="predicted" stroke="#6366f1" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 5 }} connectNulls={false} name="Predicted" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* ── Anomalies ── */}
      {anomalies.total_anomalies > 0 && (
        <div className="grid md:grid-cols-2 gap-3">
          {anomalies.region_anomalies.length > 0 && (
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <p className="text-slate-300 text-sm font-medium mb-2">⚠️ Region Anomalies</p>
              {anomalies.region_anomalies.map(a => <AnomalyRow key={a.label} item={a} />)}
            </div>
          )}
          {anomalies.product_anomalies.length > 0 && (
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <p className="text-slate-300 text-sm font-medium mb-2">⚠️ Product Anomalies</p>
              {anomalies.product_anomalies.map(a => <AnomalyRow key={a.label} item={a} />)}
            </div>
          )}
        </div>
      )}

      {/* ── Smart Recommendation ── */}
      <div className="bg-slate-800 rounded-xl p-4 border border-emerald-800/40">
        <p className="text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-2">💡 Smart Recommendation</p>
        <div className="prose text-sm whitespace-pre-wrap text-slate-300">{smart_recommendation}</div>
      </div>

    </div>
  )
}
