'use strict'
const $ = (s) => document.querySelector(s)
const $$ = (s) => [...document.querySelectorAll(s)]
const app = $('#app'), root = document.documentElement

// ---- UI-Icons (Inline-SVG, keine fremde Icon-Schrift) ----
const UI = {
  copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>',
  expand: '<path d="M8 3H5a2 2 0 0 0-2 2v3M16 3h3a2 2 0 0 1 2 2v3M8 21H5a2 2 0 0 1-2-2v-3M16 21h3a2 2 0 0 0 2-2v-3"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.4 1.4M17.2 17.2l1.4 1.4M18.6 5.4l-1.4 1.4M6.8 17.2l-1.4 1.4"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/>',
  close: '<path d="M18 6L6 18M6 6l12 12"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  down: '<path d="M12 4v12M6 12l6 6 6-6"/>',
}
const uisvg = (k, w = 18) => `<svg viewBox="0 0 24 24" width="${w}" height="${w}" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${UI[k]}</svg>`
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))

// ---- API ----
const api = {
  async sets() { return (await fetch('/api/sets')).json() },
  async search(p) {
    const qs = new URLSearchParams({ set_id: p.set_id || '', q: p.q || '', style: p.style || '', scope: p.scope || 'set', license: p.license || '', page: p.page || 1, per_page: 120 })
    return (await fetch('/api/icons/search?' + qs)).json()
  },
  async code(setId, name, style, size, color) {
    const qs = new URLSearchParams({ style: style || '', size, color })
    return (await fetch(`/api/icons/${encodeURIComponent(setId)}/${encodeURIComponent(name)}/code?` + qs)).json()
  },
  async health() { return (await fetch('/health')).json() },
}

// ---- Material-Palette ----
const HUES = [['#FFCDD2','#E57373','#F44336','#D32F2F','#B71C1C'],['#F8BBD0','#F06292','#E91E63','#C2185B','#880E4F'],['#E1BEE7','#BA68C8','#9C27B0','#7B1FA2','#4A148C'],['#C5CAE9','#7986CB','#3F51B5','#303F9F','#1A237E'],['#BBDEFB','#64B5F6','#2196F3','#1976D2','#0D47A1'],['#B2DFDB','#4DB6AC','#009688','#00796B','#004D40'],['#C8E6C9','#81C784','#4CAF50','#388E3C','#1B5E20'],['#FFECB3','#FFD54F','#FFC107','#FFA000','#FF6F00'],['#FFCCBC','#FF8A65','#FF5722','#E64A19','#BF360C'],['#F5F5F5','#BDBDBD','#9E9E9E','#616161','#212121']]
const SW = ['#000000', '#FFFFFF', ...HUES.flat()]

// ---- Zustand ----
const st = { sets: [], setId: null, scope: 'all', mode: 'word', workshop: false, license: '', q: '', style: '', page: 1, pages: 1, loading: false,
  bg: 'auto', color: 'auto', codeData: null, codeTab: 'svg', detail: null, wset: null, wicons: [] }

// ---- Bausteine von Bootstrap ----
const bs = {}
function initComponents() {
  bs.detail = new bootstrap.Offcanvas('#detail')
  bs.cmdk = new bootstrap.Modal('#cmdk')
  bs.settings = new bootstrap.Modal('#settings')
  bs.newset = new bootstrap.Modal('#newset')
  bs.toast = new bootstrap.Toast('#toast', { delay: 2200 })
  bs.facets = bootstrap.Offcanvas.getOrCreateInstance('#facets')
}

