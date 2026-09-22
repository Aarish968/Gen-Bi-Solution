import type { ChatMessage } from '../hooks/useChat'
import ChartView from './ChartView'
import InsightCard from './InsightCard'

interface Props {
  message: ChatMessage
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-xl bg-indigo-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm">
          {message.text}
        </div>
      </div>
    )
  }

  // Loading state
  if (message.isLoading) {
    return (
      <div className="flex items-start gap-3">
        <div className="shrink-0 w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center text-sm">✦</div>
        <div className="bg-slate-800 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2">
          <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:0ms]" />
          <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:150ms]" />
          <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:300ms]" />
        </div>
      </div>
    )
  }

  // Error state
  if (message.error) {
    return (
      <div className="flex items-start gap-3">
        <div className="shrink-0 w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center text-sm">✦</div>
        <div className="bg-red-900/30 border border-red-700/40 rounded-2xl rounded-tl-sm px-4 py-3 text-sm text-red-300">
          ⚠️ {message.error}
        </div>
      </div>
    )
  }

  // Upload confirmation (simple text — no chart/insight)
  if (!message.data) {
    return (
      <div className="flex items-start gap-3">
        <div className="shrink-0 w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center text-sm">✦</div>
        <div className="bg-slate-800 rounded-2xl rounded-tl-sm px-4 py-3 text-sm text-slate-300 max-w-xl">
          {message.text}
        </div>
      </div>
    )
  }

  // Full AI response — insight + chart + recommendation
  const { data } = message
  return (
    <div className="flex items-start gap-3">
      <div className="shrink-0 w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center text-sm">✦</div>
      <div className="flex-1 min-w-0">
        {/* Chart */}
        {data.chart_config?.labels?.length > 0 && (
          <ChartView config={data.chart_config} />
        )}
        {/* Insight + Recommendation + SQL + Plan */}
        <InsightCard
          insight={data.insight}
          recommendation={data.recommendation}
          sql={data.sql}
          plan={data.plan}
        />
      </div>
    </div>
  )
}
