import { useQueries } from '@tanstack/react-query'
import { CalendarCheck2, CircleAlert, LoaderCircle, RotateCcw } from 'lucide-react'
import { useState } from 'react'

import { useAuth } from '../auth/authStore'
import { getFollowUps } from './api'
import { FollowUpDialog } from './FollowUpDialog'
import { FollowUpItem } from './FollowUpItem'
import { followUpKeys } from './queryKeys'
import { followUpGroups } from './types'
import type { FollowUp, FollowUpGroup } from './types'

const groupContent: Record<FollowUpGroup, { title: string; description: string; empty: string }> = {
  overdue: {
    title: 'Overdue',
    description: 'Needs attention from a previous day.',
    empty: 'Nothing overdue.',
  },
  today: {
    title: 'Today',
    description: 'Scheduled for your local day.',
    empty: 'Nothing scheduled for today.',
  },
  upcoming: {
    title: 'Upcoming',
    description: 'Planned from tomorrow onward.',
    empty: 'No upcoming follow-ups.',
  },
  completed: {
    title: 'Completed',
    description: 'Recently finished follow-ups.',
    empty: 'No completed follow-ups yet.',
  },
}

export function FollowUpsPage() {
  const { user } = useAuth()
  const [editing, setEditing] = useState<FollowUp | null>(null)
  const queries = useQueries({
    queries: followUpGroups.map((group) => ({
      queryKey: followUpKeys.group(group),
      queryFn: () => getFollowUps({ group }),
    })),
  })
  const pending = queries.some((query) => query.isPending)
  const failed = queries.some((query) => query.isError)

  return (
    <section>
      <div>
        <p className="text-sm font-semibold text-blue-600">Daily workflow</p>
        <h2 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">Follow-ups</h2>
        <p className="mt-2 text-sm text-slate-600">Prioritize the next conversation in {user?.timezone || 'your timezone'}.</p>
      </div>

      {pending ? (
        <div className="mt-7 grid min-h-64 place-items-center rounded-2xl border border-slate-200 bg-white"><LoaderCircle aria-label="Loading follow-ups" className="size-7 animate-spin text-blue-600" /></div>
      ) : failed ? (
        <div className="mt-7 rounded-2xl border border-red-200 bg-white p-10 text-center">
          <CircleAlert className="mx-auto size-8 text-red-500" />
          <h3 className="mt-4 font-semibold">Follow-ups could not be loaded</h3>
          <button type="button" onClick={() => queries.forEach((query) => void query.refetch())} className="mt-5 inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-300 px-4 text-sm font-semibold"><RotateCcw className="size-4" /> Retry</button>
        </div>
      ) : (
        <div className="mt-7 grid gap-5 xl:grid-cols-2">
          {followUpGroups.map((group, index) => {
            const content = groupContent[group]
            const items = queries[index].data?.items || []
            return (
              <section key={group} aria-labelledby={`${group}-heading`} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                <div className="flex items-start justify-between gap-4">
                  <div><h3 id={`${group}-heading`} className="text-lg font-semibold text-slate-900">{content.title}</h3><p className="mt-1 text-sm text-slate-600">{content.description}</p></div>
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-600">{items.length}</span>
                </div>
                {items.length === 0 ? (
                  <p className="mt-5 flex items-center gap-2 rounded-xl bg-slate-50 p-4 text-sm text-slate-500"><CalendarCheck2 className="size-4" /> {content.empty}</p>
                ) : (
                  <div className="mt-5 space-y-3">{items.map((followUp) => <FollowUpItem key={followUp.id} followUp={followUp} timeZone={user?.timezone || 'UTC'} onEdit={followUp.is_completed ? undefined : setEditing} />)}</div>
                )}
              </section>
            )
          })}
        </div>
      )}

      {editing && (
        <FollowUpDialog
          lead={editing.lead}
          timeZone={user?.timezone || 'UTC'}
          followUp={editing}
          onClose={() => setEditing(null)}
        />
      )}
    </section>
  )
}
