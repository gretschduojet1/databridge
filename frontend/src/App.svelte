<script>
  let ready = false

  async function checkApi() {
    try {
      const res = await fetch('http://localhost:8000/health')
      const data = await res.json()
      ready = data.status === 'ok'
    } catch {
      ready = false
    }
  }

  checkApi()
</script>

<main class="min-h-screen flex flex-col items-center justify-center">
  <div class="bg-white rounded-mac shadow-sm border border-surface-100 px-12 py-10 flex flex-col items-center gap-4">
    <h1 class="text-2xl font-semibold tracking-tight text-surface-900">Databridge</h1>
    <p class="text-surface-400 text-sm">
      API status:
      <span class={ready ? 'text-green-500' : 'text-red-400'}>
        {ready ? 'connected' : 'unavailable'}
      </span>
    </p>
  </div>
</main>
