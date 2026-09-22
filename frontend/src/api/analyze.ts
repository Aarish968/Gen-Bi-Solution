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

/**
 * POST /api/analyze/
 * Full multi-agent pipeline — plan → SQL → insight → chart → recommendation
 */
export const analyzeQuestion = (question: string) =>
  api.post<AnalyzeResponse>('/api/analyze/', { question })
