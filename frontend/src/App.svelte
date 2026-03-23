<script>
  import { isAuthenticated, logout } from './lib/auth'
  import Login from './components/Login.svelte'
</script>

{#if $isAuthenticated}
  <div class="min-h-screen bg-surface-50">
    <header class="bg-white border-b border-surface-100 px-6 py-4 flex items-center justify-between">
      <h1 class="text-base font-semibold text-surface-900">Databridge</h1>
      <button
        on:click={logout}
        class="text-xs text-surface-400 hover:text-surface-600 transition-colors"
      >
        Sign out
      </button>
    </header>

    <main class="p-6">
      <p class="text-sm text-surface-500">Dashboard coming soon.</p>
    </main>
  </div>
{:else}
  <Login />
{/if}
