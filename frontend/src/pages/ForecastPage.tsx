import { useForecast } from '../hooks/useForecast'
import ForecastCard from '../components/ForecastCard'

export default function ForecastPage() {
  const {
    data, isLoading, error,
    months, threshold,
    setMonths, setThreshold,
    fetchForecast,
  } = useForecast()

  return (
    <div className="h-full overflow-y-auto px-4 py-6">
      <div className="max-w-4xl mx-auto space-y-5">

        {/* ── Header ── */}
        <div>
          <h1 className="text-slate-100 font-semibold text-lg">📈 Forecast & Anomaly Detection</h1>
          <p className="text-slate-400 text-sm mt-0.5">
            Predict next month revenue and detect unusual patterns in your sales data
          </p>
        </div>

        {/* ── Controls ── */}
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 flex flex-wrap gap-6 items-end">

          {/* Months slider */}
          <div className="flex-1 min-w-40">
            <label className="text-slate-400 text-xs font-medium block mb-1">
              Historical Months: <span className="text-slate-200">{months}</span>
            </label>
            <input
              type="range"
              min={1} max={12} step={1}
              value={months}
              onChange={e => setMonths(Number(e.target.value))}
              className="w-full accent-indigo-500"
            />
            <div className="flex justify-between text-slate-500 text-xs mt-0.5">
              <span>1</span><span>12</span>
            </div>
          </div>

          {/* Threshold slider */}
          <div className="flex-1 min-w-40">
            <label className="text-slate-400 text-xs font-medium block mb-1">
              Anomaly Threshold: <span className="text-slate-200">{Math.round(threshold * 100)}%</span>
            </label>
            <input
              type="range"
              min={0.05} max={0.75} step={0.05}
              value={threshold}
              onChange={e => setThreshold(Number(e.target.value))}
              className="w-full accent-indigo-500"
            />
            <div className="flex justify-between text-slate-500 text-xs mt-0.5">
              <span>5%</span><span>75%</span>
            </div>
          </div>

          {/* Run button */}
          <button
            onClick={fetchForecast}
            disabled={isLoading}
            className="shrink-0 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? '⏳ Analyzing…' : 'Run Forecast'}
          </button>

        </div>

        {/* ── States ── */}
        {error && (
          <div className="bg-red-900/30 border border-red-700/40 rounded-xl px-4 py-3 text-sm text-red-300">
            ⚠️ {error}
          </div>
        )}

        {isLoading && (
          <div className="flex items-center justify-center py-16 gap-3 text-slate-400">
            <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:0ms]" />
            <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:150ms]" />
            <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:300ms]" />
            <span className="text-sm ml-1">Running forecast pipeline…</span>
          </div>
        )}

        {!isLoading && !data && !error && (
          <div className="flex flex-col items-center justify-center py-20 gap-3 text-center">
            <p className="text-4xl">📈</p>
            <p className="text-slate-300 font-medium">Ready to forecast</p>
            <p className="text-slate-400 text-sm">
              Adjust the controls above and click <strong className="text-slate-300">Run Forecast</strong>
            </p>
          </div>
        )}

        {!isLoading && data && (
          <ForecastCard data={data} />
        )}

      </div>
    </div>
  )
}
