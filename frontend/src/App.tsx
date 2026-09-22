import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import ForecastPage from './pages/ForecastPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">

        {/* ── Top Navigation ── */}
        <nav className="bg-slate-800 border-b border-slate-700 px-6 py-3 flex items-center gap-8 shrink-0">
          <span className="text-indigo-400 font-bold text-lg tracking-tight">
            ✦ Generative BI
          </span>
          <div className="flex gap-4">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `text-sm font-medium px-3 py-1.5 rounded-md transition-colors ${
                  isActive
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700'
                }`
              }
            >
              💬 Chat
            </NavLink>
            <NavLink
              to="/forecast"
              className={({ isActive }) =>
                `text-sm font-medium px-3 py-1.5 rounded-md transition-colors ${
                  isActive
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700'
                }`
              }
            >
              📈 Forecast
            </NavLink>
          </div>
        </nav>

        {/* ── Page Content ── */}
        <main className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/forecast" element={<ForecastPage />} />
          </Routes>
        </main>

      </div>
    </BrowserRouter>
  )
}
