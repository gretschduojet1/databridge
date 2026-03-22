import { readable } from 'svelte/store'
import { apiFetch } from './api'

// Polls the jobs endpoint and exposes a count of pending + running jobs.
// Components read this store; the sidebar uses it for the badge.
export const activeJobCount = readable(0, (set) => {
  async function poll() {
    try {
      const res = await apiFetch('/jobs/')
      if (!res.ok) return
      const jobs = await res.json()
      set(jobs.filter(j => j.status === 'pending' || j.status === 'running').length)
    } catch {
      // silently ignore network errors
    }
  }

  poll()
  const interval = setInterval(poll, 3000)
  return () => clearInterval(interval)
})
