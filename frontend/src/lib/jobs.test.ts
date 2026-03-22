import { get } from 'svelte/store'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('./api', () => ({
  apiFetch: vi.fn(),
}))

import { apiFetch } from './api'
import { jobCounts } from './jobs'

describe('jobCounts store', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  it('has active and failed shape', () => {
    const counts = get(jobCounts)
    expect(counts).toHaveProperty('active')
    expect(counts).toHaveProperty('failed')
  })

  it('counts active and failed jobs from API response', async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([
        { status: 'pending' },
        { status: 'running' },
        { status: 'failed' },
        { status: 'success' },
      ]),
    } as Response)

    // Subscribe to start the store, then flush the async poll() microtask
    const unsub = jobCounts.subscribe(() => {})
    await vi.advanceTimersByTimeAsync(1)
    unsub()

    const counts = get(jobCounts)
    expect(counts.active).toBe(2)
    expect(counts.failed).toBe(1)
  })

  it('handles a failed API response without throwing', async () => {
    vi.mocked(apiFetch).mockResolvedValue({ ok: false } as Response)

    const unsub = jobCounts.subscribe(() => {})
    await vi.advanceTimersByTimeAsync(1)
    unsub()

    // Just verify we didn't crash — value may retain previous counts
    expect(get(jobCounts)).toHaveProperty('active')
  })
})
