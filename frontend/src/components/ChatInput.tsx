import { useState, useRef, KeyboardEvent } from 'react'

interface Props {
  onSend: (question: string) => void
  onUpload: (file: File) => void
  isLoading: boolean
}

export default function ChatInput({ onSend, onUpload, isLoading }: Props) {
  const [value, setValue] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  const handleSend = () => {
    if (!value.trim() || isLoading) return
    onSend(value.trim())
    setValue('')
  }

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      onUpload(file)
      e.target.value = ''
    }
  }

  return (
    <div className="bg-slate-800 border-t border-slate-700 px-4 py-3">
      <div className="flex items-end gap-2 max-w-4xl mx-auto">

        {/* File upload button */}
        <button
          onClick={() => fileRef.current?.click()}
          disabled={isLoading}
          title="Upload document (PDF, TXT, CSV)"
          className="shrink-0 p-2.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-white transition-colors disabled:opacity-40"
        >
          📎
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".txt,.pdf,.csv"
          onChange={handleFile}
          className="hidden"
        />

        {/* Text input */}
        <textarea
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask anything about your data… (Enter to send)"
          disabled={isLoading}
          rows={1}
          className="flex-1 resize-none bg-slate-700 text-slate-100 placeholder-slate-400 rounded-lg px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-40 max-h-32 overflow-y-auto"
          style={{ lineHeight: '1.5' }}
        />

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={!value.trim() || isLoading}
          className="shrink-0 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isLoading ? '⏳' : 'Send'}
        </button>

      </div>
      <p className="text-center text-slate-500 text-xs mt-1.5">
        Shift+Enter for new line · 📎 to upload PDF / TXT / CSV
      </p>
    </div>
  )
}
