interface Props {
  insight: string
  recommendation: string
  sql: string
  plan: string[]
}

export default function InsightCard({ insight, recommendation, sql, plan }: Props) {
  return (
    <div className="mt-3 space-y-3">

      {/* Insight */}
      <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
        <p className="text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-2">📊 Insight</p>
        <div className="prose text-sm whitespace-pre-wrap text-slate-300">{insight}</div>
      </div>

      {/* Recommendation */}
      {recommendation && (
        <div className="bg-slate-800 rounded-xl p-4 border border-emerald-800/40">
          <p className="text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-2">💡 Recommendation</p>
          <div className="prose text-sm whitespace-pre-wrap text-slate-300">{recommendation}</div>
        </div>
      )}

      {/* SQL — collapsible */}
      {sql && (
        <details className="bg-slate-800 rounded-xl border border-slate-700">
          <summary className="px-4 py-2.5 text-slate-400 text-xs font-semibold uppercase tracking-wider cursor-pointer select-none hover:text-slate-200">
            🗄 Generated SQL
          </summary>
          <pre className="px-4 pb-3 text-xs text-cyan-300 overflow-x-auto">{sql}</pre>
        </details>
      )}

      {/* Plan — collapsible */}
      {plan.length > 0 && (
        <details className="bg-slate-800 rounded-xl border border-slate-700">
          <summary className="px-4 py-2.5 text-slate-400 text-xs font-semibold uppercase tracking-wider cursor-pointer select-none hover:text-slate-200">
            🗂 Agent Plan
          </summary>
          <ol className="px-4 pb-3 space-y-1">
            {plan.map((step, i) => (
              <li key={i} className="text-xs text-slate-400">{step}</li>
            ))}
          </ol>
        </details>
      )}

    </div>
  )
}
