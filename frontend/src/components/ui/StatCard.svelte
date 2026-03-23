<script>
  export let label
  export let value
  export let sub = null
</script>

<div class="bg-white rounded-mac border border-surface-100 shadow-sm px-6 py-5">
  <p class="text-xs font-medium text-surface-400 uppercase tracking-wide mb-1">{label}</p>
  <p class="text-2xl font-semibold text-surface-900">{value}</p>
  {#if sub}
    <p class="text-xs text-surface-400 mt-1">{sub}</p>
  {/if}
</div>
