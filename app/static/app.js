'use strict'
const $ = (s) => document.querySelector(s)
const $$ = (s) => [...document.querySelectorAll(s)]
const app = $('#app'), root = document.documentElement

// ---- UI-Icons (echte SVGs statt Glyphen) ----
const UI = {
  search: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
  copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>',
  expand: '<path d="M8 3H5a2 2 0 0 0-2 2v3M16 3h3a2 2 0 0 1 2 2v3M8 21H5a2 2 0 0 1-2-2v-3M16 21h3a2 2 0 0 0 2-2v-3"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.4 1.4M17.2 17.2l1.4 1.4M18.6 5.4l-1.4 1.4M6.8 17.2l-1.4 1.4"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/>',
  close: '<path d="M18 6L6 18M6 6l12 12"/>',
}
const uisvg = (k, w = 18) => `<svg viewBox="0 0 24 24" width="${w}" height="${w}" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${UI[k]}</svg>`

// ---- API (relativ -> über den Proxy ans echte Backend) ----
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

// ---- State ----
const st = { sets: [], setId: null, scope: 'all', license: '', q: '', style: '', page: 1, pages: 1, loading: false, bg: 'light', codeData: null, codeTab: 'svg', detail: null, wset: null, wicons: [] }

// ---- Utils ----
function toast(m) { const t = $('#toast'); t.textContent = m; t.classList.add('show'); clearTimeout(t._t); t._t = setTimeout(() => t.classList.remove('show'), 1600) }
async function copyText(text) {
  try { if (navigator.clipboard && window.isSecureContext) { await navigator.clipboard.writeText(text); return true } } catch {}
  try { const ta = document.createElement('textarea'); ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0'; document.body.appendChild(ta); ta.select(); const ok = document.execCommand('copy'); ta.remove(); return ok } catch { return false }
}
async function svgText(path) { try { return await (await fetch(path + '.svg')).text() } catch { return '' } }
async function copyIcon(icon) { const t = await svgText(icon.path); if (t && await copyText(t)) toast('SVG kopiert: ' + icon.name); else toast('Kopieren nicht möglich') }

// ---- Theme (System/Auto + manueller Toggle) ----
function applyTheme() {
  const pref = localStorage.getItem('iconify-theme') // null=auto | light | dark
  const dark = pref ? pref === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches
  root.dataset.theme = dark ? 'dark' : 'light'
  const tb = document.querySelector('[data-act="theme"]'); if (tb) tb.innerHTML = uisvg(dark ? 'sun' : 'moon', 18)
}
function toggleTheme() { const cur = root.dataset.theme; localStorage.setItem('iconify-theme', cur === 'dark' ? 'light' : 'dark'); applyTheme() }

// ---- Sets / Facetten ----
async function loadSets() {
  st.sets = await api.sets()
  const dl = st.sets.filter((s) => s.downloaded)
  const av = st.sets.filter((s) => !s.downloaded)
  let html = dl.map((s) => `<div class="setrow" data-set="${s.id}"><span class="nm">${s.name}</span><span class="n">${s.icon_count || ''}</span></div>`).join('')
  if (av.length) html += '<div class="facet-h" style="margin-top:10px">Verfügbar</div>' +
    av.map((s) => `<div class="setrow av"><span class="nm">${s.name}</span><button class="dlbtn" data-import="${s.id}" title="Importieren">↓</button></div>`).join('')
  $('#sets').innerHTML = html
  if (dl.length && !st.setId) st.setId = dl[0].id
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
  $$('.setrow').forEach((r) => r.classList.toggle('on', r.dataset.set === id))
  search(false)
}

// ---- Suche / Grid ----
function applyBg() {
  $('#grid').style.setProperty('--tile-bg', st.bg === 'dark' ? '#0f172a' : st.bg === 'light' ? '#ffffff' : 'transparent')
  $$('.tile').forEach((t) => t.classList.toggle('bg-checker', st.bg === 'checker'))
}
function tileHtml(icon) {
  return `<button class="tile ${st.bg === 'checker' ? 'bg-checker' : ''}" draggable="true" data-name="${icon.name}" data-style="${icon.style || ''}" data-path="${icon.path}" data-set="${icon.set_id}" title="${icon.name}">
    ${st.scope !== 'set' ? `<span class="setlbl">${icon.set_id}</span>` : ''}
    <span class="qa"><span class="qb" data-qa="copy" title="SVG kopieren">${uisvg('copy', 16)}</span><span class="qb" data-qa="detail" title="Detail">${uisvg('expand', 16)}</span></span>
    <span class="ti" style="--u:url('${icon.path}.svg')"></span><span class="tnm">${icon.name}</span></button>`
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
    $('#empty').textContent = st.sets.some((s) => s.downloaded) ? 'Keine Treffer.' : 'Noch keine Icons — importiere links ein Set, um loszulegen.'
    applyBg()
  } catch { toast('Suche fehlgeschlagen') } finally { st.loading = false }
}
function loadMore() { if (st.page < st.pages && !st.loading) { st.page++; search(true) } }
function renderStyles(styles) {
  $('#styleh').hidden = styles.length < 2
  $('#styles').innerHTML = styles.length < 2 ? '' :
    `<button class="chip on" data-style="">Alle</button>` + styles.map((s) => `<button class="chip" data-style="${s}">${s}</button>`).join('')
}

