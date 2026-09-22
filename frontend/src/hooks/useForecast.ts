import { useState, useCallback } from 'react'
import { getForecast } from '../api/forecast'
import type { ForecastResponse } from '../api/forecast'

interface UseForecastReturn {
  data: ForecastResponse | null
  isLoading: boolean
  error: string | null
  months: number
  threshold: number
  setMonths: (v: number) => void
  setThreshold: (v: number) => void
  fetchForecast: () => Promise<void>
}

export function useForecast(): UseForecastReturn {
  const [data, setData] = useState<ForecastResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [months, setMonths] = useState(6)
  const [threshold, setThreshold] = useState(0.3)

  const fetchForecast = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const { data: res } = await getForecast(months, threshold)
      setData(res)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch forecast.')
    } finally {
      setIsLoading(false)
    }
  }, [months, threshold])

  return { data, isLoading, error, months, threshold, setMonths, setThreshold, fetchForecast }
}
