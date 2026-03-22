import { readable } from 'svelte/store'
import { apiFetch } from './api'

export const jobCounts = readable({ active: 0, failed: 0 }, (set) => {
  async function poll() {
    try {
      const res = await apiFetch('/jobs/')
      if (!res.ok) return
      const jobs = await res.json()
      set({
        active: jobs.filter(j => j.status === 'pending' || j.status === 'running').length,
        failed: jobs.filter(j => j.status === 'failed').length,
      })
    } catch {
      // silently ignore network errors
    }
  }

  poll()
  const interval = setInterval(poll, 3000)
  return () => clearInterval(interval)
})