// ---- Hilfen ----
function toast(m) { $('#toast-body').textContent = m; bs.toast.show() }
async function copyText(text) {
  try { if (navigator.clipboard && window.isSecureContext) { await navigator.clipboard.writeText(text); return true } } catch {}
  try { const ta = document.createElement('textarea'); ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0'; document.body.appendChild(ta); ta.select(); const ok = document.execCommand('copy'); ta.remove(); return ok } catch { return false }
}
async function svgText(path) { try { return await (await fetch(path + '.svg')).text() } catch { return '' } }
async function copyIcon(icon) { const t = await svgText(icon.path); if (t && await copyText(t)) toast('SVG kopiert: ' + icon.name); else toast('Kopieren nicht möglich') }

// ---- Erscheinungsbild ----
// Der Kachelgrund bestimmt, welche Icon-Farbe lesbar ist. "Auto" haelt beides
// automatisch im Kontrast; eine gewaehlte Farbe bleibt dagegen unangetastet.
const TILE_BG = { light: '#ffffff', dark: '#12100f', checker: 'transparent' }
function isDark() { return root.dataset.bsTheme === 'dark' }
function tileBg() { return st.bg === 'auto' ? (isDark() ? '#1b211e' : '#ffffff') : TILE_BG[st.bg] }
function autoInk() {
  if (st.bg === 'light') return '#1b2421'
  if (st.bg === 'dark') return '#e7ece9'
  return isDark() ? '#e7ece9' : '#1b2421' // auto und Transparenz folgen dem Erscheinungsbild
}
function applyAppearance() {
  const ink = st.color === 'auto' ? autoInk() : st.color
  app.style.setProperty('--tile-bg', tileBg())
  app.style.setProperty('--ic-color', ink)
  app.style.setProperty('--ic-on-tile', autoInk())
  $('#colorbtn').classList.toggle('is-auto', st.color === 'auto')
  markColor()
  $('#colorbtn').style.background = st.color === 'auto' ? '' : st.color
  $$('.ic-tile').forEach((t) => t.classList.toggle('is-checker', st.bg === 'checker'))
}
function setColor(c) { st.color = c; applyAppearance(); if (st.detail) refreshDetail() }
function setSize(px) { app.style.setProperty('--ic-size', px + 'px') }

// ---- Hell / Dunkel ----
function applyTheme() {
  const pref = localStorage.getItem('iconify-theme') // null = System
  const dark = pref ? pref === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches
  root.dataset.bsTheme = dark ? 'dark' : 'light'
  $('[data-act="theme"]').innerHTML = uisvg(dark ? 'sun' : 'moon', 18)
  applyAppearance()
}
function toggleTheme() { localStorage.setItem('iconify-theme', isDark() ? 'light' : 'dark'); applyTheme() }

// ---- Sets / Filter ----
async function loadSets() {
  st.sets = await api.sets()
  const dl = st.sets.filter((s) => s.downloaded)
  const av = st.sets.filter((s) => !s.downloaded)
  let html = dl.map((s) => `<button type="button" class="ic-setrow" data-set="${esc(s.id)}"><span class="nm">${esc(s.name)}</span><span class="n">${s.icon_count || ''}</span></button>`).join('')
  if (av.length) html += '<div class="ic-label mt-3 mb-2 ms-1">Verfügbar</div>' +
    av.map((s) => `<div class="ic-setrow"><span class="nm text-secondary">${esc(s.name)}</span>
      <button type="button" class="btn btn-sm btn-outline-primary py-0 px-2" data-import="${esc(s.id)}" title="Importieren">${uisvg('down', 14)}</button></div>`).join('')
  $('#sets').innerHTML = html
  if (dl.length && !st.setId) st.setId = dl[0].id
  markActiveSet()
}
function markActiveSet() {
  $$('.ic-setrow[data-set]').forEach((r) => r.classList.toggle('active', st.scope === 'set' && r.dataset.set === st.setId))
}
async function importSet(id) {
  toast('Import gestartet: ' + id)
  try { await fetch(`/api/sets/${encodeURIComponent(id)}/download`, { method: 'POST' }) } catch { toast('Import-Start fehlgeschlagen'); return }
  const t = setInterval(async () => {
    try {
      const p = await (await fetch(`/api/sets/${encodeURIComponent(id)}/progress`)).json()
      if (p.status === 'completed' || p.status === 'error') {
        clearInterval(t); await loadSets()
        toast(p.status === 'completed' ? id + ': ' + p.completed + ' Icons geladen' : 'Import fehlgeschlagen')
      }
    } catch {}
  }, 900)
}
function selectSet(id) {
  st.setId = id; st.scope = 'set'; st.style = ''; $('#scope').value = 'set'
  markActiveSet(); bs.facets.hide(); search(false)
}

// ---- Suche / Raster ----
function tileHtml(icon) {
  return `<button type="button" class="ic-tile${st.bg === 'checker' ? ' is-checker' : ''}" draggable="true"
    data-name="${esc(icon.name)}" data-style="${esc(icon.style || '')}" data-path="${esc(icon.path)}" data-set="${esc(icon.set_id)}" title="${esc(icon.name)}">
    ${st.scope !== 'set' ? `<span class="ic-set">${esc(icon.set_id)}</span>` : ''}
    <span class="ic-quick">
      <span class="btn btn-sm" data-qa="copy" title="SVG kopieren">${uisvg('copy', 15)}</span>
      <span class="btn btn-sm" data-qa="detail" title="Detail">${uisvg('expand', 15)}</span>
      ${st.workshop ? `<span class="btn btn-sm" data-qa="add" title="In die Werkstatt aufnehmen">${uisvg('plus', 15)}</span>` : ''}
    </span>
    <span class="ic-glyph" style="--u:url('${esc(icon.path)}.svg')"></span>
    <span class="ic-name">${esc(icon.name)}</span></button>`
}
async function search(append) {
  if (st.loading) return
  if (st.scope === 'set' && !st.setId) return
  st.loading = true
  if (!append) { st.page = 1; $('#grid').innerHTML = '' }
  try {
    const r = await api.search({ set_id: st.setId, q: st.q, style: st.style, scope: st.scope, license: st.license, page: st.page })
    $('#cnt').textContent = (r.total ?? 0).toLocaleString('de-DE')
    st.pages = r.pages || 1
    if (!append) renderStyles(r.styles || [])
    $('#grid').insertAdjacentHTML('beforeend', (r.icons || []).map(tileHtml).join(''))
    $('#empty').hidden = (r.total ?? 0) > 0
    $('#empty').textContent = st.sets.some((s) => s.downloaded) ? 'Keine Treffer.' : 'Noch keine Icons - importiere links ein Set, um loszulegen.'
    applyAppearance()
  } catch { toast('Suche fehlgeschlagen') } finally { st.loading = false }
}
function loadMore() { if (st.page < st.pages && !st.loading) { st.page++; search(true) } }
function renderStyles(styles) {
  $('#styleh').hidden = styles.length < 2
  $('#styles').innerHTML = styles.length < 2 ? '' :
    `<button type="button" class="btn btn-sm btn-outline-primary rounded-pill active" data-style="">Alle</button>` +
    styles.map((s) => `<button type="button" class="btn btn-sm btn-outline-primary rounded-pill" data-style="${esc(s)}">${esc(s)}</button>`).join('')
}

// ---- Detail ----
async function openDetail(icon) {
  st.detail = icon; $('#dname').textContent = icon.name
  $('#dsize').value = 128; $('#dsizev').textContent = '128px'; $('#code').textContent = '…'
  bs.detail.show()
  await refreshDetail()
}
async function refreshDetail() {
  const i = st.detail; if (!i) return
  const size = +$('#dsize').value
  const color = getComputedStyle(app).getPropertyValue('--ic-color').trim() || '#1b2421'
  try {
    const d = await api.code(i.set_id || st.setId, i.name, i.style, size, color)
    st.codeData = d
    $('#dprev').innerHTML = d.svg || `<span class="ic-glyph" style="--u:url('${esc(i.path)}.svg');width:${size}px;height:${size}px"></span>`
    renderCode()
    $('#dlic').innerHTML = d.license
      ? `Lizenz: <b>${esc(d.license)}</b>${d.license_url ? ` · <a href="${esc(d.license_url)}" target="_blank" rel="noopener">Lizenztext</a>` : ''}${d.requires_attribution ? ' · Namensnennung nötig' : ''}`
      : ''
  } catch { $('#code').textContent = 'Fehler' }
}
function renderCode() {
  const d = st.codeData || {}
  const map = { svg: d.svg, img: d.img, font: d.font_html, css: d.font_css }
  $('#code').textContent = map[st.codeTab] || '- nicht verfügbar -'
}

// ---- Farbfelder ----
const swHtml = (c, titel = c) => `<button type="button" class="ic-sw" style="--c:${c}" data-gcolor="${c}" title="${titel}" aria-label="${titel}"></button>`
$('#palettepop').innerHTML = SW.map((c) => swHtml(c)).join('')
$('#dpal').innerHTML = `<button type="button" class="ic-sw ic-sw-auto" data-gcolor="auto" title="Automatisch" aria-label="Automatisch"></button>` +
  SW.map((c) => swHtml(c)).join('')
function markColor() {
  $$('[data-gcolor]').forEach((b) => b.classList.toggle('is-on', b.dataset.gcolor.toLowerCase() === String(st.color).toLowerCase()))
}

// ---- Ereignisse ----
app.addEventListener('click', async (e) => {
  const act = e.target.closest('[data-act]')?.dataset.act
  if (act === 'theme') return toggleTheme()
  if (act === 'newset') return openNewset()
  if (act === 'exp-font') return exportAction('font')
  if (act === 'exp-zip') return exportAction('zip')
  if (act === 'exp-sprite') return exportAction('sprite')
  if (act === 'go') return runSearch()
  if (act === 'settings') return openSettings()
  if (act === 'llm-test') return llmTest()
  if (act === 'llm-save') return llmSave(false)
  if (act === 'cmdk') return openCmd()
  if (act === 'copysvg') { if (st.codeData?.svg) { await copyText(st.codeData.svg); toast('SVG kopiert') } return }
  if (act === 'dl') { if (st.detail) { const a = document.createElement('a'); a.href = st.detail.path + '.svg'; a.download = st.detail.name + '.svg'; a.click() } return }

  const rm = e.target.closest('[data-rm]'); if (rm) { e.stopPropagation(); return removeWicon(rm.dataset.rm) }
  const gc = e.target.closest('[data-gcolor]')
  if (gc) { setColor(gc.dataset.gcolor); toast(gc.dataset.gcolor === 'auto' ? 'Farbe: automatisch' : 'Farbe: ' + gc.dataset.gcolor); return }

  const imp = e.target.closest('[data-import]'); if (imp) { e.stopPropagation(); return importSet(imp.dataset.import) }
  const setrow = e.target.closest('.ic-setrow[data-set]'); if (setrow) return selectSet(setrow.dataset.set)

  const lc = e.target.closest('#lic [data-lic]')
  if (lc) { st.license = lc.dataset.lic; $$('#lic [data-lic]').forEach((c) => c.classList.toggle('active', c === lc)); search(false); return }
  const chip = e.target.closest('#styles [data-style]')
  if (chip) { st.style = chip.dataset.style; $$('#styles [data-style]').forEach((c) => c.classList.toggle('active', c === chip)); search(false); return }
  const ct = e.target.closest('#ctabs [data-t]')
  if (ct) { st.codeTab = ct.dataset.t; $$('#ctabs [data-t]').forEach((c) => c.classList.toggle('active', c === ct)); renderCode(); return }

  const qa = e.target.closest('[data-qa]')
  const tile = e.target.closest('.ic-tile[data-name]')
  if (tile) {
    const icon = { name: tile.dataset.name, style: tile.dataset.style, path: tile.dataset.path, set_id: tile.dataset.set || st.setId }
    if (qa) {
      e.stopPropagation()
      if (qa.dataset.qa === 'detail') openDetail(icon)
      else if (qa.dataset.qa === 'add') wDrop({ set_id: icon.set_id, name: icon.name, style: icon.style || '' })
      else copyIcon(icon)
      return
    }
    copyIcon(icon)
  }
})

let qt
// Die Suchart entscheidet, was Eingabe und Eingabetaste ausloesen.
function runSearch() { return st.mode === 'ai' ? aiSearch() : search(false) }
function setSearchMode(mode) {
  st.mode = mode
  const ai = mode === 'ai'
  $('#q').placeholder = ai ? 'Beschreiben, was gesucht wird…' : 'Icons durchsuchen…'
  $('#searchhint').textContent = ai
    ? 'Beschreibung eingeben und "Suchen" drücken - das Sprachmodell übersetzt sie in Stichworte.'
    : 'Sucht sofort im Namen der Icons.'
  $('#go').classList.toggle('ic-ai', ai)
  $('#go').classList.toggle('btn-primary', !ai)
  if (!ai && st.q.trim()) search(false)
}
function setBusy(on) {
  $('#go').disabled = on
  $('#go-spin').classList.toggle('d-none', !on)
  $('#go-label').textContent = on ? 'Sucht…' : 'Suchen'
}
$('#q').addEventListener('input', (e) => {
  st.q = e.target.value
  if (st.mode !== 'word') return
  clearTimeout(qt); qt = setTimeout(() => search(false), 220)
})
$('#q').addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); runSearch() } })
$$('[name="ic-searchmode"]').forEach((r) => r.addEventListener('change', () => setSearchMode(r.value)))
$('#scope').addEventListener('change', (e) => {
  st.scope = e.target.value
  if (st.scope === 'set' && !st.setId) { const f = st.sets.find((s) => s.downloaded); if (f) st.setId = f.id }
  markActiveSet(); search(false)
})
$('#size').addEventListener('input', (e) => setSize(e.target.value))
let dt
$('#dsize').addEventListener('input', (e) => { $('#dsizev').textContent = e.target.value + 'px'; clearTimeout(dt); dt = setTimeout(refreshDetail, 180) })
$('#detail').addEventListener('hidden.bs.offcanvas', () => { st.detail = null })

