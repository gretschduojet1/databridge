import { get } from 'svelte/store'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

// Must import after setting up localStorage mock (jsdom provides it)
import { isAuthenticated, logout, token } from './auth'

describe('auth store', () => {
  beforeEach(() => {
    localStorage.clear()
    token.set(null)
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('starts unauthenticated when localStorage is empty', () => {
    expect(get(token)).toBeNull()
    expect(get(isAuthenticated)).toBe(false)
  })

  it('isAuthenticated is true when token is set', () => {
    token.set('abc.def.ghi')
    expect(get(isAuthenticated)).toBe(true)
  })

  it('persists token to localStorage', () => {
    token.set('my-token')
    expect(localStorage.getItem('token')).toBe('my-token')
  })

  it('removes token from localStorage on logout', () => {
    token.set('my-token')
    logout()
    expect(localStorage.getItem('token')).toBeNull()
    expect(get(token)).toBeNull()
    expect(get(isAuthenticated)).toBe(false)
  })
})
