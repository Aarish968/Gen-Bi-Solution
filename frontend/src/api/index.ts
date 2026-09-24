import axios from 'axios'

/**
 * Single shared Axios instance for the entire app.
 *
 * baseURL is empty — Vite proxy handles /api/* → http://localhost:8000
 * Timeout: 120s — LLM calls chain 6 Gemini requests, can take 25-40s
 */
const api = axios.create({
  baseURL: '',
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000, // 120 seconds
})

// Response interceptor — better error messages
api.interceptors.response.use(
  res => res,
  err => {
    if (err.code === 'ECONNABORTED') {
      err.message = 'Request timed out. The AI is taking too long — please try again.'
    } else if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
      err.message = 'Cannot connect to backend. Make sure the FastAPI server is running on port 8000.'
    }
    return Promise.reject(err)
  }
)

export default api
