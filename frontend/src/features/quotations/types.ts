import type { Lead } from '../leads/types'

export const quotationStatuses = ['DRAFT', 'SENT', 'ACCEPTED', 'REJECTED'] as const

export type QuotationStatus = (typeof quotationStatuses)[number]

export type QuotationItem = {
  id: string
  description: string
  quantity: string
  unit_price: string
  line_total: string
  sort_order: number
}

export type QuotationLead = Pick<Lead, 'id' | 'contact_name' | 'company' | 'email'>

export type Quotation = {
  id: string
  lead_id: string
  quote_number: string
  status: QuotationStatus
  issue_date: string
  valid_until: string
  subtotal: string
  discount_percent: string
  discount_amount: string
  tax_percent: string
  tax_amount: string
  total: string
  notes: string | null
  sent_at: string | null
  accepted_at: string | null
  rejected_at: string | null
  created_at: string
  updated_at: string
  lead: QuotationLead
  items: QuotationItem[]
}

export type QuotationListResponse = {
  items: Quotation[]
  page: number
  page_size: number
  total: number
  pages: number
}

export type QuotationListParams = {
  page: number
  pageSize: number
  search: string
  status: QuotationStatus | ''
}

export type QuotationItemPayload = {
  description: string
  quantity: string
  unit_price: string
}

export type QuotationPayload = {
  issue_date: string
  valid_until: string
  discount_percent: string
  tax_percent: string
  notes: string | null
  items: QuotationItemPayload[]
}
