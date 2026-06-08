<script lang="ts">
  import { ui, runSearch, loadMore, activeSet, saveSettings } from '../stores.svelte'
  import IconCard from './IconCard.svelte'

  let sentinel = $state<HTMLDivElement | null>(null)

  $effect(() => {
    const el = sentinel
    if (!el) return
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) loadMore()
      },
      { rootMargin: '400px' },
    )
    obs.observe(el)
    return () => obs.disconnect()
  })

  function setStyle(s: string) {
    ui.activeStyle = s
    runSearch(false)
  }
  function setGridTheme(t: 'light' | 'dark') {
    ui.settings.gridTheme = t
    saveSettings()
  }
</script>

<div class="grid-toolbar">
  <span class="count">{ui.total} Icons</span>
  {#if ui.styles.length > 1}
    <div class="style-tabs">
      <button class="style-tab" class:active={ui.activeStyle === ''} onclick={() => setStyle('')}>Alle</button>
      {#each ui.styles as s}
        <button class="style-tab" class:active={ui.activeStyle === s} onclick={() => setStyle(s)}>{s}</button>
      {/each}
    </div>
  {/if}
  <div class="seg" title="Vorschau-Hintergrund">
    <button class:active={ui.settings.gridTheme === 'light'} onclick={() => setGridTheme('light')}>Hell</button>
    <button class:active={ui.settings.gridTheme === 'dark'} onclick={() => setGridTheme('dark')}>Dunkel</button>
  </div>
</div>

<div class="grid-scroll">
  {#if !activeSet()}
    <div class="grid-empty">Wähle links ein Icon-Set – oder importiere eins.</div>
  {:else if ui.results.length === 0 && !ui.loading}
    <div class="grid-empty">Keine Icons gefunden.</div>
  {:else}
    <div class="icon-grid" class:grid-dark={ui.settings.gridTheme === 'dark'}>
      {#each ui.results as icon (icon.path)}
        <IconCard {icon} />
      {/each}
    </div>
    <div class="sentinel" bind:this={sentinel}></div>
  {/if}
</div>
