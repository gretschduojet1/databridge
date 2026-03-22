import { get } from 'svelte/store'
import { token, logout } from './auth'

const BASE_URL = 'http://localhost:8000'

export async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers }

  const currentToken = get(token)
  if (currentToken) {
    headers['Authorization'] = `Bearer ${currentToken}`
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  // Token expired or invalid — force logout
  if (res.status === 401) {
    logout()
    return
  }

  return res
}
