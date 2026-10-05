import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, LoaderCircle, Pencil } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useToast } from '../../components/ui/toast'
import { ApiError } from '../../lib/apiClient'
import { completeFollowUp } from './api'
import { formatFollowUpDate } from './dateTime'
import { followUpKeys } from './queryKeys'
import type { FollowUp } from './types'

export function FollowUpItem({
  followUp,
  timeZone,
  showLead = true,
  onEdit,
}: {
  followUp: FollowUp
  timeZone: string
  showLead?: boolean
  onEdit?: (followUp: FollowUp) => void
}) {
  const queryClient = useQueryClient()
  const { notify } = useToast()
  const completion = useMutation({
    mutationFn: () => completeFollowUp(followUp.id),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: followUpKeys.all }),
        queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
      ])
      notify({
        title: 'Follow-up completed',
        description: `Reminder for ${followUp.lead.contact_name} is now complete.`,
        tone: 'success',
      })
    },
    onError: (error) => {
      notify({
        title: 'Follow-up was not completed',
        description: error instanceof ApiError ? error.message : 'Please try again.',
        tone: 'error',
      })
    },
  })

  return (
    <article className={`rounded-xl border p-4 ${followUp.is_completed ? 'border-slate-200 bg-slate-50/70' : 'border-slate-200 bg-white'}`}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          {showLead && (
            <Link to={`/leads/${followUp.lead_id}`} className="text-xs font-bold uppercase tracking-wide text-blue-600 hover:underline">
              {followUp.lead.contact_name}
            </Link>
          )}
          <p className={`${showLead ? 'mt-2' : ''} whitespace-pre-wrap text-sm leading-6 text-slate-800`}>{followUp.note}</p>
          <p className="mt-2 text-xs font-medium text-slate-500">
            {followUp.is_completed && followUp.completed_at
              ? `Completed ${formatFollowUpDate(followUp.completed_at, timeZone)}`
              : `Due ${formatFollowUpDate(followUp.due_at, timeZone)}`}
          </p>
        </div>
        {!followUp.is_completed && (
          <div className="flex shrink-0 gap-2">
            {onEdit && (
              <button type="button" onClick={() => onEdit(followUp)} className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-slate-300 px-3 text-xs font-semibold text-slate-700 hover:bg-slate-50">
                <Pencil className="size-3.5" /> Edit
              </button>
            )}
            <button type="button" disabled={completion.isPending} onClick={() => completion.mutate()} className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-emerald-600 px-3 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-60">
              {completion.isPending ? <LoaderCircle className="size-3.5 animate-spin" /> : <Check className="size-3.5" />}
              Complete
            </button>
          </div>
        )}
      </div>
      {completion.isError && <p role="alert" className="mt-3 text-xs font-medium text-red-600">This follow-up could not be completed. Try again.</p>}
    </article>
  )
}
