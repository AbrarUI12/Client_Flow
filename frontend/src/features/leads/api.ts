import { apiRequest } from '../../lib/apiClient'
import type { Lead, LeadListParams, LeadListResponse, LeadPayload } from './types'

export async function getLeads(params: LeadListParams): Promise<LeadListResponse> {
  const query = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.pageSize),
  })

  if (params.search) query.set('search', params.search)
  if (params.status) query.set('status', params.status)
  if (params.source) query.set('source', params.source)

  return apiRequest<LeadListResponse>(`/leads?${query.toString()}`)
}

export async function getLead(leadId: string): Promise<Lead> {
  return apiRequest<Lead>(`/leads/${leadId}`)
}

export async function createLead(payload: LeadPayload): Promise<Lead> {
  return apiRequest<Lead>('/leads', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateLead(leadId: string, payload: LeadPayload): Promise<Lead> {
  return apiRequest<Lead>(`/leads/${leadId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function archiveLead(leadId: string): Promise<Lead> {
  return apiRequest<Lead>(`/leads/${leadId}/archive`, { method: 'POST' })
}
