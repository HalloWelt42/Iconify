<script lang="ts">
  import type { Icon } from '../types'
  import { ui, toggleCart, inCart } from '../stores.svelte'
  import { api } from '../api'

  let { icon, showSet = false }: { icon: Icon; showSet?: boolean } = $props()
  const selected = $derived(ui.selected?.path === icon.path)
  const carted = $derived(inCart(icon))

  function open() {
    ui.selected = icon
  }
</script>

<div
  class="icon-card"
  class:selected
  role="button"
  tabindex="0"
  title={icon.name}
  onclick={open}
  onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), open())}
>
  <button
    class="card-add"
    class:on={carted}
    title={carted ? 'Aus Arbeits-Set entfernen' : 'Zum Arbeits-Set'}
    onclick={(e) => {
      e.stopPropagation()
      toggleCart(icon)
    }}
  >{carted ? '✓' : '+'}</button>
  <img src={api.svgUrl(icon)} alt={icon.name} loading="lazy" />
  <span class="nm">{icon.name}</span>
  {#if showSet}<span class="set-tag">{icon.set_id}</span>{/if}
</div>
