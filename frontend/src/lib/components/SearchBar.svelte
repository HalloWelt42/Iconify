<script lang="ts">
  import { ui, runSearch } from '../stores.svelte'

  let timer: ReturnType<typeof setTimeout> | undefined

  function oninput(e: Event) {
    ui.query = (e.target as HTMLInputElement).value
    clearTimeout(timer)
    timer = setTimeout(() => runSearch(false), 250)
  }
</script>

<div class="searchbar">
  <span class="sb-icon">⌕</span>
  <input type="text" placeholder="Icons suchen…" value={ui.query} {oninput} />
</div>
