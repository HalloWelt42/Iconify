<script lang="ts">
  import { ui } from '../stores.svelte'
</script>

<div class="toasts">
  {#each ui.toasts as t (t.id)}
    <div class="toast {t.type}">{t.msg}</div>
  {/each}
</div>