$$('[name="ic-bg"]').forEach((r) => r.addEventListener('change', () => { st.bg = r.value; applyAppearance() }))
$$('[name="ic-dens"]').forEach((r) => r.addEventListener('change', () => { app.dataset.dens = r.value }))
$$('[name="ic-mode"]').forEach((r) => r.addEventListener('change', () => setMode(r.value)))
function setMode(mode) {
  st.workshop = mode === 'workshop'
  app.dataset.mode = mode
  // Auf schmalen Schirmen ist die Werkstatt ein Offcanvas mit eigenem Schalter.
  $('#wpane').classList.toggle('d-none', !st.workshop)
  $('#wopen').classList.toggle('d-none', !st.workshop)
  if (!st.workshop) bootstrap.Offcanvas.getOrCreateInstance('#wpane').hide()
  if (st.workshop) loadWsets()
  if ($('#grid').children.length) search(false) // Kacheln neu zeichnen (Aufnehmen-Knopf)
}

// Endloses Nachladen
new IntersectionObserver((ents) => { if (ents[0].isIntersecting) loadMore() }, { root: $('#results'), rootMargin: '500px' }).observe($('#sentinel'))

// ---- Schnellsuche ----
let cmdRes = []
function openCmd() { $('#cmdq').value = ''; $('#cmdlist').innerHTML = ''; bs.cmdk.show() }
$('#cmdk').addEventListener('shown.bs.modal', () => $('#cmdq').focus())
async function cmdSearch(q) {
  const r = await api.search({ set_id: st.setId, q, scope: st.scope, license: st.license, page: 1 })
  cmdRes = (r.icons || []).slice(0, 20)
  $('#cmdlist').innerHTML = cmdRes.map((i, n) => `<button type="button" class="ic-cmd-item${n === 0 ? ' active' : ''}" data-i="${n}">
    <span class="ic-glyph" style="--u:url('${esc(i.path)}.svg')"></span>${esc(i.name)}
    <span class="ms-auto small text-secondary">kopieren</span></button>`).join('')
}
$('#cmdq').addEventListener('input', (e) => cmdSearch(e.target.value))
$('#cmdlist').addEventListener('click', (e) => { const it = e.target.closest('[data-i]'); if (it) { copyIcon(cmdRes[+it.dataset.i]); bs.cmdk.hide() } })
$('#cmdq').addEventListener('keydown', (e) => { if (e.key === 'Enter' && cmdRes[0]) { copyIcon(cmdRes[0]); bs.cmdk.hide() } })
document.addEventListener('keydown', (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); openCmd() }
  if (e.key === '/' && !/INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) { e.preventDefault(); $('#q').focus() }
})

