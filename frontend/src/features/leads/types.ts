export const leadStatuses = ['NEW', 'CONTACTED', 'QUALIFIED', 'QUOTED', 'WON', 'LOST'] as const

export const leadSources = ['WEBSITE', 'REFERRAL', 'SOCIAL', 'EMAIL', 'PHONE', 'OTHER'] as const

export type LeadStatus = (typeof leadStatuses)[number]
export type LeadSource = (typeof leadSources)[number]

export type Lead = {
  id: string
  contact_name: string
  company: string | null
  email: string | null
  phone: string | null
  source: LeadSource | null
  status: LeadStatus
  estimated_value: string
  notes: string | null
  is_archived: boolean
  created_at: string
  updated_at: string
}

export type LeadListResponse = {
  items: Lead[]
  page: number
  page_size: number
  total: number
  pages: number
}

export type LeadListParams = {
  page: number
  pageSize: number
  search: string
  status: LeadStatus | ''
  source: LeadSource | ''
}

export type LeadPayload = {
  contact_name: string
  company: string | null
  email: string | null
  phone: string | null
  source: LeadSource | null
  status: LeadStatus
  estimated_value: string
  notes: string | null
}
