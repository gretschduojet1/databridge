<script>
  import { onMount, onDestroy } from 'svelte'
  import { Chart } from 'chart.js/auto'

  export let data = []   // [{ label, value }]
  export let title = ''

  let canvas
  let chart

  $: if (chart && data.length) {
    chart.data.labels = data.map(d => d.label)
    chart.data.datasets[0].data = data.map(d => d.value)
    chart.update()
  }

  onMount(() => {
    chart = new Chart(canvas, {
      type: 'line',
      data: {
        labels: data.map(d => d.label),
        datasets: [{
          data: data.map(d => d.value),
          borderColor: '#0071e3',
          backgroundColor: 'rgba(0, 113, 227, 0.06)',
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: '#0071e3',
          fill: true,
          tension: 0.3,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, border: { display: false } },
          y: { grid: { color: '#f5f5f7' }, border: { display: false } },
        },
      },
    })
  })

  onDestroy(() => chart?.destroy())
</script>

<div class="bg-white rounded-mac border border-surface-100 shadow-sm p-5">
  {#if title}
    <p class="text-xs font-medium text-surface-400 uppercase tracking-wide mb-4">{title}</p>
  {/if}
  <canvas bind:this={canvas}></canvas>
</div>
