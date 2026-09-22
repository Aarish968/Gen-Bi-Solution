import api from './index'

export type UploadResponse = {
  ingested_chunks: number
  total_chunks_in_index: number
  filename: string
}

export type SearchResponse = {
  query: string
  results: string[]
  message?: string
}

export type StatusResponse = {
  total_chunks: number
  ready: boolean
}

/**
 * POST /api/documents/upload
 * Upload a TXT, PDF or CSV file into the RAG index.
 * Requires multipart/form-data — uses FormData, not JSON.
 */
export const uploadDocument = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post<UploadResponse>('/api/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/**
 * POST /api/documents/search
 * Search across uploaded documents for relevant chunks.
 */
export const searchDocuments = (query: string) =>
  api.post<SearchResponse>(`/api/documents/search?query=${encodeURIComponent(query)}`)

/**
 * GET /api/documents/status
 * Returns how many chunks are stored in the RAG index.
 */
export const getDocumentStatus = () =>
  api.get<StatusResponse>('/api/documents/status')
