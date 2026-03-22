<script>
  import { onMount } from 'svelte'
  import { apiFetch } from '../../lib/api'
  import StatCard from '../ui/StatCard.svelte'
  import BarChart from '../charts/BarChart.svelte'
  import LineChart from '../charts/LineChart.svelte'

  const ICONS = {
    revenue:   'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    orders:    'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9h6',
    customers: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z',
    stock:     'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
  }

  let summary = null
  let regionData = []
  let monthlyData = []

  onMount(async () => {
    const [s, r, m] = await Promise.all([
      apiFetch('/reports/summary').then(r => r.json()),
      apiFetch('/reports/sales/by-region').then(r => r.json()),
      apiFetch('/reports/sales/monthly').then(r => r.json()),
    ])
    summary = s
    regionData = r.map(d => ({ label: d.region, value: d.revenue }))
    monthlyData = m.map(d => ({
      label: new Date(d.month).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
      value: d.revenue,
    }))
  })

  function fmt(n) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
  }
</script>

<div class="p-8 flex flex-col gap-6">
  <div>
    <h2 class="text-xl font-bold text-surface-900">Dashboard</h2>
    <p class="text-sm text-surface-400 mt-0.5">Business overview</p>
  </div>

  {#if summary}
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard label="Total Revenue"    value={fmt(summary.total_revenue)}              color="indigo" icon={ICONS.revenue}   />
      <StatCard label="Total Orders"     value={summary.total_orders.toLocaleString()}   color="violet" icon={ICONS.orders}    />
      <StatCard label="Customers"        value={summary.total_customers.toLocaleString()} color="teal"  icon={ICONS.customers} />
      <StatCard label="Low Stock Items"  value={summary.low_stock_count}                 color="rose"   icon={ICONS.stock} sub="at or below reorder level" />
    </div>
  {/if}

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
    <BarChart title="Revenue by Region" data={regionData} />
    <LineChart title="Monthly Revenue" data={monthlyData} />
  </div>
</div>
