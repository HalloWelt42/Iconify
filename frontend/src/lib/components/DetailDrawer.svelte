<script lang="ts">
  import { ui, toast } from '../stores.svelte'
  import { api } from '../api'
  import type { IconCode } from '../types'

  type Tab = 'svg' | 'img' | 'font' | 'css'
  const presets = [16, 24, 32, 48, 64, 128, 256]

  let size = $state(ui.settings.size || 128)
  let color = $state('#000000')
  let tab = $state<Tab>('svg')
  let code = $state<IconCode | null>(null)

  const icon = $derived(ui.selected!)

  async function load() {
    if (!ui.selected) return
    try {
      code = await api.code(ui.selected.set_id, ui.selected.name, {
        style: ui.selected.style,
        size,
        color,
      })
    } catch {
      code = null
    }
  }
  $effect(() => {
    load()
  })

  const snippet = $derived(
    tab === 'svg'
      ? code?.svg ?? ''
      : tab === 'img'
        ? code?.img ?? ''
        : tab === 'font'
          ? code?.font_html ?? ''
          : code?.font_css ?? '',
  )

  function close() {
    ui.selected = null
  }
  async function copy() {
    try {
      await navigator.clipboard.writeText(snippet)
      toast('Kopiert', 'success')
    } catch {
      toast('Kopieren fehlgeschlagen', 'error')
    }
  }
  function download() {
    const a = document.createElement('a')
    a.href = api.svgUrl(icon)
    a.download = `${icon.name}.svg`
    a.click()
  }
</script>

<svelte:window onkeydown={(e) => e.key === 'Escape' && close()} />

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="drawer-overlay" role="presentation" onclick={(e) => { if (e.target === e.currentTarget) close() }}>
  <div class="drawer" role="dialog" aria-modal="true" tabindex="-1">
    <div class="drawer-head">
      <h2>{icon.name}</h2>
      <button class="icon-btn" onclick={close} aria-label="Schließen">✕</button>
    </div>
    <div class="drawer-body">
      <div class="preview">
        {#if code?.svg}
          <!-- eslint-disable-next-line svelte/no-at-html-tags -->
          {@html code.svg}
        {:else}
          <img src={api.svgUrl(icon)} alt={icon.name} style="width:{size}px;height:{size}px" />
        {/if}
      </div>

      <div class="control">
        <div class="control-label"><span>Größe</span><span>{size}px</span></div>
        <input type="range" min="16" max="512" bind:value={size} />
        <div class="size-presets">
          {#each presets as p}
            <button class:active={size === p} onclick={() => (size = p)}>{p}</button>
          {/each}
        </div>
      </div>

      <div class="control">
        <div class="control-label"><span>Farbe</span><span>{color}</span></div>
        <input type="color" bind:value={color} />
      </div>

      {#if code}
        <div class="panel-license">
          Lizenz:
          {#if code.license_url}
            <a href={code.license_url} target="_blank" rel="noopener">{code.license}</a>
          {:else}{code.license}{/if}
        </div>
        {#if code.requires_attribution && code.attribution}
          <div class="attribution">⚠ {code.attribution}</div>
        {/if}
      {/if}

      <div class="code-tabs">
        {#each ['svg', 'img', 'font', 'css'] as const as t}
          <button class="code-tab" class:active={tab === t} onclick={() => (tab = t)}>{t.toUpperCase()}</button>
        {/each}
      </div>
      <div class="code-block">
        <button class="copy-btn" onclick={copy}>Kopieren</button>
        <pre>{snippet || '— nicht verfügbar —'}</pre>
      </div>
    </div>
    <div class="drawer-actions">
      <button class="btn btn-primary block" onclick={download}>SVG herunterladen</button>
      <button class="btn btn-secondary block" onclick={copy}>Code kopieren</button>
    </div>
  </div>
</div>
