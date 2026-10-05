import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { LoaderCircle, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { ApiError } from '../../lib/apiClient'
import { leadKeys } from '../leads/queryKeys'
import { createFollowUp, updateFollowUp } from './api'
import { defaultFollowUpLocal, isoToLocalInput, zonedLocalToIso } from './dateTime'
import { followUpKeys } from './queryKeys'
import type { FollowUp } from './types'

const formSchema = z.object({
  due_local: z.string().min(1, 'Choose a due date and time.'),
  note: z.string().trim().min(1, 'A note is required.').max(5000),
})

type FormValues = z.infer<typeof formSchema>

export function FollowUpDialog({
  lead,
  timeZone,
  followUp,
  onClose,
}: {
  lead: { id: string; contact_name: string }
  timeZone: string
  followUp?: FollowUp
  onClose: () => void
}) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const queryClient = useQueryClient()
  const [generalError, setGeneralError] = useState('')
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      due_local: followUp
        ? isoToLocalInput(followUp.due_at, timeZone)
        : defaultFollowUpLocal(timeZone),
      note: followUp?.note || '',
    },
  })

  useEffect(() => {
    const dialog = dialogRef.current
    if (dialog && !dialog.open) dialog.showModal()
    return () => {
      if (dialog?.open) dialog.close()
    }
  }, [])

  const mutation = useMutation({
    mutationFn: (values: FormValues) => {
      const payload = {
        note: values.note.trim(),
        due_at: zonedLocalToIso(values.due_local, timeZone),
      }
      return followUp
        ? updateFollowUp(followUp.id, payload)
        : createFollowUp(lead.id, payload)
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: followUpKeys.all }),
        queryClient.invalidateQueries({ queryKey: leadKeys.detail(lead.id) }),
        queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
      ])
      onClose()
    },
  })

  const submit = handleSubmit(async (values) => {
    setGeneralError('')
    try {
      await mutation.mutateAsync(values)
    } catch (error) {
      setGeneralError(
        error instanceof ApiError ? error.message : 'The follow-up could not be saved. Please try again.',
      )
    }
  })

  const inputClass =
    'mt-2 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10'

  return (
    <dialog
      ref={dialogRef}
      onCancel={(event) => {
        event.preventDefault()
        onClose()
      }}
      aria-labelledby="follow-up-dialog-title"
      className="m-auto w-[calc(100%_-_2rem)] max-w-lg rounded-2xl bg-white p-0 text-slate-900 shadow-2xl backdrop:bg-slate-950/55 backdrop:backdrop-blur-sm"
    >
      <form onSubmit={(event) => void submit(event)} noValidate>
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-5 sm:px-6">
          <div>
            <p className="text-sm font-semibold text-blue-600">{lead.contact_name}</p>
            <h2 id="follow-up-dialog-title" className="mt-1 text-xl font-bold">
              {followUp ? 'Edit follow-up' : 'Add follow-up'}
            </h2>
          </div>
          <button type="button" onClick={onClose} aria-label="Close follow-up dialog" className="grid size-10 place-items-center rounded-lg text-slate-500 hover:bg-slate-100">
            <X className="size-5" />
          </button>
        </div>

        <div className="space-y-5 px-5 py-6 sm:px-6">
          {generalError && <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{generalError}</p>}
          <label className="block text-sm font-medium text-slate-700">
            Due date and time
            <input type="datetime-local" {...register('due_local')} className={inputClass} />
            <span className="mt-1.5 block text-xs text-slate-500">Shown in {timeZone}.</span>
            {errors.due_local && <span className="mt-1 block text-xs font-medium text-red-600">{errors.due_local.message}</span>}
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Note
            <textarea autoFocus rows={5} {...register('note')} className={`${inputClass} py-3`} placeholder="What needs to happen next?" />
            {errors.note && <span className="mt-1.5 block text-xs font-medium text-red-600">{errors.note.message}</span>}
          </label>
        </div>

        <div className="flex justify-end gap-3 border-t border-slate-200 px-5 py-4 sm:px-6">
          <button type="button" disabled={isSubmitting} onClick={onClose} className="min-h-11 rounded-xl border border-slate-300 px-4 text-sm font-semibold text-slate-700">Cancel</button>
          <button type="submit" disabled={isSubmitting} className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-blue-600 px-4 text-sm font-semibold text-white disabled:opacity-60">
            {isSubmitting && <LoaderCircle className="size-4 animate-spin" />}
            {isSubmitting ? 'Saving…' : followUp ? 'Save changes' : 'Add follow-up'}
          </button>
        </div>
      </form>
    </dialog>
  )
}