// ---- Detail ----
async function openDetail(icon) {
  st.detail = icon; $('#dname').textContent = icon.name; $('#scrim').classList.add('show')
  $('#dpal').hidden = true; $('#palcaret').textContent = '▸'
  $('#dsize').value = 128; $('#dsizev').textContent = '128px'; $('#code').textContent = '…'
  await refreshDetail()
}
async function refreshDetail() {
  const i = st.detail; if (!i) return
  const size = +$('#dsize').value
  const color = getComputedStyle(app).getPropertyValue('--ic-color').trim() || '#000000'
  try {
    const d = await api.code(i.set_id || st.setId, i.name, i.style, size, color)
    st.codeData = d
    $('#dprev').innerHTML = d.svg || `<span class="ti" style="--u:url('${i.path}.svg');width:${size}px;height:${size}px"></span>`
    renderCode()
    $('#dlic').innerHTML = d.license ? `Lizenz: <b>${d.license}</b>${d.license_url ? ` · <a href="${d.license_url}" target="_blank" rel="noopener">Lizenztext</a>` : ''}${d.requires_attribution ? ' · Namensnennung nötig' : ''}` : ''
  } catch { $('#code').textContent = 'Fehler' }
}
function renderCode() {
  const d = st.codeData || {}
  const map = { svg: d.svg, img: d.img, font: d.font_html, css: d.font_css }
  $('#code').textContent = map[st.codeTab] || '— nicht verfügbar —'
}

// ---- Appearance ----
function setSize(px) { app.style.setProperty('--ic-size', px + 'px') }
function setColor(c) { app.style.setProperty('--ic-color', c); $('#colorbtn').style.background = c; const ch = $('#dchip'); if (ch) ch.style.background = c }

// ---- Palette-Popover ----
$('#palettepop').innerHTML = SW.map((c) => `<button class="sw" style="--c:${c};width:16px;height:16px" data-gcolor="${c}"></button>`).join('')
$('#dpal').innerHTML = SW.map((c) => `<button class="sw" style="--c:${c}" data-dcolor="${c}"></button>`).join('')

