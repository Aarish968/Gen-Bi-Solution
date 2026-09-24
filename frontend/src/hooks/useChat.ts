import { useState, useRef, useCallback } from 'react'
import { submitAnalyze, pollTaskStatus } from '../api/analyze'
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

// Poll every 5 seconds — max 36 attempts = 3 minutes before giving up
const POLL_INTERVAL_MS = 5000
const MAX_POLL_ATTEMPTS = 36
// Stop polling after this many consecutive network errors (server down)
const MAX_NETWORK_ERRORS = 3

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [ragChunks, setRagChunks] = useState(0)
  const idRef = useRef(0)

  const nextId = () => String(++idRef.current)

  const refreshRagStatus = useCallback(async () => {
    try {
      const { data } = await getDocumentStatus()
      setRagChunks(data.total_chunks)
    } catch {
      // non-critical — silently ignore
    }
  }, [])

  // ── Polling helper ───────────────────────────────────────────────────────
  const pollUntilDone = useCallback(
    async (task_id: string, loadingId: string) => {
      let attempts = 0
      let networkErrors = 0

      const stopWithError = (msg: string) => {
        setMessages(prev =>
          prev.map(m =>
            m.id === loadingId ? { ...m, isLoading: false, error: msg } : m
          )
        )
        setIsLoading(false)
      }

      const poll = async (): Promise<void> => {
        attempts++

        // ── Give up after max attempts ──────────────────────────────────
        if (attempts > MAX_POLL_ATTEMPTS) {
          stopWithError('Request timed out after 3 minutes. Please try again.')
          return
        }

        try {
          const { data } = await pollTaskStatus(task_id)

          // Reset network error counter on success
          networkErrors = 0

          if (data.status === 'pending') {
            setTimeout(poll, POLL_INTERVAL_MS)
            return
          }

          if (data.status === 'complete') {
            setMessages(prev =>
              prev.map(m =>
                m.id === loadingId
                  ? {
                      id: loadingId,
                      role: 'ai' as MessageRole,
                      text: data.result.insight,
                      data: data.result,
                      isLoading: false,
                    }
                  : m
              )
            )
            setIsLoading(false)
            return
          }

          if (data.status === 'failed') {
            // Parse error message — check for quota error
            const errMsg = data.error ?? ''
            const isQuota =
              errMsg.includes('429') ||
              errMsg.includes('RESOURCE_EXHAUSTED') ||
              errMsg.includes('quota')

            stopWithError(
              isQuota
                ? '⚠️ Gemini API quota exceeded. Please wait 1 minute and try again.'
                : `Task failed: ${errMsg}`
            )
            return
          }

        } catch (err: unknown) {
          networkErrors++

          // ── Server down or unreachable ──────────────────────────────
          // Check HTTP status — 502/503/504 = server down
          const status = (err as { response?: { status?: number } })?.response?.status
          if (status === 502 || status === 503 || status === 504) {
            stopWithError('⚠️ Server is down. Please restart FastAPI and Celery.')
            return
          }

          // Stop after MAX_NETWORK_ERRORS consecutive failures
          if (networkErrors >= MAX_NETWORK_ERRORS) {
            stopWithError(
              '⚠️ Lost connection to server after 3 attempts. Please check if FastAPI and Celery are running.'
            )
            return
          }

          // Transient error — retry after interval
          setTimeout(poll, POLL_INTERVAL_MS)
        }
      }

      setTimeout(poll, POLL_INTERVAL_MS)
    },
    []
  )

  // ── Send message ─────────────────────────────────────────────────────────
  const sendMessage = useCallback(
    async (question: string) => {
      if (!question.trim() || isLoading) return

      // 1. Add user message immediately
      setMessages(prev => [
        ...prev,
        { id: nextId(), role: 'user', text: question },
      ])

      // 2. Add loading placeholder
      const loadingId = nextId()
      setMessages(prev => [
        ...prev,
        { id: loadingId, role: 'ai', text: '', isLoading: true },
      ])
      setIsLoading(true)

      try {
        // 3. Submit task → get task_id back immediately
        const { data } = await submitAnalyze(question)

        // 4. Start polling for result
        await pollUntilDone(data.task_id, loadingId)
      } catch (err: unknown) {
        const message =
          err instanceof Error
            ? err.message
            : 'Could not connect to server. Make sure FastAPI and Celery are running.'
        setMessages(prev =>
          prev.map(m =>
            m.id === loadingId
              ? { ...m, isLoading: false, error: message }
              : m
          )
        )
        setIsLoading(false)
      }
    },
    [isLoading, pollUntilDone]
  )

  // ── Upload file to RAG ────────────────────────────────────────────────────
  const uploadFile = useCallback(
    async (file: File) => {
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
                  role: 'ai' as MessageRole,
                  text: `✅ "${data.filename}" ingested — ${data.ingested_chunks} chunks added. Total: ${data.total_chunks_in_index}.`,
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
                  ...m,
                  isLoading: false,
                  error: `Failed to upload "${file.name}". Supported: .txt, .pdf, .csv`,
                }
              : m
          )
        )
      }
    },
    [refreshRagStatus]
  )

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
