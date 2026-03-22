<script lang="ts">
  import type { SvelteComponent } from 'svelte'

  interface Column {
    key: string
    label: string
    sortable?: boolean
    render?: typeof SvelteComponent
  }

  export let columns: Column[] = []
  export let rows: Record<string, unknown>[] = []
  export let total: number = 0
  export let page: number = 0
  export let pageSize: number = 25
  export let sortBy: string | null = null
  export let sortOrder: 'asc' | 'desc' = 'asc'
  export let loading: boolean = false

  export let onSort: (key: string, order: 'asc' | 'desc') => void = () => {}
  export let onPage: (page: number) => void = () => {}
  export let onExport: (() => Promise<void>) | null = null

  let exporting: boolean = false
  let exportDone: boolean = false

  $: totalPages = Math.ceil(total / pageSize)

  function handleSort(col) {
    if (!col.sortable) return
    if (sortBy === col.key) {
      onSort(col.key, sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      onSort(col.key, 'asc')
    }
  }

  async function handleExport() {
    if (!onExport) return
    exporting = true
    try {
      await onExport()
      exportDone = true
      setTimeout(() => exportDone = false, 3000)
    } finally {
      exporting = false
    }
  }
</script>

<div class="bg-white rounded-2xl border border-surface-100 shadow-sm overflow-hidden">
  <div class="flex items-center justify-between px-6 py-4 border-b border-surface-100">
    <span class="text-sm font-medium text-surface-500">
      {total.toLocaleString()} <span class="text-surface-300">results</span>
    </span>
    <button
      on:click={handleExport}
      disabled={!onExport || exporting}
      class="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-all disabled:opacity-40
        {exportDone
          ? 'bg-emerald-50 text-emerald-600'
          : 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100 hover:text-indigo-700'}"
    >
      {#if exporting}
        <svg class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Exporting…
      {:else if exportDone}
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        Queued — check your email
      {:else}
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        Export
      {/if}
    </button>
  </div>

  <div class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead>
        <tr class="bg-surface-50 border-b border-surface-100">
          {#each columns as col}
            <th
              class="px-6 py-3 text-left text-xs font-semibold text-surface-500 uppercase tracking-wide whitespace-nowrap
                {col.sortable ? 'cursor-pointer select-none hover:text-surface-800' : ''}"
              on:click={() => handleSort(col)}
            >
              <span class="flex items-center gap-1">
                {col.label}
                {#if col.sortable}
                  <span class="text-surface-300 {sortBy === col.key ? 'text-indigo-500' : ''}">
                    {sortBy === col.key ? (sortOrder === 'asc' ? '↑' : '↓') : '↕'}
                  </span>
                {/if}
              </span>
            </th>
          {/each}
        </tr>
      </thead>
      <tbody class="divide-y divide-surface-50">
        {#if loading}
          <tr>
            <td colspan={columns.length} class="px-6 py-10 text-center text-sm text-surface-300">
              Loading…
            </td>
          </tr>
        {:else if rows.length === 0}
          <tr>
            <td colspan={columns.length} class="px-6 py-10 text-center text-sm text-surface-300">
              No results
            </td>
          </tr>
        {:else}
          {#each rows as row}
            <tr class="hover:bg-surface-50/60 transition-colors">
              {#each columns as col}
                <td class="px-6 py-3.5 text-surface-700 whitespace-nowrap">
                  {#if col.render}
                    <svelte:component this={col.render} value={row[col.key]} />
                  {:else}
                    {row[col.key] ?? '—'}
                  {/if}
                </td>
              {/each}
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>

  {#if totalPages > 1}
    <div class="flex items-center justify-between px-6 py-4 border-t border-surface-100 bg-surface-50/50">
      <span class="text-xs text-surface-400">
        Page {page + 1} of {totalPages}
      </span>
      <div class="flex gap-2">
        <button
          disabled={page === 0}
          on:click={() => onPage(page - 1)}
          class="text-xs px-3 py-1.5 rounded-lg border border-surface-200 text-surface-600 disabled:opacity-30 hover:bg-white hover:border-surface-300 transition-all"
        >
          ← Prev
        </button>
        <button
          disabled={page + 1 >= totalPages}
          on:click={() => onPage(page + 1)}
          class="text-xs px-3 py-1.5 rounded-lg border border-surface-200 text-surface-600 disabled:opacity-30 hover:bg-white hover:border-surface-300 transition-all"
        >
          Next →
        </button>
      </div>
    </div>
  {/if}
</div>
