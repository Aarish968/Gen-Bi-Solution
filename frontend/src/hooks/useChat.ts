import { useState, useRef, useCallback } from 'react'
import { analyzeQuestion } from '../api/analyze'
import type { AnalyzeResponse } from '../api/analyze'
import { uploadDocument, getDocumentStatus } from '../api/documents'

export type MessageRole = 'user' | 'ai'

export type ChatMessage = {
  id: string
  role: MessageRole
  text: string
  data?: AnalyzeResponse
  isLoading?: boolean
  error?: string
}

type UseChatReturn = {
  messages: ChatMessage[]
  isLoading: boolean
  ragReady: boolean
  ragChunks: number
  sendMessage: (question: string) => Promise<void>
  uploadFile: (file: File) => Promise<void>
  clearChat: () => void
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [ragChunks, setRagChunks] = useState(0)
  const idRef = useRef(0)

  const nextId = () => String(++idRef.current)

  // ── Check RAG status on demand ───────────────────────────────────────────
  const refreshRagStatus = useCallback(async () => {
    try {
      const { data } = await getDocumentStatus()
      setRagChunks(data.total_chunks)
    } catch {
      // silently ignore — RAG status is non-critical
    }
  }, [])

  // ── Send a question through the full analyze pipeline ───────────────────
  const sendMessage = useCallback(async (question: string) => {
    if (!question.trim() || isLoading) return

    // 1. Add user message immediately
    const userMsg: ChatMessage = { id: nextId(), role: 'user', text: question }
    setMessages(prev => [...prev, userMsg])

    // 2. Add loading placeholder
    const loadingId = nextId()
    setMessages(prev => [
      ...prev,
      { id: loadingId, role: 'ai', text: '', isLoading: true },
    ])
    setIsLoading(true)

    try {
      const { data } = await analyzeQuestion(question)

      // 3. Replace loading placeholder with real response
      setMessages(prev =>
        prev.map(m =>
          m.id === loadingId
            ? { id: loadingId, role: 'ai', text: data.insight, data, isLoading: false }
            : m
        )
      )
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Something went wrong. Please try again.'
      setMessages(prev =>
        prev.map(m =>
          m.id === loadingId
            ? { id: loadingId, role: 'ai', text: '', error: message, isLoading: false }
            : m
        )
      )
    } finally {
      setIsLoading(false)
    }
  }, [isLoading])

  // ── Upload a document to RAG ─────────────────────────────────────────────
  const uploadFile = useCallback(async (file: File) => {
    const uploadingId = nextId()
    setMessages(prev => [
      ...prev,
      {
        id: uploadingId,
        role: 'ai',
        text: `Uploading "${file.name}"...`,
        isLoading: true,
      },
    ])

    try {
      const { data } = await uploadDocument(file)
      setMessages(prev =>
        prev.map(m =>
          m.id === uploadingId
            ? {
                id: uploadingId,
                role: 'ai',
                text: `✅ "${data.filename}" ingested — ${data.ingested_chunks} chunks added. Total in index: ${data.total_chunks_in_index}.`,
                isLoading: false,
              }
            : m
        )
      )
      await refreshRagStatus()
    } catch {
      setMessages(prev =>
        prev.map(m =>
          m.id === uploadingId
            ? {
                id: uploadingId,
                role: 'ai',
                text: '',
                error: `Failed to upload "${file.name}". Only .txt, .pdf, .csv files are supported.`,
                isLoading: false,
              }
            : m
        )
      )
    }
  }, [refreshRagStatus])

  const clearChat = useCallback(() => setMessages([]), [])

  return {
    messages,
    isLoading,
    ragReady: ragChunks > 0,
    ragChunks,
    sendMessage,
    uploadFile,
    clearChat,
  }
}
