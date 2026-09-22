import axios from 'axios'

/**
 * Single shared Axios instance for the entire app.
 *
 * baseURL is empty — Vite proxy handles /api/* → http://localhost:8000
 * so we never hardcode the backend URL anywhere else.
 *
 * All API files import this instance — never create axios.create() again.
 */
const api = axios.create({
  baseURL: '',
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000, // 60s — LLM calls can be slow
})

export default api
