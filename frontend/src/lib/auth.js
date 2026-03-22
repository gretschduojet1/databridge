import { writable, derived } from 'svelte/store'

// Persist the token across page refreshes
const storedToken = localStorage.getItem('token')

export const token = writable(storedToken)
export const isAuthenticated = derived(token, $token => !!$token)

token.subscribe(value => {
  if (value) {
    localStorage.setItem('token', value)
  } else {
    localStorage.removeItem('token')
  }
})

export function logout() {
  token.set(null)
}
