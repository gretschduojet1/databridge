<script>
  import { onMount } from 'svelte'
  import { apiFetch } from '../../lib/api'
  import Table from '../ui/Table.svelte'
  import Badge from '../ui/Badge.svelte'

  let rows = [], total = 0, loading = false
  let page = 0, pageSize = 25
  let sortBy = 'name', sortOrder = 'asc'
  let region = ''

  const columns = [
    { key: 'name',       label: 'Name',       sortable: true },
    { key: 'email',      label: 'Email',      sortable: true },
    { key: 'region',     label: 'Region',     sortable: true, render: Badge },
    { key: 'created_at', label: 'Joined',     sortable: true },
  ]

  async function load() {
    loading = true
    const params = new URLSearchParams({
      skip: page * pageSize,
      limit: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
      ...(region && { region }),
    })
    const res = await apiFetch(`/customers/?${params}`)
    const data = await res.json()
    rows = data.items.map(r => ({
      ...r,
      created_at: new Date(r.created_at).toLocaleDateString(),
    }))
    total = data.total
    loading = false
  }

  onMount(load)

  function handleSort(key, order) { sortBy = key; sortOrder = order; page = 0; load() }
  function handlePage(p) { page = p; load() }
</script>

<div class="p-6 flex flex-col gap-4">
  <div class="flex items-center justify-between">
    <h2 class="text-lg font-semibold text-surface-900">Customers</h2>
    <select
      bind:value={region}
      on:change={() => { page = 0; load() }}
      class="text-sm border border-surface-200 rounded-mac px-3 py-1.5 text-surface-700 focus:outline-none focus:ring-2 focus:ring-accent"
    >
      <option value="">All Regions</option>
      <option>Northeast</option>
      <option>Southeast</option>
      <option>Midwest</option>
      <option>West</option>
    </select>
  </div>

  <Table
    {columns} {rows} {total} {page} {pageSize} {sortBy} {sortOrder} {loading}
    exportName="customers"
    onSort={handleSort}
    onPage={handlePage}
  />
</div>
