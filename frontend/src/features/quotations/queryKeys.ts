import type { QuotationListParams } from './types'

export const quotationKeys = {
  all: ['quotations'] as const,
  lists: () => [...quotationKeys.all, 'list'] as const,
  list: (params: QuotationListParams) => [...quotationKeys.lists(), params] as const,
  leadList: (leadId: string) => [...quotationKeys.lists(), 'lead', leadId] as const,
  details: () => [...quotationKeys.all, 'detail'] as const,
  detail: (quotationId: string) => [...quotationKeys.details(), quotationId] as const,
}
