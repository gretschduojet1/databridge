<script>
  import { onMount } from 'svelte'
  import { apiFetch } from '../../lib/api'
  import Table from '../ui/Table.svelte'
  import Badge from '../ui/Badge.svelte'

  let rows = [], total = 0, loading = false
  let page = 0, pageSize = 25
  let sortBy = 'name', sortOrder = 'asc'
  let category = ''

  const columns = [
    { key: 'sku',           label: 'SKU',        sortable: true },
    { key: 'name',          label: 'Name',        sortable: true },
    { key: 'category',      label: 'Category',    sortable: true, render: Badge },
    { key: 'stock_qty',     label: 'Stock',       sortable: true },
    { key: 'reorder_level', label: 'Reorder At',  sortable: false },
  ]

  async function load() {
    loading = true
    const params = new URLSearchParams({
      skip: page * pageSize,
      limit: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
      ...(category && { category }),
    })
    const res = await apiFetch(`/products/?${params}`)
    const data = await res.json()
    rows = data.items
    total = data.total
    loading = false
  }

  onMount(load)

  function handleSort(key, order) { sortBy = key; sortOrder = order; page = 0; load() }
  function handlePage(p) { page = p; load() }
</script>

<div class="p-8 flex flex-col gap-6">
  <div class="flex items-start justify-between">
    <div>
      <h2 class="text-xl font-bold text-surface-900">Products</h2>
      <p class="text-sm text-surface-400 mt-0.5">Inventory catalog</p>
    </div>
    <select
      bind:value={category}
      on:change={() => { page = 0; load() }}
      class="text-sm border border-surface-200 rounded-xl px-3 py-2 text-surface-700 focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white"
    >
      <option value="">All Categories</option>
      <option>Electronics</option>
      <option>Office</option>
      <option>Supplies</option>
    </select>
  </div>

  <Table
    {columns} {rows} {total} {page} {pageSize} {sortBy} {sortOrder} {loading}
    exportName="products"
    onSort={handleSort}
    onPage={handlePage}
  />
</div>
