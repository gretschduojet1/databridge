<script lang="ts">
  type ColorKey = 'indigo' | 'violet' | 'teal' | 'rose' | 'amber'
  interface PaletteEntry { wrap: string; icon: string }

  export let label: string
  export let value: string | number
  export let sub: string | null = null
  export let color: ColorKey = 'indigo'
  export let icon: string | null = null

  const palette: Record<ColorKey, PaletteEntry> = {
    indigo: { wrap: 'bg-indigo-50',  icon: 'text-indigo-500' },
    violet: { wrap: 'bg-violet-50',  icon: 'text-violet-500' },
    teal:   { wrap: 'bg-teal-50',    icon: 'text-teal-500'   },
    rose:   { wrap: 'bg-rose-50',    icon: 'text-rose-500'   },
    amber:  { wrap: 'bg-amber-50',   icon: 'text-amber-500'  },
  }

  $: p = palette[color] ?? palette.indigo
</script>

<div class="bg-white rounded-2xl border border-surface-100 shadow-sm p-6">
  {#if icon}
    <div class="{p.wrap} rounded-xl p-2.5 inline-flex mb-4">
      <svg class="w-5 h-5 {p.icon}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75">
        <path stroke-linecap="round" stroke-linejoin="round" d={icon} />
      </svg>
    </div>
  {/if}
  <p class="text-3xl font-bold text-surface-900 mb-1">{value}</p>
  <p class="text-sm font-medium text-surface-500">{label}</p>
  {#if sub}
    <p class="text-xs text-surface-400 mt-1">{sub}</p>
  {/if}
</div>
