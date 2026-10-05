import type { FollowUpGroup } from './types'

export const followUpKeys = {
  all: ['follow-ups'] as const,
  groups: () => [...followUpKeys.all, 'group'] as const,
  group: (group: FollowUpGroup) => [...followUpKeys.groups(), group] as const,
  lead: (leadId: string) => [...followUpKeys.all, 'lead', leadId] as const,
}