// ---- Werkstatt ----
function loadWsets() {
  const custom = st.sets.filter((s) => s.is_custom)
  $('#wset').innerHTML = custom.length
    ? custom.map((s) => `<option value="${esc(s.id)}">${esc(s.name)}</option>`).join('')
    : '<option value="">- noch kein eigenes Set -</option>'
  st.wset = custom.length ? custom[0].id : null
  if (st.wset) $('#wset').value = st.wset
  loadWicons()
}
async function loadWicons() {
  if (!st.wset) { renderWGrid([]); return }
  try { const d = await (await fetch(`/api/custom/sets/${encodeURIComponent(st.wset)}/icons`)).json(); renderWGrid(d.icons || []) }
  catch { renderWGrid([]) }
}
function renderWGrid(icons) {
  st.wicons = icons
  $('#wempty').hidden = icons.length > 0
  $('#wgrid').innerHTML = icons.map((i) => `<div class="ic-tile${st.bg === 'checker' ? ' is-checker' : ''}" title="${esc(i.name)}">
    <button type="button" class="btn btn-sm btn-outline-danger ic-remove" data-rm="${esc(i.name)}" title="Entfernen">${uisvg('close', 12)}</button>
    <span class="ic-glyph" style="--u:url('${esc(i.path)}.svg')"></span><span class="ic-name">${esc(i.name)}</span>
    <span class="ic-origin">${i.origin && i.origin !== 'eigen' ? 'aus ' + esc(i.origin) : 'eigen'}</span></div>`).join('')
}
function openNewset() { $('#newset-name').value = ''; bs.newset.show() }
$('#newset').addEventListener('shown.bs.modal', () => $('#newset-name').focus())
$('#newset-form').addEventListener('submit', async (e) => {
  e.preventDefault()
  const name = $('#newset-name').value.trim(); if (name.length < 2) return
  bs.newset.hide()
  try {
    const r = await (await fetch('/api/custom/sets', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) })).json()
    if (r.success) { await loadSets(); loadWsets(); st.wset = r.set_id; $('#wset').value = r.set_id; loadWicons(); toast('Set "' + name + '" erstellt') }
    else toast(r.error || 'Konnte Set nicht anlegen')
  } catch { toast('Fehler') }
})
async function removeWicon(name) {
  if (!st.wset) return
  try { await fetch(`/api/custom/sets/${encodeURIComponent(st.wset)}/icons/${encodeURIComponent(name)}`, { method: 'DELETE' }); loadWicons() } catch {}
}
async function wDrop(p) {
  if (!st.wset) { toast('Erst ein Ziel-Set wählen oder anlegen'); return }
  try {
    const r = await (await fetch(`/api/custom/sets/${encodeURIComponent(st.wset)}/icons/from`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ src_set: p.set_id, name: p.name, style: p.style }) })).json()
    if (r.success) { toast('"' + r.name + '" hinzugefügt'); loadWicons() } else toast(r.detail || 'Konnte nicht hinzufügen')
  } catch { toast('Fehler beim Hinzufügen') }
}
async function exportAction(kind) {
  if (!st.wset || !st.wicons.length) { toast('Set ist leer'); return }
  const icons = st.wicons.map((i) => ({ set_id: st.wset, name: i.name, style: '' }))
  const name = st.wset.replace('custom-', '')
  if (kind === 'font') {
    try {
      const r = await (await fetch('/api/font/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ icons, font_name: name }) })).json()
      if (r.success) { location.href = r.download_url; toast('Font erzeugt') } else toast(r.error || 'Font fehlgeschlagen')
    } catch { toast('Font fehlgeschlagen') }
    return
  }
  const ep = kind === 'zip' ? '/api/export/zip' : '/api/export/sprite'
  try {
    const resp = await fetch(ep, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ icons, name }) })
    const blob = await resp.blob(); const a = document.createElement('a'); a.href = URL.createObjectURL(blob)
    a.download = kind === 'zip' ? name + '.zip' : name + '-sprite.svg'; a.click(); URL.revokeObjectURL(a.href)
    toast(kind === 'zip' ? 'ZIP geladen' : 'Sprite geladen')
  } catch { toast('Export fehlgeschlagen') }
}
$('#wset').addEventListener('change', (e) => { st.wset = e.target.value; loadWicons() })
app.addEventListener('dragstart', (e) => {
  const t = e.target.closest('.ic-tile[draggable]')
  if (t && t.dataset.name) e.dataTransfer.setData('text/plain', JSON.stringify({ set_id: t.dataset.set || st.setId, name: t.dataset.name, style: t.dataset.style || '' }))
})
;(() => {
  const wt = $('#wtarget')
  wt.addEventListener('dragover', (e) => { e.preventDefault(); wt.classList.add('is-drag') })
  wt.addEventListener('dragleave', () => wt.classList.remove('is-drag'))
  wt.addEventListener('drop', (e) => { e.preventDefault(); wt.classList.remove('is-drag'); try { wDrop(JSON.parse(e.dataTransfer.getData('text/plain'))) } catch {} })
})()

