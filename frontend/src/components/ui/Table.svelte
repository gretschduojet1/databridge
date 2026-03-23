<script>
  import * as XLSX from 'xlsx'

  // columns: [{ key, label, sortable?, render? }]
  export let columns = []
  export let rows = []
  export let total = 0
  export let page = 0
  export let pageSize = 25
  export let sortBy = null
  export let sortOrder = 'asc'
  export let loading = false
  export let exportName = 'export'

  export let onSort = () => {}
  export let onPage = () => {}

  $: totalPages = Math.ceil(total / pageSize)

  function handleSort(col) {
    if (!col.sortable) return
    if (sortBy === col.key) {
      onSort(col.key, sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      onSort(col.key, 'asc')
    }
  }

  function exportExcel() {
    const data = rows.map(row =>
      Object.fromEntries(columns.map(col => [col.label, row[col.key] ?? '']))
    )
    const ws = XLSX.utils.json_to_sheet(data)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, exportName)
    XLSX.writeFile(wb, `${exportName}.xlsx`)
  }
</script>

<div class="bg-white rounded-mac border border-surface-100 shadow-sm overflow-hidden">
  <div class="flex items-center justify-between px-5 py-3 border-b border-surface-100">
    <span class="text-xs text-surface-400">{total.toLocaleString()} results</span>
    <button
      on:click={exportExcel}
      class="text-xs text-accent hover:underline"
    >
      Export Excel
    </button>
  </div>

  <div class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-surface-100">
          {#each columns as col}
            <th
              class="px-5 py-3 text-left text-xs font-medium text-surface-400 uppercase tracking-wide whitespace-nowrap
                {col.sortable ? 'cursor-pointer select-none hover:text-surface-600' : ''}"
              on:click={() => handleSort(col)}
            >
              {col.label}
              {#if col.sortable && sortBy === col.key}
                <span class="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
              {/if}
            </th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#if loading}
          <tr>
            <td colspan={columns.length} class="px-5 py-8 text-center text-sm text-surface-300">
              Loading…
            </td>
          </tr>
        {:else if rows.length === 0}
          <tr>
            <td colspan={columns.length} class="px-5 py-8 text-center text-sm text-surface-300">
              No results
            </td>
          </tr>
        {:else}
          {#each rows as row}
            <tr class="border-b border-surface-50 hover:bg-surface-50 transition-colors">
              {#each columns as col}
                <td class="px-5 py-3 text-surface-700 whitespace-nowrap">
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
    <div class="flex items-center justify-between px-5 py-3 border-t border-surface-100">
      <span class="text-xs text-surface-400">
        Page {page + 1} of {totalPages}
      </span>
      <div class="flex gap-2">
        <button
          disabled={page === 0}
          on:click={() => onPage(page - 1)}
          class="text-xs px-3 py-1 rounded border border-surface-200 text-surface-600 disabled:opacity-30 hover:bg-surface-50"
        >
          Previous
        </button>
        <button
          disabled={page + 1 >= totalPages}
          on:click={() => onPage(page + 1)}
          class="text-xs px-3 py-1 rounded border border-surface-200 text-surface-600 disabled:opacity-30 hover:bg-surface-50"
        >
          Next
        </button>
      </div>
    </div>
  {/if}
</div>
