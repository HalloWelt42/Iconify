import { api } from './api'
import type { IconSet, Icon } from './types'

export interface Settings {
  theme: 'auto' | 'light' | 'dark'
  gridTheme: 'light' | 'dark'
  size: number
}

function loadSettings(): Settings {
  const def: Settings = { theme: 'auto', gridTheme: 'light', size: 128 }
  try {
    return { ...def, ...JSON.parse(localStorage.getItem('iconify-settings') || '{}') }
  } catch {
    return def
  }
}

function loadCart(): Icon[] {
  try {
    return JSON.parse(localStorage.getItem('iconify-cart') || '[]')
  } catch {
    return []
  }
}

interface Toast { id: number; msg: string; type: string }

export const ui = $state({
  sets: [] as IconSet[],
  activeSetId: null as string | null,
  licenseFilter: '',
  query: '',
  activeStyle: '',
  results: [] as Icon[],
  total: 0,
  page: 1,
  pages: 1,
  loading: false,
  styles: [] as string[],
  selected: null as Icon | null,
  cart: loadCart(),
  toasts: [] as Toast[],
  settings: loadSettings(),
})

let toastSeq = 0
export function toast(msg: string, type = 'info') {
  const id = ++toastSeq
  ui.toasts = [...ui.toasts, { id, msg, type }]
  setTimeout(() => {
    ui.toasts = ui.toasts.filter((t) => t.id !== id)
  }, 3000)
}

export function saveSettings() {
  localStorage.setItem('iconify-settings', JSON.stringify(ui.settings))
}

export function saveCart() {
  localStorage.setItem('iconify-cart', JSON.stringify(ui.cart))
}
export function inCart(icon: Icon): boolean {
  return ui.cart.some((c) => c.path === icon.path)
}
export function toggleCart(icon: Icon) {
  ui.cart = inCart(icon) ? ui.cart.filter((c) => c.path !== icon.path) : [...ui.cart, icon]
  saveCart()
}
export function clearCart() {
  ui.cart = []
  saveCart()
}

export function activeSet(): IconSet | undefined {
  return ui.sets.find((s) => s.id === ui.activeSetId)
}

export async function loadSets() {
  try {
    ui.sets = await api.sets()
  } catch {
    toast('Fehler beim Laden der Sets', 'error')
  }
}

export async function selectSet(id: string) {
  ui.activeSetId = id
  ui.activeStyle = ''
  ui.query = ''
  await runSearch(false)
}

export async function runSearch(append: boolean) {
  const set = activeSet()
  if (!set || !set.downloaded || ui.loading) return
  ui.loading = true
  if (!append) {
    ui.page = 1
    ui.results = []
  }
  try {
    const r = await api.search({ set_id: set.id, q: ui.query, style: ui.activeStyle, page: ui.page })
    ui.results = append ? [...ui.results, ...r.icons] : r.icons
    if (!append) ui.styles = r.styles ?? []
    ui.total = r.total
    ui.pages = r.pages
  } catch {
    toast('Fehler bei der Suche', 'error')
  } finally {
    ui.loading = false
  }
}

export async function loadMore() {
  if (ui.page >= ui.pages || ui.loading) return
  ui.page += 1
  await runSearch(true)
}