// ---- KI-Suche und Einstellungen ----
async function aiSearch() {
  if (!st.q.trim()) { toast('Erst eine Beschreibung eingeben'); return }
  setBusy(true)
  try {
    const d = await (await fetch('/api/icons/ai-search?q=' + encodeURIComponent(st.q) + '&license=' + st.license)).json()
    if (!d.connected) { toast('KI nicht verbunden - siehe Einstellungen'); return }
    if (!d.icons || !d.icons.length) { toast('KI: keine Treffer für "' + st.q + '"'); return }
    st.scope = 'all'; $('#scope').value = 'all'; st.page = 1; st.pages = 1; markActiveSet()
    $('#grid').innerHTML = d.icons.map(tileHtml).join(''); applyAppearance()
    $('#cnt').textContent = d.total; $('#empty').hidden = true
    toast('KI-Treffer: ' + d.terms.join(', '))
  } catch { toast('KI-Suche fehlgeschlagen') } finally { setBusy(false) }
}
function showLlmStatus(s) {
  const el = $('#llm-status')
  const ok = s && s.connected
  el.className = 'alert py-2 px-3 small mb-0 ' + (ok ? 'alert-success' : 'alert-danger')
  el.textContent = ok ? 'Verbunden · Modelle: ' + ((s.models || []).join(', ') || '-')
                      : 'Nicht verbunden' + (s && s.error ? ' · ' + s.error : '')
}
async function openSettings() {
  bs.settings.show()
  try {
    const d = await (await fetch('/api/llm/config')).json()
    $('#llm-url').value = d.config.base_url || ''
    $('#llm-model').value = d.config.model || ''
    $('#llm-enabled').checked = !!d.config.enabled
    showLlmStatus(d.status)
  } catch { showLlmStatus({ connected: false, error: 'Backend nicht erreichbar' }) }
}
async function llmSave(silent) {
  const body = { base_url: $('#llm-url').value.trim(), model: $('#llm-model').value.trim(), enabled: $('#llm-enabled').checked }
  try {
    const d = await (await fetch('/api/llm/config', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })).json()
    showLlmStatus(d.status); if (!silent) toast('Gespeichert')
  } catch { if (!silent) toast('Speichern fehlgeschlagen') }
}
async function llmTest() {
  const el = $('#llm-status'); el.className = 'alert alert-secondary py-2 px-3 small mb-0'; el.textContent = 'Teste…'
  await llmSave(true)
  try { showLlmStatus(await (await fetch('/api/llm/test', { method: 'POST' })).json()) } catch { showLlmStatus({ connected: false, error: 'Test fehlgeschlagen' }) }
}

// ---- Start ----
initComponents()
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { if (!localStorage.getItem('iconify-theme')) applyTheme() })
applyTheme(); setSize(48); setSearchMode('word')
app.dataset.dens = 'comf'
setMode('browse')
api.health().then((h) => { $('#ver').textContent = 'Iconify ' + (h.voll || 'v' + h.version) })
  .catch(() => { $('#ver').textContent = 'Backend nicht erreichbar' })
loadSets().then(() => search(false)).catch(() => toast('Backend nicht erreichbar'))
