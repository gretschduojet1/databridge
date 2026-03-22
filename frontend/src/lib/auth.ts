import { writable, derived } from 'svelte/store'
import type { Writable, Readable } from 'svelte/store'

// Persist the token across page refreshes
const storedToken = localStorage.getItem('token')

export const token: Writable<string | null> = writable(storedToken)
export const isAuthenticated: Readable<boolean> = derived(token, $token => !!$token)

token.subscribe(value => {
  if (value) {
    localStorage.setItem('token', value)
  } else {
    localStorage.removeItem('token')
  }
})

export function logout(): void {
  token.set(null)
}
