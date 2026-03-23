<script lang="ts">
  import { onMount } from 'svelte'
  import { apiFetch } from '../../lib/api'
  import StatCard from '../ui/StatCard.svelte'
  import BarChart from '../charts/BarChart.svelte'
  import LineChart from '../charts/LineChart.svelte'

  interface Summary {
    total_revenue: number
    total_orders: number
    total_customers: number
    total_products: number
    low_stock_count: number
  }

  interface StockProjection {
    product_id: number
    sku: string
    name: string
    stock_qty: number
    reorder_level: number
    avg_daily_sales: number
    days_until_stockout: number | null
    projected_stockout_date: string | null
    velocity_trend: 'accelerating' | 'steady' | 'slowing'
    is_low_stock: boolean
    computed_at: string
  }

  interface ChartPoint { label: string; value: number }
  interface RegionRow { region: string; revenue: number }
  interface MonthlyRow { month: string; revenue: number }

  const ICONS: Record<string, string> = {
    revenue:   'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    orders:    'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9h6',
    customers: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z',
    products:  'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4',
  }

  let summary: Summary | null = null
  let projections: StockProjection[] = []
  let regionData: ChartPoint[] = []
  let monthlyData: ChartPoint[] = []

  onMount(async () => {
    const [s, r, m, p] = await Promise.all([
      apiFetch('/reports/summary').then(res => res!.json()),
      apiFetch('/reports/sales/by-region').then(res => res!.json()),
      apiFetch('/reports/sales/monthly').then(res => res!.json()),
      apiFetch('/reports/inventory/projections').then(res => res!.json()),
    ])
    summary = s
    projections = p
    regionData = r.map((d: RegionRow) => ({ label: d.region, value: d.revenue }))
    monthlyData = m.map((d: MonthlyRow) => ({
      label: new Date(d.month).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
      value: d.revenue,
    }))
  })

  function fmt(n: number): string {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
  }

  function urgencyColor(days: number | null): string {
    if (days === null) return 'text-surface-400'
    if (days <= 7)  return 'text-rose-600'
    if (days <= 30) return 'text-amber-600'
    return 'text-emerald-600'
  }

  function urgencyBadge(item: StockProjection): { label: string; classes: string } {
    if (item.stock_qty === 0)        return { label: 'Out of stock',   classes: 'bg-rose-100 text-rose-600' }
    if (item.is_low_stock)           return { label: 'Low stock',      classes: 'bg-amber-100 text-amber-600' }
    if (item.days_until_stockout !== null && item.days_until_stockout <= 14)
                                     return { label: 'Running low',    classes: 'bg-orange-100 text-orange-600' }
    return { label: 'In stock', classes: 'bg-emerald-100 text-emerald-600' }
  }

  const TREND_ICON: Record<string, string> = {
    accelerating: '↑',
    slowing:      '↓',
    steady:       '→',
  }
  const TREND_COLOR: Record<string, string> = {
    accelerating: 'text-rose-500',
    slowing:      'text-emerald-500',
    steady:       'text-surface-400',
  }
</script>

<div class="p-8 flex flex-col gap-6">
  <div>
    <h2 class="text-xl font-bold text-surface-900">Dashboard</h2>
    <p class="text-sm text-surface-400 mt-0.5">Business overview</p>
  </div>

  {#if summary}
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard label="Total Revenue" value={fmt(summary.total_revenue)}               color="indigo" icon={ICONS.revenue}   />
      <StatCard label="Total Orders"  value={summary.total_orders.toLocaleString()}    color="violet" icon={ICONS.orders}    />
      <StatCard label="Customers"     value={summary.total_customers.toLocaleString()} color="teal"   icon={ICONS.customers} />
      <StatCard label="Products"      value={summary.total_products.toLocaleString()}  color="sky"    icon={ICONS.products}  />
    </div>
  {/if}

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
    <BarChart title="Revenue by Region" data={regionData} />
    <LineChart title="Monthly Revenue" data={monthlyData} />
  </div>

  {#if projections.length > 0}
    <div class="bg-white rounded-2xl border border-surface-200 overflow-hidden">
      <div class="px-5 py-4 border-b border-surface-100 flex items-center justify-between">
        <div>
          <h3 class="text-sm font-semibold text-surface-900">Inventory Projections</h3>
          <p class="text-xs text-surface-400 mt-0.5">
            Stockout forecast based on 30-day sales velocity · computed nightly by Airflow
          </p>
        </div>
        {#if summary && summary.low_stock_count > 0}
          <span class="text-xs font-semibold bg-rose-100 text-rose-600 rounded-full px-2.5 py-0.5">
            {summary.low_stock_count} below reorder
          </span>
        {/if}
      </div>
      <table class="w-full text-sm">
        <thead>
          <tr class="text-left text-xs text-surface-400 uppercase tracking-wider border-b border-surface-100">
            <th class="px-5 py-3 font-medium">Product</th>
            <th class="px-5 py-3 font-medium text-right">In Stock</th>
            <th class="px-5 py-3 font-medium text-right">Avg / Day</th>
            <th class="px-5 py-3 font-medium text-right">Days Left</th>
            <th class="px-5 py-3 font-medium text-right">Stockout</th>
            <th class="px-5 py-3 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {#each projections as item}
            {@const badge = urgencyBadge(item)}
            <tr class="border-b border-surface-50 last:border-0 hover:bg-surface-50 transition-colors">
              <td class="px-5 py-3">
                <div class="flex flex-col">
                  <span class="text-surface-800 font-medium">{item.name}</span>
                  <span class="text-xs font-mono text-surface-400">{item.sku}</span>
                </div>
              </td>
              <td class="px-5 py-3 text-right font-semibold
                {item.stock_qty === 0 ? 'text-rose-600' : item.is_low_stock ? 'text-amber-600' : 'text-surface-700'}">
                {item.stock_qty}
              </td>
              <td class="px-5 py-3 text-right text-surface-500">
                {item.avg_daily_sales.toFixed(1)}
                <span class="ml-1 font-semibold {TREND_COLOR[item.velocity_trend]}" title="{item.velocity_trend}">
                  {TREND_ICON[item.velocity_trend]}
                </span>
              </td>
              <td class="px-5 py-3 text-right font-semibold {urgencyColor(item.days_until_stockout)}">
                {item.days_until_stockout !== null ? item.days_until_stockout : '—'}
              </td>
              <td class="px-5 py-3 text-right text-surface-500">
                {#if item.projected_stockout_date}
                  {new Date(item.projected_stockout_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                {:else}
                  —
                {/if}
              </td>
              <td class="px-5 py-3">
                <span class="text-xs font-semibold {badge.classes} rounded-full px-2 py-0.5">
                  {badge.label}
                </span>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else}
    <div class="bg-white rounded-2xl border border-surface-200 px-5 py-8 text-center">
      <p class="text-sm font-medium text-surface-600">No projections yet</p>
      <p class="text-xs text-surface-400 mt-1">Trigger the <span class="font-mono">compute_stock_projections</span> DAG in Airflow to generate forecasts.</p>
    </div>
  {/if}
</div>
