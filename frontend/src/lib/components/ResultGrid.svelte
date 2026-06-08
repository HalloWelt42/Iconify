<script lang="ts">
  import { ui, runSearch, loadMore, activeSet, saveSettings, toast } from '../stores.svelte'
  import { api } from '../api'
  import IconCard from './IconCard.svelte'

  let sentinel = $state<HTMLDivElement | null>(null)
  let dragging = $state(false)
  let fileInput = $state<HTMLInputElement | null>(null)

  const isCustom = $derived(activeSet()?.is_custom ?? false)

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

  async function uploadFiles(files: FileList | null) {
    const set = activeSet()
    if (!set || !files?.length) return
    const arr = Array.from(files).filter((f) => f.name.toLowerCase().endsWith('.svg'))
    if (!arr.length) {
      toast('Nur SVG-Dateien', 'error')
      return
    }
    try {
      const r = await api.uploadIcons(set.id, arr)
      toast(`${r.count} Icon(s) hochgeladen`, r.count ? 'success' : 'error')
      runSearch(false)
    } catch {
      toast('Upload fehlgeschlagen', 'error')
    }
  }

  function onDrop(e: DragEvent) {
    e.preventDefault()
    dragging = false
    if (isCustom) uploadFiles(e.dataTransfer?.files ?? null)
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

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
  class="grid-scroll"
  class:dropping={dragging && isCustom}
  ondragover={(e) => {
    if (isCustom) {
      e.preventDefault()
      dragging = true
    }
  }}
  ondragleave={() => (dragging = false)}
  ondrop={onDrop}
>
  {#if !activeSet()}
    <div class="grid-empty">Wähle links ein Icon-Set – oder importiere eins.</div>
  {:else if isCustom && ui.results.length === 0 && !ui.loading}
    <div class="grid-empty">
      <p>Noch keine Icons. SVG-Dateien hierher ziehen oder hochladen.</p>
      <button class="btn btn-primary" onclick={() => fileInput?.click()}>SVG hochladen</button>
    </div>
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

  {#if dragging && isCustom}
    <div class="dropzone-hint">SVG-Dateien ablegen…</div>
  {/if}
</div>

<input
  bind:this={fileInput}
  type="file"
  accept=".svg"
  multiple
  style="display:none"
  onchange={(e) => uploadFiles((e.target as HTMLInputElement).files)}
/>