// ---- Events ----
app.addEventListener('click', async (e) => {
  const act = e.target.closest('[data-act]')?.dataset.act
  if (act === 'theme') return toggleTheme()
  if (act === 'closed') return $('#scrim').classList.remove('show')
  if (act === 'togglepal') { const p = $('#dpal'); p.hidden = !p.hidden; $('#palcaret').textContent = p.hidden ? '▸' : '▾'; return }
  if (act === 'newset') return newWset()
  if (act === 'exp-font') return exportAction('font')
  if (act === 'exp-zip') return exportAction('zip')
  if (act === 'exp-sprite') return exportAction('sprite')
  if (act === 'ai') return aiSearch()
  if (act === 'settings') return openSettings()
  if (act === 'closeset') return $('#settings').classList.remove('show')
  if (act === 'llm-test') return llmTest()
  if (act === 'llm-save') return llmSave(false)
  const rm = e.target.closest('[data-rm]'); if (rm) { e.stopPropagation(); removeWicon(rm.dataset.rm); return }
  if (act === 'cmdk') return openCmd()
  if (act === 'copysvg') { if (st.codeData?.svg) { await copyText(st.codeData.svg); toast('SVG kopiert') } return }
  if (act === 'dl') { if (st.detail) { const a = document.createElement('a'); a.href = st.detail.path + '.svg'; a.download = st.detail.name + '.svg'; a.click() } return }

  const cb = e.target.closest('#colorbtn'); if (cb) { $('#palettepop').hidden = !$('#palettepop').hidden; return }
  const gc = e.target.closest('[data-gcolor]'); if (gc) { setColor(gc.dataset.gcolor); $('#palettepop').hidden = true; toast('Farbe: ' + gc.dataset.gcolor); return }
  const dc = e.target.closest('[data-dcolor]'); if (dc) { setColor(dc.dataset.dcolor); refreshDetail(); $('#dpal').hidden = true; $('#palcaret').textContent = '▸'; return }

  const seg = e.target.closest('[data-seg] button')
  if (seg) { const g = seg.closest('[data-seg]').dataset.seg; seg.parentElement.querySelectorAll('button').forEach((b) => b.classList.toggle('on', b === seg))
    if (g === 'bg') { st.bg = seg.dataset.v; applyBg() }
    if (g === 'dens') { const c = seg.dataset.v === 'comp'; $('#grid').style.setProperty('--tile-min', c ? '84px' : '112px'); $('#grid').style.setProperty('--tile-gap', c ? '10px' : '16px') } return }

  const imp = e.target.closest('[data-import]'); if (imp) { e.stopPropagation(); return importSet(imp.dataset.import) }
  const setrow = e.target.closest('.setrow'); if (setrow && setrow.dataset.set) return selectSet(setrow.dataset.set)
  const lc = e.target.closest('#lic .chip'); if (lc) { st.license = lc.dataset.lic; $$('#lic .chip').forEach((c) => c.classList.toggle('on', c === lc)); search(false); return }
  const chip = e.target.closest('#styles .chip'); if (chip) { st.style = chip.dataset.style; $$('#styles .chip').forEach((c) => c.classList.toggle('on', c === chip)); search(false); return }
  const ct = e.target.closest('.ctab'); if (ct) { st.codeTab = ct.dataset.t; $$('.ctab').forEach((c) => c.classList.toggle('on', c === ct)); renderCode(); return }

  const qa = e.target.closest('[data-qa]')
  const tile = e.target.closest('.tile')
  if (tile) {
    const icon = { name: tile.dataset.name, style: tile.dataset.style, path: tile.dataset.path, set_id: tile.dataset.set || st.setId }
    if (qa) { e.stopPropagation(); if (qa.dataset.qa === 'detail') openDetail(icon); else copyIcon(icon); return }
    copyIcon(icon)
  }
})
$('#scrim').addEventListener('click', (e) => { if (!e.target.closest('[data-stop]')) $('#scrim').classList.remove('show') })
document.addEventListener('click', (e) => { if (!e.target.closest('#colorbtn') && !e.target.closest('#palettepop')) $('#palettepop').hidden = true }, true)

let qt
$('#q').addEventListener('input', (e) => { st.q = e.target.value; clearTimeout(qt); qt = setTimeout(() => search(false), 220) })
$('#scope').addEventListener('change', (e) => {
  st.scope = e.target.value
  if (st.scope === 'set' && !st.setId) { const f = st.sets.find((s) => s.downloaded); if (f) st.setId = f.id }
  $$('.setrow').forEach((r) => r.classList.toggle('on', st.scope === 'set' && r.dataset.set === st.setId))
  search(false)
})
$('#size').addEventListener('input', (e) => setSize(e.target.value))
$('#dsize').addEventListener('input', (e) => { $('#dsizev').textContent = e.target.value + 'px'; clearTimeout(qt); qt = setTimeout(refreshDetail, 180) })

// Infinite scroll
new IntersectionObserver((ents) => { if (ents[0].isIntersecting) loadMore() }, { rootMargin: '500px' }).observe($('#sentinel'))

