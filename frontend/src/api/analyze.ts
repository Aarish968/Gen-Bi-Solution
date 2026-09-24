import api from './index'

export type AnalyzeResponse = {
  question: string
  plan: string[]
  sql: string
  results: Record<string, unknown>[]
  insight: string
  chart_config: {
    chart_type: string
    title: string
    labels: string[]
    datasets: { label: string; data: number[] }[]
  }
  recommendation: string
}

export type TaskStatus =
  | { task_id: string; status: 'pending' }
  | { task_id: string; status: 'complete'; result: AnalyzeResponse }
  | { task_id: string; status: 'failed'; error: string }

/**
 * POST /api/analyze/
 * Submits question as a background Celery task.
 * Returns task_id immediately — no waiting.
 */
export const submitAnalyze = (question: string) =>
  api.post<{ task_id: string }>('/api/analyze/', { question })

/**
 * GET /api/task/{task_id}
 * Poll this to check task progress.
 * Returns pending / complete / failed.
 */
export const pollTaskStatus = (task_id: string) =>
  api.get<TaskStatus>(`/api/task/${task_id}`)
