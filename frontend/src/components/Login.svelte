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

<div class="min-h-screen bg-surface-900 flex">
  <!-- Left panel -->
  <div class="hidden lg:flex flex-col justify-between w-1/2 bg-gradient-to-br from-indigo-600 via-violet-600 to-purple-700 p-12">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center">
        <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
        </svg>
      </div>
      <span class="text-white font-semibold text-lg">Databridge</span>
    </div>

    <div>
      <h1 class="text-4xl font-bold text-white leading-tight mb-4">
        Your data,<br />unified.
      </h1>
      <p class="text-indigo-200 text-base leading-relaxed max-w-sm">
        Real-time visibility across customers, inventory, and sales — all in one place.
      </p>
    </div>

    <div class="flex gap-4">
      <div class="bg-white/10 rounded-xl px-4 py-3 flex-1">
        <p class="text-white font-bold text-xl">500+</p>
        <p class="text-indigo-200 text-xs mt-0.5">Orders tracked</p>
      </div>
      <div class="bg-white/10 rounded-xl px-4 py-3 flex-1">
        <p class="text-white font-bold text-xl">200+</p>
        <p class="text-indigo-200 text-xs mt-0.5">Customers</p>
      </div>
      <div class="bg-white/10 rounded-xl px-4 py-3 flex-1">
        <p class="text-white font-bold text-xl">3</p>
        <p class="text-indigo-200 text-xs mt-0.5">Data sources</p>
      </div>
    </div>
  </div>

  <!-- Right panel -->
  <div class="flex-1 flex items-center justify-center p-8 bg-white">
    <div class="w-full max-w-sm">
      <div class="lg:hidden flex items-center gap-2 mb-8">
        <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
          <svg class="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
          </svg>
        </div>
        <span class="font-semibold text-surface-900">Databridge</span>
      </div>

      <h2 class="text-2xl font-bold text-surface-900 mb-1">Welcome back</h2>
      <p class="text-sm text-surface-400 mb-8">Sign in to your account</p>

      <form on:submit|preventDefault={handleSubmit} class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <label for="email" class="text-xs font-semibold text-surface-600 uppercase tracking-wide">Email</label>
          <input
            id="email"
            type="email"
            bind:value={email}
            placeholder="you@example.com"
            required
            class="border border-surface-200 rounded-xl px-4 py-2.5 text-sm text-surface-900 placeholder:text-surface-300 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition-shadow"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <label for="password" class="text-xs font-semibold text-surface-600 uppercase tracking-wide">Password</label>
          <input
            id="password"
            type="password"
            bind:value={password}
            placeholder="••••••••"
            required
            class="border border-surface-200 rounded-xl px-4 py-2.5 text-sm text-surface-900 placeholder:text-surface-300 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition-shadow"
          />
        </div>

        {#if error}
          <div class="bg-rose-50 border border-rose-100 rounded-xl px-4 py-2.5">
            <p class="text-xs text-rose-600">{error}</p>
          </div>
        {/if}

        <button
          type="submit"
          disabled={loading}
          class="bg-indigo-500 text-white text-sm font-semibold py-2.5 rounded-xl hover:bg-indigo-600 transition-colors disabled:opacity-50 shadow-lg shadow-indigo-500/20 mt-1"
        >
          {loading ? 'Signing in…' : 'Sign in'}
        </button>
      </form>

      <div class="mt-8 pt-6 border-t border-surface-100">
        <p class="text-xs font-semibold text-surface-400 uppercase tracking-wide mb-3">Demo credentials</p>
        <div class="flex flex-col gap-2">
          <div class="bg-surface-50 rounded-xl px-4 py-2.5 flex items-center justify-between">
            <span class="text-xs text-surface-500 font-mono">admin@databridge.io</span>
            <span class="text-xs font-semibold text-indigo-500 bg-indigo-50 px-2 py-0.5 rounded-md">admin</span>
          </div>
          <div class="bg-surface-50 rounded-xl px-4 py-2.5 flex items-center justify-between">
            <span class="text-xs text-surface-500 font-mono">demo@databridge.io</span>
            <span class="text-xs font-semibold text-surface-400 bg-surface-100 px-2 py-0.5 rounded-md">viewer</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
