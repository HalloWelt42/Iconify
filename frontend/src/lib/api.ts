import type { IconSet, SearchResult, Progress, IconCode } from './types'

async function j<T>(url: string, opts?: RequestInit): Promise<T> {
  const r = await fetch(url, opts)
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return (await r.json()) as T
}

export interface SearchParams {
  set_id: string
  q?: string
  style?: string
  page?: number
  per_page?: number
}

export const api = {
  health: () => j<{ status: string; version: string }>('/health'),

  sets: (licenseCategory = '') =>
    j<IconSet[]>(`/api/sets${licenseCategory ? `?license_category=${encodeURIComponent(licenseCategory)}` : ''}`),

  search: (p: SearchParams) => {
    const qs = new URLSearchParams({
      set_id: p.set_id,
      q: p.q ?? '',
      style: p.style ?? '',
      page: String(p.page ?? 1),
      per_page: String(p.per_page ?? 120),
    })
    return j<SearchResult>(`/api/icons/search?${qs}`)
  },

  code: (setId: string, name: string, p: { style?: string; size?: number; color?: string }) => {
    const qs = new URLSearchParams({
      style: p.style ?? '',
      size: String(p.size ?? 128),
      color: p.color ?? '#000000',
    })
    return j<IconCode>(`/api/icons/${encodeURIComponent(setId)}/${encodeURIComponent(name)}/code?${qs}`)
  },

  svgUrl: (icon: { path: string }) => `${icon.path}.svg`,

  downloadSet: (id: string) => fetch(`/api/sets/${encodeURIComponent(id)}/download`, { method: 'POST' }),
  progress: (id: string) => j<Progress>(`/api/sets/${encodeURIComponent(id)}/progress`),
  deleteSet: (id: string) => fetch(`/api/sets/${encodeURIComponent(id)}`, { method: 'DELETE' }),
}
