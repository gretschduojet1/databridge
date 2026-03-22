<script>
  import { onMount, onDestroy } from 'svelte'
  import { apiFetch } from '../../lib/api'

  let jobs = []
  let loading = false
  let dispatching = null
  let pollInterval = null

  const statusStyles = {
    pending: 'bg-amber-100 text-amber-700',
    running: 'bg-indigo-100 text-indigo-700',
    success: 'bg-emerald-100 text-emerald-700',
    failed:  'bg-rose-100 text-rose-700',
  }

  async function load() {
    const res = await apiFetch('/jobs/')
    jobs = await res.json()
  }

  async function dispatch(type) {
    dispatching = type
    try {
      await apiFetch(`/jobs/dispatch/${type}`, { method: 'POST' })
      await load()
      startPolling()
    } finally {
      dispatching = null
    }
  }

  function startPolling() {
    if (pollInterval) return
    pollInterval = setInterval(async () => {
      await load()
      const active = jobs.some(j => j.status === 'pending' || j.status === 'running')
      if (!active) stopPolling()
    }, 2000)
  }

  function stopPolling() {
    clearInterval(pollInterval)
    pollInterval = null
  }

  function fmt(iso) {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  onMount(async () => {
    loading = true
    await load()
    loading = false
    const active = jobs.some(j => j.status === 'pending' || j.status === 'running')
    if (active) startPolling()
  })

  onDestroy(stopPolling)
</script>

<div class="p-8 flex flex-col gap-6">
  <div class="flex items-start justify-between">
    <div>
      <h2 class="text-xl font-bold text-surface-900">Background Jobs</h2>
      <p class="text-sm text-surface-400 mt-0.5">Dispatch and monitor async tasks</p>
    </div>
    <a
      href="http://localhost:5555"
      target="_blank"
      rel="noreferrer"
      class="inline-flex items-center gap-1.5 text-xs font-medium text-surface-500 hover:text-surface-800 bg-white border border-surface-200 hover:border-surface-300 px-3 py-2 rounded-xl transition-all"
    >
      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
      </svg>
      Flower dashboard
    </a>
  </div>

  <!-- Dispatch panel -->
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
    <div class="bg-white rounded-2xl border border-surface-100 shadow-sm p-6">
      <div class="inline-flex bg-indigo-50 rounded-xl p-2.5 mb-4">
        <svg class="w-5 h-5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      </div>
      <p class="text-sm font-semibold text-surface-900 mb-1">Generate Report</p>
      <p class="text-xs text-surface-400 mb-4">Recomputes all summary statistics across orders, customers, and inventory.</p>
      <button
        on:click={() => dispatch('report')}
        disabled={dispatching === 'report'}
        class="w-full bg-indigo-500 text-white text-sm font-medium py-2 rounded-xl hover:bg-indigo-600 transition-colors disabled:opacity-50 shadow-sm shadow-indigo-500/20"
      >
        {dispatching === 'report' ? 'Queuing…' : 'Run now'}
      </button>
    </div>

    <div class="bg-white rounded-2xl border border-surface-100 shadow-sm p-6">
      <div class="inline-flex bg-surface-50 rounded-xl p-2.5 mb-4">
        <svg class="w-5 h-5 text-surface-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <p class="text-sm font-semibold text-surface-900 mb-1">Data Sync</p>
      <p class="text-xs text-surface-400 mb-4">
        In production, data pipelines are orchestrated by Airflow. Sync jobs appear here automatically as they run.
      </p>
      <div class="w-full text-center text-xs text-surface-300 py-1.5">Managed by Airflow</div>
    </div>
  </div>

  <!-- Jobs table -->
  <div class="bg-white rounded-2xl border border-surface-100 shadow-sm overflow-hidden">
    <div class="flex items-center justify-between px-6 py-4 border-b border-surface-100">
      <span class="text-sm font-medium text-surface-500">
        Recent jobs
        {#if pollInterval}
          <span class="ml-2 inline-flex items-center gap-1 text-xs text-indigo-500">
            <span class="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse"></span>
            live
          </span>
        {/if}
      </span>
      <button on:click={load} class="text-xs text-surface-400 hover:text-surface-700 transition-colors">Refresh</button>
    </div>

    {#if loading}
      <div class="px-6 py-10 text-center text-sm text-surface-300">Loading…</div>
    {:else if jobs.length === 0}
      <div class="px-6 py-10 text-center text-sm text-surface-300">No jobs yet — dispatch one above.</div>
    {:else}
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-surface-50 border-b border-surface-100">
            <th class="px-6 py-3 text-left text-xs font-semibold text-surface-500 uppercase tracking-wide">Job</th>
            <th class="px-6 py-3 text-left text-xs font-semibold text-surface-500 uppercase tracking-wide">Status</th>
            <th class="px-6 py-3 text-left text-xs font-semibold text-surface-500 uppercase tracking-wide">Started</th>
            <th class="px-6 py-3 text-left text-xs font-semibold text-surface-500 uppercase tracking-wide">Updated</th>
            <th class="px-6 py-3 text-left text-xs font-semibold text-surface-500 uppercase tracking-wide">Result</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-50">
          {#each jobs as job}
            <tr class="hover:bg-surface-50/60 transition-colors">
              <td class="px-6 py-3.5">
                <span class="font-medium text-surface-800">{job.name.replace(/_/g, ' ')}</span>
                <p class="text-xs text-surface-400 font-mono mt-0.5">{job.id.slice(0, 8)}…</p>
              </td>
              <td class="px-6 py-3.5">
                <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold {statusStyles[job.status] ?? ''}">
                  {#if job.status === 'running'}
                    <span class="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse"></span>
                  {/if}
                  {job.status}
                </span>
              </td>
              <td class="px-6 py-3.5 text-surface-500 text-xs">{fmt(job.created_at)}</td>
              <td class="px-6 py-3.5 text-surface-500 text-xs">{fmt(job.updated_at)}</td>
              <td class="px-6 py-3.5 text-xs text-surface-500 max-w-xs truncate font-mono">
                {#if job.result}
                  {JSON.stringify(job.result)}
                {:else if job.error}
                  <span class="text-rose-500">{job.error}</span>
                {:else}
                  —
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
</div>
