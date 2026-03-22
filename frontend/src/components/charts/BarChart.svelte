<script lang="ts">
  import { onMount, onDestroy } from 'svelte'
  import { Chart } from 'chart.js/auto'

  interface ChartPoint { label: string; value: number }

  export let data: ChartPoint[] = []
  export let title: string = ''

  let canvas: HTMLCanvasElement
  let chart: Chart | undefined

  $: if (chart && data.length) {
    chart.data.labels = data.map(d => d.label)
    chart.data.datasets[0].data = data.map(d => d.value)
    chart.update()
  }

  onMount(() => {
    chart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: data.map(d => d.label),
        datasets: [{
          data: data.map(d => d.value),
          backgroundColor: 'rgba(99, 102, 241, 0.85)',
          hoverBackgroundColor: 'rgba(99, 102, 241, 1)',
          borderRadius: 6,
          borderSkipped: false,
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          title: { display: false },
        },
        scales: {
          x: { grid: { display: false }, border: { display: false }, ticks: { color: '#94a3b8' } },
          y: { grid: { color: '#f1f5f9' }, border: { display: false }, ticks: { color: '#94a3b8' } },
        },
      },
    })
  })

  onDestroy(() => chart?.destroy())
</script>

<div class="bg-white rounded-2xl border border-surface-100 shadow-sm p-6">
  {#if title}
    <p class="text-sm font-semibold text-surface-700 mb-5">{title}</p>
  {/if}
  <canvas bind:this={canvas}></canvas>
</div>
