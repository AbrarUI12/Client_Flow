import { useQuery } from '@tanstack/react-query'
import { CalendarClock, LoaderCircle, Plus } from 'lucide-react'
import { useState } from 'react'

import { useAuth } from '../auth/authStore'
import { getFollowUps } from './api'
import { FollowUpDialog } from './FollowUpDialog'
import { FollowUpItem } from './FollowUpItem'
import { followUpKeys } from './queryKeys'
import type { FollowUp } from './types'

export function LeadFollowUpsSection({
  lead,
}: {
  lead: { id: string; contact_name: string }
}) {
  const { user } = useAuth()
  const [dialog, setDialog] = useState<'create' | FollowUp | null>(null)
  const query = useQuery({
    queryKey: followUpKeys.lead(lead.id),
    queryFn: () => getFollowUps({ leadId: lead.id }),
  })
  const timeZone = user?.timezone || 'UTC'

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <div><h3 className="font-semibold text-slate-900">Follow-ups</h3><p className="mt-1 text-sm text-slate-600">Conversations and reminders for this lead.</p></div>
        <button type="button" onClick={() => setDialog('create')} className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-blue-200 px-3 text-sm font-semibold text-blue-600"><Plus className="size-4" /> Add</button>
      </div>

      {query.isPending ? (
        <LoaderCircle aria-label="Loading follow-ups" className="mx-auto my-8 size-6 animate-spin text-blue-600" />
      ) : query.isError ? (
        <p className="mt-5 rounded-xl bg-red-50 p-3 text-sm text-red-700">Follow-ups could not be loaded.</p>
      ) : query.data.items.length === 0 ? (
        <p className="mt-5 flex items-center gap-2 rounded-xl bg-slate-50 p-4 text-sm text-slate-600"><CalendarClock className="size-4" /> No follow-ups yet. Add the next action for this lead.</p>
      ) : (
        <div className="mt-5 space-y-3">{query.data.items.map((followUp) => <FollowUpItem key={followUp.id} followUp={followUp} timeZone={timeZone} showLead={false} onEdit={followUp.is_completed ? undefined : setDialog} />)}</div>
      )}

      {dialog && (
        <FollowUpDialog
          lead={lead}
          timeZone={timeZone}
          followUp={dialog === 'create' ? undefined : dialog}
          onClose={() => setDialog(null)}
        />
      )}
    </div>
  )
}
