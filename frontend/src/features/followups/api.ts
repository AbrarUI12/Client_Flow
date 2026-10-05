import { apiRequest } from '../../lib/apiClient'
import type { FollowUp, FollowUpGroup, FollowUpListResponse, FollowUpPayload } from './types'

export async function getFollowUps(options: {
  group?: FollowUpGroup
  leadId?: string
} = {}): Promise<FollowUpListResponse> {
  const query = new URLSearchParams({ limit: '500' })
  if (options.group) query.set('group', options.group)
  if (options.leadId) query.set('lead_id', options.leadId)
  return apiRequest<FollowUpListResponse>(`/follow-ups?${query.toString()}`)
}

export async function createFollowUp(leadId: string, payload: FollowUpPayload): Promise<FollowUp> {
  return apiRequest<FollowUp>(`/leads/${leadId}/follow-ups`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateFollowUp(followUpId: string, payload: FollowUpPayload): Promise<FollowUp> {
  return apiRequest<FollowUp>(`/follow-ups/${followUpId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function completeFollowUp(followUpId: string): Promise<FollowUp> {
  return apiRequest<FollowUp>(`/follow-ups/${followUpId}/complete`, { method: 'PATCH' })
}