// ---- ⌘K ----
let cmdRes = []
function openCmd() { $('#cmdk').classList.add('show'); $('#cmdq').value = ''; $('#cmdlist').innerHTML = ''; $('#cmdq').focus() }
async function cmdSearch(q) {
  const r = await api.search({ set_id: st.setId, q, scope: st.scope, license: st.license, page: 1 })
  cmdRes = (r.icons || []).slice(0, 20)
  $('#cmdlist').innerHTML = cmdRes.map((i, n) => `<div class="cmdk-it ${n === 0 ? 'sel' : ''}" data-i="${n}"><span class="ti" style="--u:url('${i.path}.svg')"></span>${i.name}<span style="margin-left:auto;color:var(--mut);font-size:11px">kopieren</span></div>`).join('')
}
$('#cmdq').addEventListener('input', (e) => cmdSearch(e.target.value))
$('#cmdlist').addEventListener('click', (e) => { const it = e.target.closest('[data-i]'); if (it) { copyIcon(cmdRes[+it.dataset.i]); $('#cmdk').classList.remove('show') } })
$('#cmdk').addEventListener('click', (e) => { if (!e.target.closest('[data-stop]')) $('#cmdk').classList.remove('show') })
$('#cmdq').addEventListener('keydown', (e) => { if (e.key === 'Enter' && cmdRes[0]) { copyIcon(cmdRes[0]); $('#cmdk').classList.remove('show') } })
document.addEventListener('keydown', (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); openCmd() }
  if (e.key === 'Escape') { $('#cmdk').classList.remove('show'); $('#scrim').classList.remove('show') }
  if (e.key === '/' && !/INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) { e.preventDefault(); $('#q').focus() }
})

// Mode (Werkstatt kommt in K3)
$$('.modesw [data-mode]').forEach((b) => b.addEventListener('click', () => {
  app.dataset.mode = b.dataset.mode
  $$('.modesw button').forEach((x) => x.classList.toggle('on', x === b))
  if (b.dataset.mode === 'workshop') loadWsets()
}))

// ---- Werkstatt (K3) ----
function loadWsets() {
  const custom = st.sets.filter((s) => s.is_custom)
  $('#wset').innerHTML = custom.length
    ? custom.map((s) => `<option value="${s.id}">${s.name}</option>`).join('')
    : '<option value="">— noch kein eigenes Set —</option>'
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
  $('#wgrid').innerHTML = icons.map((i) => `<div class="tile wtile ${st.bg === 'checker' ? 'bg-checker' : ''}" title="${i.name}">
    <span class="rm" data-rm="${i.name}" title="Entfernen">${uisvg('close', 13)}</span>
    <span class="ti" style="--u:url('${i.path}.svg')"></span><span class="tnm">${i.name}</span>
    <span class="worigin">${i.origin && i.origin !== 'eigen' ? 'aus ' + i.origin : 'eigen'}</span></div>`).join('')
}
async function newWset() {
  const name = prompt('Name des eigenen Sets:')?.trim(); if (!name || name.length < 2) return
  try {
    const r = await (await fetch('/api/custom/sets', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) })).json()
    if (r.success) { await loadSets(); loadWsets(); st.wset = r.set_id; $('#wset').value = r.set_id; loadWicons(); toast('Set „' + name + '" erstellt') }
    else toast(r.error || 'Konnte Set nicht anlegen')
  } catch { toast('Fehler') }
}
async function removeWicon(name) {
  if (!st.wset) return
  try { await fetch(`/api/custom/sets/${encodeURIComponent(st.wset)}/icons/${encodeURIComponent(name)}`, { method: 'DELETE' }); loadWicons() } catch {}
}
async function wDrop(p) {
  if (!st.wset) { toast('Erst ein Ziel-Set wählen oder anlegen'); return }
  try {
    const r = await (await fetch(`/api/custom/sets/${encodeURIComponent(st.wset)}/icons/from`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ src_set: p.set_id, name: p.name, style: p.style }) })).json()
    if (r.success) { toast('„' + r.name + '" hinzugefügt'); loadWicons() } else toast(r.detail || 'Konnte nicht hinzufügen')
  } catch { toast('Fehler beim Hinzufügen') }
}
async function exportAction(kind) {
  if (!st.wset || !st.wicons.length) { toast('Set ist leer'); return }
  const icons = st.wicons.map((i) => ({ set_id: st.wset, name: i.name, style: '' }))
  const name = st.wset.replace('custom-', '')
  if (kind === 'font') {
    try { const r = await (await fetch('/api/font/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ icons, font_name: name }) })).json(); if (r.success) { location.href = r.download_url; toast('Font erzeugt') } else toast(r.error || 'Font fehlgeschlagen') } catch { toast('Font fehlgeschlagen') }
    return
  }
  const ep = kind === 'zip' ? '/api/export/zip' : '/api/export/sprite'
  try {
    const resp = await fetch(ep, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ icons, name }) })
    const blob = await resp.blob(); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = kind === 'zip' ? name + '.zip' : name + '-sprite.svg'; a.click(); URL.revokeObjectURL(a.href)
    toast(kind === 'zip' ? 'ZIP geladen' : 'Sprite geladen')
  } catch { toast('Export fehlgeschlagen') }
}
$('#wset').addEventListener('change', (e) => { st.wset = e.target.value; loadWicons() })
app.addEventListener('dragstart', (e) => { const t = e.target.closest('.tile[draggable]'); if (t && t.dataset.name) e.dataTransfer.setData('text/plain', JSON.stringify({ set_id: t.dataset.set || st.setId, name: t.dataset.name, style: t.dataset.style || '' })) })
;(() => { const wt = $('#wtarget'); if (!wt) return; wt.addEventListener('dragover', (e) => { e.preventDefault(); wt.classList.add('drag') }); wt.addEventListener('dragleave', () => wt.classList.remove('drag')); wt.addEventListener('drop', (e) => { e.preventDefault(); wt.classList.remove('drag'); try { wDrop(JSON.parse(e.dataTransfer.getData('text/plain'))) } catch {} }) })()

