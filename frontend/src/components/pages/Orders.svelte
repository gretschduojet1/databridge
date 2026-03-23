<script>
  import { onMount } from 'svelte'
  import { apiFetch } from '../../lib/api'
  import Table from '../ui/Table.svelte'

  let rows = [], total = 0, loading = false
  let page = 0, pageSize = 25
  let sortBy = 'ordered_at', sortOrder = 'desc'
  let dateFrom = '', dateTo = ''

  const columns = [
    { key: 'id',          label: 'Order #',   sortable: false },
    { key: 'customer_id', label: 'Customer',  sortable: false },
    { key: 'product_id',  label: 'Product',   sortable: false },
    { key: 'quantity',    label: 'Qty',       sortable: true },
    { key: 'unit_price',  label: 'Unit Price', sortable: true },
    { key: 'total',       label: 'Total',     sortable: false },
    { key: 'ordered_at',  label: 'Date',      sortable: true },
  ]

  async function load() {
    loading = true
    const params = new URLSearchParams({
      skip: page * pageSize,
      limit: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
      ...(dateFrom && { date_from: dateFrom }),
      ...(dateTo && { date_to: dateTo }),
    })
    const res = await apiFetch(`/orders/?${params}`)
    const data = await res.json()
    rows = data.items.map(r => ({
      ...r,
      unit_price: `$${parseFloat(r.unit_price).toFixed(2)}`,
      total: `$${(r.quantity * parseFloat(r.unit_price)).toFixed(2)}`,
      ordered_at: new Date(r.ordered_at).toLocaleDateString(),
    }))
    total = data.total
    loading = false
  }

  onMount(load)

  function handleSort(key, order) { sortBy = key; sortOrder = order; page = 0; load() }
  function handlePage(p) { page = p; load() }
</script>

<div class="p-6 flex flex-col gap-4">
  <div class="flex items-center justify-between flex-wrap gap-3">
    <h2 class="text-lg font-semibold text-surface-900">Orders</h2>
    <div class="flex items-center gap-2 text-sm">
      <input
        type="date" bind:value={dateFrom}
        on:change={() => { page = 0; load() }}
        class="border border-surface-200 rounded-mac px-3 py-1.5 text-surface-700 focus:outline-none focus:ring-2 focus:ring-accent"
      />
      <span class="text-surface-300">to</span>
      <input
        type="date" bind:value={dateTo}
        on:change={() => { page = 0; load() }}
        class="border border-surface-200 rounded-mac px-3 py-1.5 text-surface-700 focus:outline-none focus:ring-2 focus:ring-accent"
      />
    </div>
  </div>

  <Table
    {columns} {rows} {total} {page} {pageSize} {sortBy} {sortOrder} {loading}
    exportName="orders"
    onSort={handleSort}
    onPage={handlePage}
  />
</div>
