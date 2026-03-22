<script lang="ts">
  export let value: string

  const colors: Record<string, string> = {
    Northeast:   'bg-indigo-100 text-indigo-700',
    Southeast:   'bg-emerald-100 text-emerald-700',
    Midwest:     'bg-amber-100 text-amber-700',
    West:        'bg-violet-100 text-violet-700',
    Electronics: 'bg-blue-100 text-blue-700',
    Office:      'bg-orange-100 text-orange-700',
    Supplies:    'bg-teal-100 text-teal-700',
    admin:       'bg-rose-100 text-rose-700',
    viewer:      'bg-surface-100 text-surface-500',
  }

  $: cls = colors[value] ?? 'bg-surface-100 text-surface-500'
</script>

<span class="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold {cls}">{value}</span>
