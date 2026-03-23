<script>
  import { onMount } from 'svelte'
  import { apiFetch } from '../../lib/api'
  import StatCard from '../ui/StatCard.svelte'
  import BarChart from '../charts/BarChart.svelte'
  import LineChart from '../charts/LineChart.svelte'

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

<div class="p-6 flex flex-col gap-6">
  <h2 class="text-lg font-semibold text-surface-900">Dashboard</h2>

  {#if summary}
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard label="Total Revenue" value={fmt(summary.total_revenue)} />
      <StatCard label="Total Orders" value={summary.total_orders.toLocaleString()} />
      <StatCard label="Customers" value={summary.total_customers.toLocaleString()} />
      <StatCard label="Low Stock Items" value={summary.low_stock_count} sub="at or below reorder level" />
    </div>
  {/if}

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
    <BarChart title="Revenue by Region" data={regionData} />
    <LineChart title="Monthly Revenue" data={monthlyData} />
  </div>
</div>
