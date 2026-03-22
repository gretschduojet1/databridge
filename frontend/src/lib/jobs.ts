import { readable } from 'svelte/store'
import type { Readable } from 'svelte/store'
import { apiFetch } from './api'

interface JobCounts {
  active: number
  failed: number
}

interface Job {
  status: string
}

export const jobCounts: Readable<JobCounts> = readable({ active: 0, failed: 0 }, (set) => {
  async function poll(): Promise<void> {
    try {
      const res = await apiFetch('/jobs/')
      if (!res || !res.ok) return
      const jobs: Job[] = await res.json()
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
