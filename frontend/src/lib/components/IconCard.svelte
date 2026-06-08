<script lang="ts">
  import type { Icon } from '../types'
  import { ui } from '../stores.svelte'
  import { api } from '../api'

  let { icon, showSet = false }: { icon: Icon; showSet?: boolean } = $props()
  const selected = $derived(ui.selected?.path === icon.path)
</script>

<button class="icon-card" class:selected title={icon.name} onclick={() => (ui.selected = icon)}>
  <img src={api.svgUrl(icon)} alt={icon.name} loading="lazy" />
  <span class="nm">{icon.name}</span>
  {#if showSet}<span class="set-tag">{icon.set_id}</span>{/if}
</button>
