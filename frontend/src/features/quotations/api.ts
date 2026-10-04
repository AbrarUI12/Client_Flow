import { apiRequest } from '../../lib/apiClient'
import type {
  Quotation,
  QuotationListParams,
  QuotationListResponse,
  QuotationPayload,
  QuotationStatus,
} from './types'

export async function getQuotations(params: QuotationListParams): Promise<QuotationListResponse> {
  const query = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.pageSize),
  })
  if (params.search) query.set('search', params.search)
  if (params.status) query.set('status', params.status)
  return apiRequest<QuotationListResponse>(`/quotations?${query.toString()}`)
}

export async function getLeadQuotations(leadId: string): Promise<QuotationListResponse> {
  return apiRequest<QuotationListResponse>(`/leads/${leadId}/quotations?page_size=100`)
}

export async function getQuotation(quotationId: string): Promise<Quotation> {
  return apiRequest<Quotation>(`/quotations/${quotationId}`)
}

export async function createQuotation(leadId: string, payload: QuotationPayload): Promise<Quotation> {
  return apiRequest<Quotation>(`/leads/${leadId}/quotations`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateQuotation(
  quotationId: string,
  payload: QuotationPayload,
): Promise<Quotation> {
  return apiRequest<Quotation>(`/quotations/${quotationId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function transitionQuotation(
  quotationId: string,
  status: QuotationStatus,
): Promise<Quotation> {
  return apiRequest<Quotation>(`/quotations/${quotationId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
}
