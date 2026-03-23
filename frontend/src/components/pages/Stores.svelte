<script lang="ts">
  import { onMount } from 'svelte'
  import { apiFetch } from '../../lib/api'

  interface StoreSummary {
    id: number
    name: string
    city: string
    region: string
    total_products: number
    low_stock_count: number
  }

  interface StoreStockItem {
    product_id: number
    sku: string
    name: string
    category: string
    qty_on_hand: number
    reorder_level: number
    is_low_stock: boolean
    updated_at: string
  }

  interface StoreDetail {
    id: number
    name: string
    city: string
    region: string
    inventory: StoreStockItem[]
  }

  interface PagedResponse { items: StoreSummary[]; total: number }

  let stores: StoreSummary[] = []
  let total: number = 0
  let loading: boolean = false
  let page: number = 0
  let pageSize: number = 25
  let search: string = ''
  let region: string = ''
  let lowStockOnly: boolean = false

  let selectedStore: StoreDetail | null = null
  let detailLoading: boolean = false
  let searchInput: string = ''
  let searchTimeout: ReturnType<typeof setTimeout>

  async function load() {
    loading = true
    const params = new URLSearchParams({
      skip: String(page * pageSize),
      limit: String(pageSize),
      ...(region && { region }),
      ...(search && { search }),
      ...(lowStockOnly && { low_stock_only: 'true' }),
    })
    const res = await apiFetch(`/stores/?${params}`)
    const data: PagedResponse = await res!.json()
    stores = data.items
    total = data.total
    loading = false
  }

  async function openStore(id: number) {
    detailLoading = true
    selectedStore = null
    const res = await apiFetch(`/stores/${id}`)
    selectedStore = await res!.json()
    detailLoading = false
  }

  function handleSearchInput() {
    clearTimeout(searchTimeout)
    searchTimeout = setTimeout(() => { search = searchInput; page = 0; load() }, 300)
  }

  onMount(load)

  const regionOptions = ['Northeast', 'Southeast', 'Midwest', 'West']

  const totalPages = () => Math.ceil(total / pageSize)
</script>

<div class="p-8 flex gap-6">
  <!-- Store list -->
  <div class="flex-1 flex flex-col gap-4 min-w-0">
    <div class="flex items-start justify-between gap-3">
      <div>
        <h2 class="text-xl font-bold text-surface-900">Stores</h2>
        <p class="text-sm text-surface-400 mt-0.5">{total} locations</p>
      </div>

      <div class="flex items-center gap-2">
        <input
          type="text"
          placeholder="Search name or city…"
          bind:value={searchInput}
          on:input={handleSearchInput}
          class="text-sm border border-surface-200 rounded-xl px-3 py-2 text-surface-700 focus:outline-none focus:ring-2 focus:ring-indigo-400 w-48"
        />

        <select
          bind:value={region}
          on:change={() => { page = 0; load() }}
          class="text-sm border border-surface-200 rounded-xl px-3 py-2 text-surface-700 focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white"
        >
          <option value="">All Regions</option>
          {#each regionOptions as r}
            <option>{r}</option>
          {/each}
        </select>

        <label class="flex items-center gap-1.5 text-sm text-surface-600 cursor-pointer select-none">
          <input
            type="checkbox"
            bind:checked={lowStockOnly}
            on:change={() => { page = 0; load() }}
            class="rounded accent-rose-500"
          />
          Low stock only
        </label>
      </div>
    </div>

    {#if loading}
      <div class="text-sm text-surface-400 py-8 text-center">Loading…</div>
    {:else if stores.length === 0}
      <div class="text-sm text-surface-400 py-8 text-center">No stores found.</div>
    {:else}
      <div class="flex flex-col gap-2">
        {#each stores as store}
          <button
            on:click={() => openStore(store.id)}
            class="w-full text-left bg-white border border-surface-100 rounded-2xl px-5 py-4 hover:border-indigo-200 hover:shadow-sm transition-all
              {selectedStore?.id === store.id ? 'border-indigo-400 shadow-md' : ''}"
          >
            <div class="flex items-center justify-between">
              <div>
                <p class="font-semibold text-surface-900 text-sm">{store.name}</p>
                <p class="text-xs text-surface-400 mt-0.5">{store.city} · {store.region}</p>
              </div>
              <div class="flex items-center gap-3">
                <span class="text-xs text-surface-400">{store.total_products} products</span>
                {#if store.low_stock_count > 0}
                  <span class="text-xs font-semibold bg-rose-50 text-rose-600 border border-rose-100 px-2 py-0.5 rounded-full">
                    {store.low_stock_count} low stock
                  </span>
                {:else}
                  <span class="text-xs font-semibold bg-emerald-50 text-emerald-600 border border-emerald-100 px-2 py-0.5 rounded-full">
                    All stocked
                  </span>
                {/if}
              </div>
            </div>
          </button>
        {/each}
      </div>

      {#if totalPages() > 1}
        <div class="flex items-center justify-between pt-2">
          <p class="text-xs text-surface-400">
            {page * pageSize + 1}–{Math.min((page + 1) * pageSize, total)} of {total}
          </p>
          <div class="flex gap-1">
            <button
              disabled={page === 0}
              on:click={() => { page--; load() }}
              class="px-3 py-1.5 text-xs rounded-lg border border-surface-200 text-surface-600 disabled:opacity-40 hover:bg-surface-50"
            >← Prev</button>
            <button
              disabled={page >= totalPages() - 1}
              on:click={() => { page++; load() }}
              class="px-3 py-1.5 text-xs rounded-lg border border-surface-200 text-surface-600 disabled:opacity-40 hover:bg-surface-50"
            >Next →</button>
          </div>
        </div>
      {/if}
    {/if}
  </div>

  <!-- Store detail panel -->
  {#if selectedStore || detailLoading}
    <div class="w-96 shrink-0 flex flex-col gap-4">
      {#if detailLoading}
        <div class="bg-white border border-surface-100 rounded-2xl p-6 text-sm text-surface-400">Loading…</div>
      {:else if selectedStore}
        <div class="bg-white border border-surface-100 rounded-2xl p-5 flex flex-col gap-4">
          <div class="flex items-start justify-between">
            <div>
              <h3 class="font-bold text-surface-900">{selectedStore.name}</h3>
              <p class="text-xs text-surface-400 mt-0.5">{selectedStore.city} · {selectedStore.region}</p>
            </div>
            <button
              on:click={() => selectedStore = null}
              class="text-surface-300 hover:text-surface-600 transition-colors text-lg leading-none"
            >✕</button>
          </div>

          <div class="flex flex-col gap-1">
            {#each selectedStore.inventory as item}
              <div class="flex items-center justify-between py-2 border-b border-surface-50 last:border-0">
                <div class="min-w-0 flex-1 pr-3">
                  <p class="text-xs font-medium text-surface-800 truncate">{item.name}</p>
                  <p class="text-xs text-surface-400">{item.sku} · {item.category}</p>
                </div>
                <div class="text-right shrink-0">
                  <p class="text-xs font-semibold {item.is_low_stock ? 'text-rose-600' : 'text-surface-700'}">
                    {item.qty_on_hand}
                  </p>
                  <p class="text-xs text-surface-300">/{item.reorder_level} min</p>
                </div>
                {#if item.is_low_stock}
                  <span class="ml-2 w-1.5 h-1.5 rounded-full bg-rose-400 shrink-0"></span>
                {:else}
                  <span class="ml-2 w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0"></span>
                {/if}
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>
