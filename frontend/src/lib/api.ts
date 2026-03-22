import { get } from 'svelte/store'
import { token, logout } from './auth'

const BASE_URL = 'http://localhost:8000'

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response | undefined> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  const currentToken = get(token)
  if (currentToken) {
    headers['Authorization'] = `Bearer ${currentToken}`
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  // Token expired or invalid — force logout
  if (res.status === 401) {
    logout()
    return undefined
  }

  return res
}
