import api from './index'

export type ForecastResponse = {
  forecast: {
    historical: { month: string; total_revenue: number }[]
    predicted_revenue: number
    growth_rate: number
    based_on_months: number
    trend: 'upward' | 'downward' | 'stable'
  }
  anomalies: {
    region_anomalies: AnomalyItem[]
    product_anomalies: AnomalyItem[]
    total_anomalies: number
  }
  smart_recommendation: string
}

export type AnomalyItem = {
  label: string
  revenue: number
  mean_revenue: number
  deviation_pct: number
  type: 'above_average' | 'below_average'
  severity: 'high' | 'medium'
}

/**
 * POST /api/forecast/
 * Forecasting + anomaly detection + smart recommendations
 */
export const getForecast = (months = 6, anomaly_threshold = 0.3) =>
  api.post<ForecastResponse>('/api/forecast/', { months, anomaly_threshold })
