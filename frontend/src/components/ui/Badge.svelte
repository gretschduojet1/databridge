<script>
  export let value

  const colors = {
    Northeast: 'bg-blue-50 text-blue-700',
    Southeast: 'bg-green-50 text-green-700',
    Midwest:   'bg-yellow-50 text-yellow-700',
    West:      'bg-purple-50 text-purple-700',
    Electronics: 'bg-blue-50 text-blue-700',
    Office:      'bg-orange-50 text-orange-700',
    Supplies:    'bg-gray-100 text-gray-600',
    admin:       'bg-red-50 text-red-700',
    viewer:      'bg-surface-100 text-surface-500',
  }

  $: cls = colors[value] ?? 'bg-surface-100 text-surface-500'
</script>

<span class="inline-block px-2 py-0.5 rounded text-xs font-medium {cls}">{value}</span>
