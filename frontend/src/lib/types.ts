export type LicenseCategory = 'permissive' | 'attribution' | 'none'

export interface IconSet {
  id: string
  name: string
  estimated_count: number
  icon_count: number
  license: string
  license_spdx: string
  license_url: string
  license_category: LicenseCategory
  requires_attribution: boolean
  website: string
  styles: string[]
  downloaded: boolean
  has_font: boolean
  is_custom: boolean
  prefix?: string
}

export interface Icon {
  name: string
  style: string
  path: string
  set_id: string
}

export interface SearchResult {
  icons: Icon[]
  total: number
  page: number
  per_page: number
  pages: number
  styles: string[]
  has_font: boolean
  is_custom: boolean
  error?: string
}

export interface Progress {
  total: number
  unique_icons: number
  styles_count: number
  completed: number
  failed: number
  status: string
  message: string
  current_icon: string
  percent: number
}

export interface IconCode {
  svg: string | null
  img: string
  font_html: string | null
  font_css: string | null
  font_url: string | null
  has_font: boolean
  license: string
  license_spdx: string
  license_url: string
  requires_attribution: boolean
  attribution: string
}
