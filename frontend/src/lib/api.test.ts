import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { get } from 'svelte/store'
import { token } from './auth'
import { apiFetch } from './api'

function mockFetch(status: number, body: unknown = {}): void {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    status,
    json: () => Promise.resolve(body),
    ok: status >= 200 && status < 300,
  }))
}

describe('apiFetch', () => {
  beforeEach(() => {
    localStorage.clear()
    token.set(null)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  it('sends JSON content-type header', async () => {
    mockFetch(200)
    await apiFetch('/test')
    const call = (fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(call[1].headers['Content-Type']).toBe('application/json')
  })

  it('attaches Authorization header when token is set', async () => {
    token.set('test-token')
    mockFetch(200)
    await apiFetch('/test')
    const call = (fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(call[1].headers['Authorization']).toBe('Bearer test-token')
  })

  it('omits Authorization header when no token', async () => {
    mockFetch(200)
    await apiFetch('/test')
    const call = (fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(call[1].headers['Authorization']).toBeUndefined()
  })

  it('returns undefined and clears token on 401', async () => {
    token.set('expired-token')
    mockFetch(401)
    const result = await apiFetch('/protected')
    expect(result).toBeUndefined()
    expect(get(token)).toBeNull()
  })

  it('returns the response on success', async () => {
    mockFetch(200, { ok: true })
    const result = await apiFetch('/health')
    expect(result).toBeDefined()
    expect(result!.status).toBe(200)
  })
})