// ---- K4: KI-Prosa-Suche + Einstellungen (LM-Studio) ----
async function aiSearch() {
  if (!st.q.trim()) { toast('Erst einen Suchbegriff eingeben'); return }
  toast('KI denkt…')
  try {
    const d = await (await fetch('/api/icons/ai-search?q=' + encodeURIComponent(st.q) + '&license=' + st.license)).json()
    if (!d.connected) { toast('KI nicht verbunden — siehe Einstellungen ⚙'); return }
    if (!d.icons || !d.icons.length) { toast('KI: keine Treffer für „' + st.q + '"'); return }
    st.scope = 'all'; $('#scope').value = 'all'; st.page = 1; st.pages = 1
    $('#grid').innerHTML = d.icons.map(tileHtml).join(''); applyBg()
    $('#cnt').textContent = d.total; $('#empty').hidden = true
    toast('KI-Treffer: ' + d.terms.join(', '))
  } catch { toast('KI-Suche fehlgeschlagen') }
}
function showLlmStatus(s) {
  const el = $('#llm-status')
  if (s && s.connected) { el.className = 'llm-status ok'; el.textContent = 'Verbunden · Modelle: ' + ((s.models || []).join(', ') || '—') }
  else { el.className = 'llm-status err'; el.textContent = 'Nicht verbunden' + (s && s.error ? ' · ' + s.error : '') }
}
async function openSettings() {
  $('#settings').classList.add('show')
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
  $('#llm-status').className = 'llm-status'; $('#llm-status').textContent = 'Teste…'
  await llmSave(true)
  try { showLlmStatus(await (await fetch('/api/llm/test', { method: 'POST' })).json()) } catch { showLlmStatus({ connected: false, error: 'Test fehlgeschlagen' }) }
}
$('#settings').addEventListener('click', (e) => { if (!e.target.closest('[data-stop]')) $('#settings').classList.remove('show') })
$('#q').addEventListener('keydown', (e) => { if (e.key === 'Enter') aiSearch() })

// ---- Init ----
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { if (!localStorage.getItem('iconify-theme')) applyTheme() })
applyTheme(); setColor(getComputedStyle(app).getPropertyValue('--ic-color').trim() || '#1b2421'); setSize(40)
api.health().then((h) => { $('#ver').textContent = 'v' + h.version }).catch(() => {})
loadSets().then(() => search(false)).catch(() => toast('Backend nicht erreichbar'))
