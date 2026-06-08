<script lang="ts">
  import { onMount } from 'svelte'
  import { ui, loadSets, saveSettings } from './lib/stores.svelte'
  import { api } from './lib/api'
  import Sidebar from './lib/components/Sidebar.svelte'
  import SearchBar from './lib/components/SearchBar.svelte'
  import ResultGrid from './lib/components/ResultGrid.svelte'
  import DetailDrawer from './lib/components/DetailDrawer.svelte'
  import Cart from './lib/components/Cart.svelte'
  import Toasts from './lib/components/Toasts.svelte'

  let version = $state('')

  function applyTheme() {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const dark = ui.settings.theme === 'dark' || (ui.settings.theme === 'auto' && prefersDark)
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
  }

  function toggleTheme() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark'
    ui.settings.theme = isDark ? 'light' : 'dark'
    applyTheme()
    saveSettings()
  }

  onMount(async () => {
    applyTheme()
    await loadSets()
    try {
      version = (await api.health()).version
    } catch {
      /* Backend evtl. offline – egal */
    }
  })
</script>

<header class="app-bar">
  <div class="brand">
    <span class="logo">◆</span> Iconify
    {#if version}<span class="version">v{version}</span>{/if}
  </div>
  <SearchBar />
  <div class="app-bar-actions">
    <button class="icon-btn" title="Hell/Dunkel" onclick={toggleTheme}>◐</button>
  </div>
</header>

<div class="workspace">
  <aside class="zone zone-left"><Sidebar /></aside>
  <main class="zone-center"><ResultGrid /></main>
  <aside class="zone zone-right"><Cart /></aside>
</div>

{#if ui.selected}
  <DetailDrawer />
{/if}

<Toasts />
