export const followUpGroups = ['overdue', 'today', 'upcoming', 'completed'] as const

export type FollowUpGroup = (typeof followUpGroups)[number]

export type FollowUp = {
  id: string
  lead_id: string
  due_at: string
  note: string
  is_completed: boolean
  completed_at: string | null
  created_at: string
  updated_at: string
  lead: {
    id: string
    contact_name: string
    company: string | null
  }
}

export type FollowUpListResponse = {
  items: FollowUp[]
  total: number
}

export type FollowUpPayload = {
  note: string
  due_at: string
}
