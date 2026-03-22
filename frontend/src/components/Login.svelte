<script>
  import { token } from '../lib/auth'

  let email = ''
  let password = ''
  let error = ''
  let loading = false

  async function handleSubmit() {
    error = ''
    loading = true

    try {
      const res = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      if (res.ok) {
        const data = await res.json()
        token.set(data.access_token)
      } else {
        error = 'Invalid email or password'
      }
    } catch {
      error = 'Could not connect to the server'
    } finally {
      loading = false
    }
  }
</script>

<div class="min-h-screen bg-surface-50 flex items-center justify-center">
  <div class="w-full max-w-sm">
    <div class="bg-white rounded-mac shadow-sm border border-surface-100 p-8">

      <h1 class="text-xl font-semibold text-surface-900 mb-1">Databridge</h1>
      <p class="text-sm text-surface-400 mb-6">Sign in to continue</p>

      <form on:submit|preventDefault={handleSubmit} class="flex flex-col gap-4">
        <div class="flex flex-col gap-1">
          <label for="email" class="text-xs font-medium text-surface-500 uppercase tracking-wide">Email</label>
          <input
            id="email"
            type="email"
            bind:value={email}
            placeholder="you@example.com"
            required
            class="border border-surface-200 rounded-mac px-3 py-2 text-sm text-surface-900 placeholder:text-surface-300 focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
          />
        </div>

        <div class="flex flex-col gap-1">
          <label for="password" class="text-xs font-medium text-surface-500 uppercase tracking-wide">Password</label>
          <input
            id="password"
            type="password"
            bind:value={password}
            placeholder="••••••••"
            required
            class="border border-surface-200 rounded-mac px-3 py-2 text-sm text-surface-900 placeholder:text-surface-300 focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
          />
        </div>

        {#if error}
          <p class="text-xs text-red-500">{error}</p>
        {/if}

        <button
          type="submit"
          disabled={loading}
          class="bg-accent text-white text-sm font-medium py-2 rounded-mac hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {loading ? 'Signing in…' : 'Sign in'}
        </button>
      </form>

      <div class="mt-6 pt-5 border-t border-surface-100">
        <p class="text-xs text-surface-400 font-medium mb-2">Demo credentials</p>
        <div class="flex flex-col gap-1 text-xs text-surface-500 font-mono">
          <span>admin@databridge.io / admin</span>
          <span>demo@databridge.io / demo</span>
        </div>
      </div>

    </div>
  </div>
</div>
