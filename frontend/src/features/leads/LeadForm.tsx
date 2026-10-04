import { zodResolver } from '@hookform/resolvers/zod'
import { LoaderCircle } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { ApiError } from '../../lib/apiClient'
import { sourceLabels, statusLabels } from './formatting'
import { leadSources, leadStatuses } from './types'
import type { LeadPayload } from './types'

const optionalEmail = z
  .string()
  .trim()
  .max(254, 'Email must be 254 characters or fewer.')
  .refine((value) => !value || z.email().safeParse(value).success, 'Enter a valid email address.')

const leadFormSchema = z.object({
  contact_name: z.string().trim().min(1, 'Contact name is required.').max(100),
  company: z.string().trim().max(150),
  email: optionalEmail,
  phone: z.string().trim().max(50),
  source: z.union([z.literal(''), z.enum(leadSources)]),
  status: z.enum(leadStatuses),
  estimated_value: z
    .string()
    .trim()
    .min(1, 'Estimated value is required.')
    .refine(
      (value) => /^\d{1,12}(\.\d{1,2})?$/.test(value),
      'Use a positive amount with up to two decimal places.',
    ),
  notes: z.string().trim().max(5000),
})

export type LeadFormValues = z.infer<typeof leadFormSchema>

function toPayload(values: LeadFormValues): LeadPayload {
  return {
    contact_name: values.contact_name.trim(),
    company: values.company.trim() || null,
    email: values.email.trim().toLowerCase() || null,
    phone: values.phone.trim() || null,
    source: values.source || null,
    status: values.status,
    estimated_value: values.estimated_value.trim(),
    notes: values.notes.trim() || null,
  }
}

type LeadFormProps = {
  defaultValues: LeadFormValues
  submitLabel: string
  onSubmit: (payload: LeadPayload) => Promise<void>
}

const inputClass =
  'mt-2 block min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10'

export function LeadForm({ defaultValues, submitLabel, onSubmit }: LeadFormProps) {
  const [generalError, setGeneralError] = useState('')
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LeadFormValues>({
    resolver: zodResolver(leadFormSchema),
    defaultValues,
  })

  const submit = handleSubmit(async (values) => {
    setGeneralError('')
    try {
      await onSubmit(toPayload(values))
    } catch (error) {
      setGeneralError(
        error instanceof ApiError ? error.message : 'We could not save this lead. Please try again.',
      )
    }
  })

  return (
    <form onSubmit={(event) => void submit(event)} noValidate className="space-y-6">
      {generalError && (
        <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {generalError}
        </div>
      )}

      <div className="grid gap-5 sm:grid-cols-2">
        <Field htmlFor="contact_name" label="Contact name" error={errors.contact_name?.message} required>
          <input id="contact_name" {...register('contact_name')} autoComplete="name" className={inputClass} />
        </Field>

        <Field htmlFor="company" label="Company" error={errors.company?.message}>
          <input id="company" {...register('company')} autoComplete="organization" className={inputClass} />
        </Field>

        <Field htmlFor="email" label="Email" error={errors.email?.message}>
          <input id="email" {...register('email')} type="email" autoComplete="email" className={inputClass} />
        </Field>

        <Field htmlFor="phone" label="Phone" error={errors.phone?.message}>
          <input id="phone" {...register('phone')} type="tel" autoComplete="tel" className={inputClass} />
        </Field>

        <Field htmlFor="source" label="Source" error={errors.source?.message}>
          <select id="source" {...register('source')} className={inputClass}>
            <option value="">Not specified</option>
            {leadSources.map((source) => (
              <option key={source} value={source}>
                {sourceLabels[source]}
              </option>
            ))}
          </select>
        </Field>

        <Field htmlFor="status" label="Status" error={errors.status?.message} required>
          <select id="status" {...register('status')} className={inputClass}>
            {leadStatuses.map((status) => (
              <option key={status} value={status}>
                {statusLabels[status]}
              </option>
            ))}
          </select>
        </Field>

        <Field htmlFor="estimated_value" label="Estimated value" error={errors.estimated_value?.message} required>
          <input
            id="estimated_value"
            {...register('estimated_value')}
            type="number"
            min="0"
            max="999999999999.99"
            step="0.01"
            inputMode="decimal"
            className={inputClass}
          />
        </Field>
      </div>

      <Field htmlFor="notes" label="Notes" error={errors.notes?.message}>
        <textarea id="notes" {...register('notes')} rows={6} className={`${inputClass} resize-y`} />
      </Field>

      <div className="flex justify-end border-t border-slate-200 pt-6">
        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting && <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />}
          {isSubmitting ? 'Saving…' : submitLabel}
        </button>
      </div>
    </form>
  )
}

function Field({
  htmlFor,
  label,
  error,
  required = false,
  children,
}: {
  htmlFor: string
  label: string
  error?: string
  required?: boolean
  children: React.ReactNode
}) {
  return (
    <div className="block text-sm font-medium text-slate-700">
      <label htmlFor={htmlFor}>
        {label}
        {required && <span className="ml-1 text-red-500" aria-hidden="true">*</span>}
      </label>
      {children}
      {error && <span className="mt-1.5 block text-xs font-medium text-red-600">{error}</span>}
    </div>
  )
}
