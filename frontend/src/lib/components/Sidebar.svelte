<script lang="ts">
  import { ui, loadSets, selectSet, toast } from '../stores.svelte'
  import { api } from '../api'
  import type { IconSet } from '../types'

  let importing = $state<string | null>(null)
  let prog = $state({ percent: 0, message: '', completed: 0, failed: 0 })

  const filtered = $derived(
    ui.licenseFilter ? ui.sets.filter((s) => s.license_category === ui.licenseFilter) : ui.sets,
  )
  const downloaded = $derived(filtered.filter((s) => s.downloaded))
  const available = $derived(filtered.filter((s) => !s.downloaded))

  function badgeClass(s: IconSet) {
    return s.license_category === 'attribution'
      ? 'lic-attribution'
      : s.license_category === 'none'
        ? 'lic-none'
        : 'lic-permissive'
  }

  async function startImport(id: string) {
    importing = id
    prog = { percent: 0, message: 'Start…', completed: 0, failed: 0 }
    await api.downloadSet(id)
    const timer = setInterval(async () => {
      try {
        const p = await api.progress(id)
        prog = { percent: p.percent, message: p.message, completed: p.completed, failed: p.failed }
        if (p.status === 'completed' || p.status === 'error') {
          clearInterval(timer)
          importing = null
          await loadSets()
          toast(
            p.status === 'completed' ? `${p.completed} Icons geladen` : 'Import fehlgeschlagen',
            p.status === 'completed' ? 'success' : 'error',
          )
        }
      } catch {
        /* weiter pollen */
      }
    }, 600)
  }

  async function reimport(id: string, name: string) {
    if (!confirm(`"${name}" neu importieren? Vorhandene Dateien werden ersetzt.`)) return
    await api.deleteSet(id)
    startImport(id)
  }
  async function del(id: string, name: string) {
    if (!confirm(`"${name}" wirklich löschen?`)) return
    await api.deleteSet(id)
    if (ui.activeSetId === id) ui.activeSetId = null
    await loadSets()
  }
</script>

<div class="sidebar">
  <select class="license-filter" bind:value={ui.licenseFilter}>
    <option value="">Alle Lizenzen</option>
    <option value="permissive">Frei nutzbar</option>
    <option value="attribution">Namensnennung nötig</option>
    <option value="none">Ohne Lizenz</option>
  </select>

  {#if importing}
    <div class="progress">
      <div class="progress-text">Importiere {importing} … {prog.completed}</div>
      <div class="progress-track"><div class="progress-fill" style="width:{prog.percent}%"></div></div>
      <div class="progress-text">{prog.message}</div>
    </div>
  {/if}

  {#if downloaded.length}
    <div class="sidebar-title">Geladen</div>
    {#each downloaded as s (s.id)}
      <div
        class="set-item"
        class:active={ui.activeSetId === s.id}
        role="button"
        tabindex="0"
        onclick={() => selectSet(s.id)}
        onkeydown={(e) => e.key === 'Enter' && selectSet(s.id)}
      >
        <div class="set-info">
          <div class="set-name">{s.name}</div>
          <div class="set-meta">
            <span class="set-count">{s.icon_count} Icons</span>
            <span class="license-badge {badgeClass(s)}">{s.license_spdx || s.license}</span>
          </div>
        </div>
        {#if s.is_custom}
          <button class="set-btn" title="Löschen" onclick={(e) => { e.stopPropagation(); del(s.id, s.name) }}>×</button>
        {:else}
          <button class="set-btn" title="Neu importieren" onclick={(e) => { e.stopPropagation(); reimport(s.id, s.name) }}>↻</button>
        {/if}
      </div>
    {/each}
  {/if}

  {#if available.length}
    <div class="sidebar-title">Verfügbar</div>
    {#each available as s (s.id)}
      <div class="set-item">
        <div class="set-info">
          <div class="set-name">{s.name}</div>
          <div class="set-meta">
            <span class="set-count">~{s.estimated_count}</span>
            <span class="license-badge {badgeClass(s)}">{s.license_spdx || s.license}</span>
          </div>
        </div>
        <button class="set-btn" title="Herunterladen" onclick={() => startImport(s.id)}>↓</button>
      </div>
    {/each}
  {/if}
</div>
