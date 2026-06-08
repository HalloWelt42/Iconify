<script lang="ts">
  import { ui, toggleCart, clearCart, toast } from '../stores.svelte'
  import { api } from '../api'

  let fontName = $state('meine-icons')
  let busy = $state(false)

  async function genFont() {
    if (!ui.cart.length) return
    busy = true
    try {
      const r = await api.generateFont(
        ui.cart.map((c) => ({ set_id: c.set_id, name: c.name, style: c.style })),
        fontName,
      )
      if (r.success) {
        window.location.href = r.download_url
        toast('Font erzeugt', 'success')
      } else {
        toast(r.error || 'Font-Generierung fehlgeschlagen', 'error')
      }
    } catch {
      toast('Font-Generierung fehlgeschlagen', 'error')
    } finally {
      busy = false
    }
  }
</script>

<div class="cart">
  <h3>Arbeits-Set <span class="cart-n">{ui.cart.length}</span></h3>

  {#if ui.cart.length === 0}
    <p class="hint">
      Icons über das <strong>+</strong> auf den Kacheln sammeln, dann z.&nbsp;B. einen Icon-Font
      erzeugen. Drag&amp;Drop und weitere Aktionen (ZIP, Sprite, als eigenes Set speichern) folgen in R2.
    </p>
  {:else}
    <div class="cart-actions">
      <input class="cart-name" bind:value={fontName} placeholder="Font-Name" />
      <button class="btn btn-primary block" disabled={busy} onclick={genFont}>
        {busy ? '…' : 'Font generieren'}
      </button>
      <button class="btn btn-secondary block" onclick={clearCart}>Leeren</button>
    </div>
    <div class="cart-list">
      {#each ui.cart as c (c.path)}
        <div class="cart-item">
          <img src={api.svgUrl(c)} alt={c.name} />
          <span class="cart-item-nm" title={c.name}>{c.name}</span>
          <button class="set-btn" title="Entfernen" onclick={() => toggleCart(c)}>×</button>
        </div>
      {/each}
    </div>
  {/if}
</div>
