import { useEffect, useRef } from 'react'
import { useChat } from '../hooks/useChat'
import ChatInput from '../components/ChatInput'
import MessageBubble from '../components/MessageBubble'

const SUGGESTIONS = [
  'Show me total sales by region',
  'Which product has the highest revenue?',
  'Show monthly sales trend',
  'Compare North and South region sales',
]

export default function ChatPage() {
  const { messages, isLoading, ragChunks, sendMessage, uploadFile, clearChat } = useChat()
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex flex-col h-full">

      {/* ── Header ── */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-slate-700 bg-slate-800/50 shrink-0">
        <div>
          <h1 className="text-slate-100 font-semibold text-sm">AI Business Analyst</h1>
          <p className="text-slate-400 text-xs">
            Ask questions about your sales data in plain English
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* RAG status badge */}
          <span className={`text-xs px-2 py-1 rounded-full border ${
            ragChunks > 0
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              : 'bg-slate-700 text-slate-400 border-slate-600'
          }`}>
            📎 {ragChunks > 0 ? `${ragChunks} doc chunks` : 'No docs uploaded'}
          </span>
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* ── Messages ── */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-5">
        {messages.length === 0 ? (
          /* Empty state — show suggestions */
          <div className="flex flex-col items-center justify-center h-full gap-6 text-center">
            <div>
              <p className="text-4xl mb-3">✦</p>
              <h2 className="text-slate-200 text-lg font-semibold">What would you like to know?</h2>
              <p className="text-slate-400 text-sm mt-1">
                Ask anything about your business data
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  disabled={isLoading}
                  className="text-left text-sm text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl px-4 py-3 transition-colors disabled:opacity-40"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map(msg => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      {/* ── Input ── */}
      <ChatInput
        onSend={sendMessage}
        onUpload={uploadFile}
        isLoading={isLoading}
      />

    </div>
  )
}
