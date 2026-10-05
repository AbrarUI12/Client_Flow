import type { FollowUp } from '../followups/types'
import type { Lead, LeadStatus } from '../leads/types'

export type DashboardSummary = {
  total_leads: number
  open_quotation_count: number
  open_quotation_value: string
  overdue_followup_count: number
  pipeline_counts: Record<LeadStatus, number>
  overdue_followups: FollowUp[]
  upcoming_followups: FollowUp[]
  recent_leads: Lead[]
}
