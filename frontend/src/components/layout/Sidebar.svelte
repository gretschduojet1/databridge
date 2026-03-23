<script>
  export let current = 'dashboard'
  export let onNavigate = () => {}

  const links = [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'customers', label: 'Customers' },
    { key: 'products',  label: 'Products'  },
    { key: 'orders',    label: 'Orders'    },
  ]
</script>

<aside class="w-52 shrink-0 bg-white border-r border-surface-100 min-h-screen flex flex-col">
  <div class="px-5 py-5 border-b border-surface-100">
    <span class="text-base font-semibold text-surface-900">Databridge</span>
  </div>

  <nav class="flex flex-col gap-0.5 p-3 flex-1">
    {#each links as link}
      <button
        on:click={() => onNavigate(link.key)}
        class="w-full text-left px-3 py-2 rounded-lg text-sm transition-colors
          {current === link.key
            ? 'bg-surface-100 text-surface-900 font-medium'
            : 'text-surface-500 hover:bg-surface-50 hover:text-surface-700'}"
      >
        {link.label}
      </button>
    {/each}
  </nav>
</aside>
