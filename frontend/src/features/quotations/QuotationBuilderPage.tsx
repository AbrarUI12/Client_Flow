import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  CircleAlert,
  LoaderCircle,
  Plus,
  Send,
  Trash2,
} from 'lucide-react'
import { cloneElement, useId, useMemo, useState } from 'react'
import type { ReactElement } from 'react'
import { useFieldArray, useForm, useWatch } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { z } from 'zod'

import { useToast } from '../../components/ui/toast'
import { ApiError } from '../../lib/apiClient'
import { useAuth } from '../auth/authStore'
import { getLead } from '../leads/api'
import { formatMoney } from '../leads/formatting'
import { leadKeys } from '../leads/queryKeys'
import { createQuotation, getQuotation, transitionQuotation, updateQuotation } from './api'
import { calculatePreview } from './calculation'
import { quotationKeys } from './queryKeys'
import type { Quotation, QuotationPayload } from './types'

const decimalPattern = /^\d{1,12}(\.\d{1,3})?$/
const moneyPattern = /^\d{1,12}(\.\d{1,2})?$/
const percentPattern = /^(?:100(?:\.0{1,2})?|\d{1,2}(?:\.\d{1,2})?)$/

const itemSchema = z.object({
  description: z.string().trim().min(1, 'Description is required.').max(500),
  quantity: z.string().trim().refine((value) => decimalPattern.test(value) && Number(value) > 0, 'Enter a quantity greater than zero (up to 3 decimals).'),
  unit_price: z.string().trim().refine((value) => moneyPattern.test(value), 'Enter a non-negative price with up to 2 decimals.'),
})

const builderSchema = z.object({
  issue_date: z.string().min(1, 'Issue date is required.'),
  valid_until: z.string().min(1, 'Valid-until date is required.'),
  discount_percent: z.string().trim().refine((value) => percentPattern.test(value), 'Enter a percentage from 0 to 100.'),
  tax_percent: z.string().trim().refine((value) => percentPattern.test(value), 'Enter a percentage from 0 to 100.'),
  notes: z.string().trim().max(5000),
  items: z.array(itemSchema).min(1),
}).refine((values) => values.valid_until >= values.issue_date, {
  path: ['valid_until'],
  message: 'Valid-until date must be on or after the issue date.',
})

type BuilderValues = z.infer<typeof builderSchema>
type SaveIntent = 'draft' | 'sent'

const blankItem = { description: '', quantity: '1.000', unit_price: '0.00' }

function dateInputValue(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function defaultBuilderValues(): BuilderValues {
  const issueDate = new Date()
  const validUntil = new Date(issueDate)
  validUntil.setDate(validUntil.getDate() + 14)
  return {
    issue_date: dateInputValue(issueDate),
    valid_until: dateInputValue(validUntil),
    discount_percent: '0.00',
    tax_percent: '0.00',
    notes: '',
    items: [{ ...blankItem }],
  }
}

function quotationToValues(quotation: Quotation): BuilderValues {
  return {
    issue_date: quotation.issue_date,
    valid_until: quotation.valid_until,
    discount_percent: quotation.discount_percent,
    tax_percent: quotation.tax_percent,
    notes: quotation.notes || '',
    items: quotation.items.map((item) => ({
      description: item.description,
      quantity: item.quantity,
      unit_price: item.unit_price,
    })),
  }
}

function toPayload(values: BuilderValues): QuotationPayload {
  return {
    issue_date: values.issue_date,
    valid_until: values.valid_until,
    discount_percent: values.discount_percent,
    tax_percent: values.tax_percent,
    notes: values.notes.trim() || null,
    items: values.items.map((item) => ({
      description: item.description.trim(),
      quantity: item.quantity,
      unit_price: item.unit_price,
    })),
  }
}

export function QuotationBuilderPage({ mode }: { mode: 'create' | 'edit' }) {
  const { leadId = '', id = '' } = useParams()
  const isEditing = mode === 'edit'
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { notify } = useToast()

  const quotationQuery = useQuery({
    queryKey: quotationKeys.detail(id),
    queryFn: () => getQuotation(id),
    enabled: isEditing && Boolean(id),
    retry: false,
  })
  const selectedLeadId = isEditing ? quotationQuery.data?.lead_id || '' : leadId
  const leadQuery = useQuery({
    queryKey: leadKeys.detail(selectedLeadId),
    queryFn: () => getLead(selectedLeadId),
    enabled: !isEditing && Boolean(selectedLeadId),
    retry: false,
  })

  if ((isEditing && quotationQuery.isPending) || (!isEditing && leadQuery.isPending)) {
    return <BuilderState title="Loading quotation builder…" loading />
  }
  if ((isEditing && quotationQuery.isError) || (!isEditing && leadQuery.isError)) {
    return <BuilderState title="The selected record could not be loaded." />
  }
  if (isEditing && quotationQuery.data?.status !== 'DRAFT') {
    return <BuilderState title="Only draft quotations can be edited." />
  }

  const quotation = quotationQuery.data
  const lead = isEditing ? quotation?.lead : leadQuery.data
  if (!lead) return <BuilderState title="Select a valid lead before creating a quotation." />

  return (
    <QuotationBuilderForm
      key={quotation?.id || lead.id}
      lead={lead}
      quotation={quotation}
      currency={user?.currency_code || 'USD'}
      onSaved={async (saved, intent) => {
        let finalQuotation = saved
        if (intent === 'sent') {
          finalQuotation = await transitionQuotation(saved.id, 'SENT')
        }
        queryClient.setQueryData(quotationKeys.detail(finalQuotation.id), finalQuotation)
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: quotationKeys.lists() }),
          queryClient.invalidateQueries({ queryKey: leadKeys.all }),
        ])
        notify({
          title: intent === 'sent' ? 'Quotation saved and sent' : 'Quotation draft saved',
          description: finalQuotation.quote_number,
          tone: 'success',
        })
        navigate(`/quotations/${finalQuotation.id}`, { replace: true })
      }}
    />
  )
}

function QuotationBuilderForm({
  lead,
  quotation,
  currency,
  onSaved,
}: {
  lead: { id: string; contact_name: string; company: string | null; email: string | null }
  quotation?: Quotation
  currency: string
  onSaved: (quotation: Quotation, intent: SaveIntent) => Promise<void>
}) {
  const [generalError, setGeneralError] = useState('')
  const [intent, setIntent] = useState<SaveIntent>('draft')
  const { notify } = useToast()
  const {
    register,
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<BuilderValues>({
    resolver: zodResolver(builderSchema),
    defaultValues: quotation ? quotationToValues(quotation) : defaultBuilderValues(),
  })
  const { fields, append, remove, update, move } = useFieldArray({ control, name: 'items' })
  const watchedItems = useWatch({ control, name: 'items' })
  const discount = useWatch({ control, name: 'discount_percent' })
  const tax = useWatch({ control, name: 'tax_percent' })
  const preview = useMemo(
    () => calculatePreview(watchedItems || [], discount || '0', tax || '0'),
    [discount, tax, watchedItems],
  )

  const saveMutation = useMutation({
    mutationFn: (payload: QuotationPayload) =>
      quotation ? updateQuotation(quotation.id, payload) : createQuotation(lead.id, payload),
  })

  const submit = handleSubmit(async (values, event) => {
    setGeneralError('')
    try {
      const submitter = (event?.nativeEvent as SubmitEvent | undefined)?.submitter
      const saveIntent: SaveIntent =
        submitter instanceof HTMLButtonElement && submitter.value === 'sent' ? 'sent' : 'draft'
      const saved = await saveMutation.mutateAsync(toPayload(values))
      await onSaved(saved, saveIntent)
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'The quotation could not be saved. Please try again.'
      setGeneralError(message)
      notify({ title: 'Quotation was not saved', description: message, tone: 'error' })
    }
  })

  const inputClass = 'mt-2 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10'

  return (
    <section className="mx-auto max-w-7xl">
      <Link to={quotation ? `/quotations/${quotation.id}` : `/leads/${lead.id}`} className="mb-5 inline-flex min-h-11 items-center gap-2 text-sm font-semibold text-slate-600 hover:text-slate-900">
        <ArrowLeft className="size-4" /> {quotation ? 'Back to quotation' : 'Back to lead'}
      </Link>

      <div className="mb-5 rounded-2xl border border-blue-200 bg-blue-50 p-5">
        <p className="text-xs font-bold uppercase tracking-wide text-blue-700">Selected client</p>
        <h2 className="mt-1 text-xl font-bold text-slate-950">{lead.contact_name}</h2>
        <p className="mt-1 text-sm text-slate-600">{lead.company || lead.email || 'No company or email provided'}</p>
      </div>

      <form onSubmit={(event) => void submit(event)} noValidate className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="space-y-5">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
            <div>
              <p className="text-sm font-semibold text-blue-600">{quotation ? quotation.quote_number : 'New draft'}</p>
              <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950">{quotation ? 'Edit quotation' : 'Build quotation'}</h1>
            </div>
            {generalError && <p role="alert" className="mt-5 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{generalError}</p>}

            <div className="mt-6 grid gap-5 sm:grid-cols-2">
              <BuilderField label="Issue date" error={errors.issue_date?.message}>
                <input type="date" {...register('issue_date')} className={inputClass} />
              </BuilderField>
              <BuilderField label="Valid until" error={errors.valid_until?.message}>
                <input type="date" {...register('valid_until')} className={inputClass} />
              </BuilderField>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Line items</h2>
                <p className="mt-1 text-sm text-slate-600">Use the arrows to keep the order clear.</p>
              </div>
              <button type="button" onClick={() => append({ ...blankItem })} className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-300 px-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">
                <Plus className="size-4" /> Add item
              </button>
            </div>

            <div className="mt-5 space-y-4">
              {fields.map((field, index) => (
                <div key={field.id} className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold text-slate-700">Item {index + 1}</p>
                    <div className="flex gap-1">
                      <IconButton label={`Move item ${index + 1} up`} disabled={index === 0} onClick={() => move(index, index - 1)} icon={<ArrowUp />} />
                      <IconButton label={`Move item ${index + 1} down`} disabled={index === fields.length - 1} onClick={() => move(index, index + 1)} icon={<ArrowDown />} />
                      <IconButton
                        label={`Remove item ${index + 1}`}
                        onClick={() => fields.length === 1 ? update(0, { ...blankItem }) : remove(index)}
                        icon={<Trash2 />}
                        danger
                      />
                    </div>
                  </div>
                  <div className="mt-3 grid gap-4 sm:grid-cols-[minmax(12rem,1fr)_9rem_11rem]">
                    <BuilderField label="Description" error={errors.items?.[index]?.description?.message}>
                      <input {...register(`items.${index}.description`)} className={inputClass} />
                    </BuilderField>
                    <BuilderField label="Quantity" error={errors.items?.[index]?.quantity?.message}>
                      <input type="number" min="0.001" step="0.001" {...register(`items.${index}.quantity`)} className={inputClass} />
                    </BuilderField>
                    <BuilderField label="Unit price" error={errors.items?.[index]?.unit_price?.message}>
                      <input type="number" min="0" step="0.01" {...register(`items.${index}.unit_price`)} className={inputClass} />
                    </BuilderField>
                  </div>
                  <p className="mt-3 text-right text-sm text-slate-600">Line total <span className="font-semibold text-slate-900">{formatMoney(preview.lineTotals[index] || '0.00', currency)}</span></p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
            <div className="grid gap-5 sm:grid-cols-2">
              <BuilderField label="Discount (%)" error={errors.discount_percent?.message}>
                <input type="number" min="0" max="100" step="0.01" {...register('discount_percent')} className={inputClass} />
              </BuilderField>
              <BuilderField label="Tax (%)" error={errors.tax_percent?.message}>
                <input type="number" min="0" max="100" step="0.01" {...register('tax_percent')} className={inputClass} />
              </BuilderField>
            </div>
            <BuilderField label="Notes" error={errors.notes?.message}>
              <textarea rows={5} {...register('notes')} className={`${inputClass} py-3`} />
            </BuilderField>
          </div>
        </div>

        <aside className="h-fit rounded-2xl border border-slate-200 bg-white p-5 shadow-sm xl:sticky xl:top-28">
          <h2 className="text-lg font-semibold text-slate-900">Calculation preview</h2>
          <p className="mt-1 text-xs leading-5 text-slate-500">Decimal-safe preview. The API recalculates authoritative totals when saved.</p>
          <dl className="mt-5 space-y-3 text-sm">
            <TotalRow label="Subtotal" value={preview.subtotal} currency={currency} />
            <TotalRow label="Discount" value={`-${preview.discountAmount}`} currency={currency} />
            <TotalRow label="Tax" value={preview.taxAmount} currency={currency} />
            <div className="border-t border-slate-200 pt-4">
              <TotalRow label="Total" value={preview.total} currency={currency} prominent />
            </div>
          </dl>
          {!preview.complete && <p className="mt-4 text-xs font-medium text-amber-700">Complete all numeric fields to update the preview.</p>}
          <div className="mt-6 grid gap-2">
            <button type="submit" value="draft" disabled={isSubmitting} onClick={() => setIntent('draft')} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-blue-200 bg-blue-50 px-4 text-sm font-semibold text-blue-700 hover:bg-blue-100 disabled:opacity-60">
              {isSubmitting && intent === 'draft' && <LoaderCircle className="size-4 animate-spin" />}
              Save draft
            </button>
            <button type="submit" value="sent" disabled={isSubmitting} onClick={() => setIntent('sent')} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60">
              {isSubmitting && intent === 'sent' ? <LoaderCircle className="size-4 animate-spin" /> : <Send className="size-4" />}
              Save and mark sent
            </button>
          </div>
        </aside>
      </form>
    </section>
  )
}

function BuilderField({
  label,
  error,
  children,
}: {
  label: string
  error?: string
  children: ReactElement<{
    'aria-invalid'?: boolean
    'aria-describedby'?: string
  }>
}) {
  const errorId = useId()
  const control = cloneElement(children, {
    'aria-invalid': Boolean(error),
    'aria-describedby': error ? errorId : children.props['aria-describedby'],
  })

  return (
    <label className="block text-sm font-medium text-slate-700">
      <span>{label}</span>
      {control}
      {error && <span id={errorId} className="mt-1.5 block text-xs font-medium text-red-600">{error}</span>}
    </label>
  )
}

function IconButton({ label, disabled = false, onClick, icon, danger = false }: { label: string; disabled?: boolean; onClick: () => void; icon: React.ReactNode; danger?: boolean }) {
  return (
    <button type="button" aria-label={label} title={label} disabled={disabled} onClick={onClick} className={`grid size-9 place-items-center rounded-lg disabled:opacity-30 ${danger ? 'text-red-600 hover:bg-red-50' : 'text-slate-500 hover:bg-slate-200'}`}>
      <span className="[&>svg]:size-4">{icon}</span>
    </button>
  )
}

function TotalRow({ label, value, currency, prominent = false }: { label: string; value: string; currency: string; prominent?: boolean }) {
  const negative = value.startsWith('-')
  const formatted = formatMoney(negative ? value.slice(1) : value, currency)
  return (
    <div className={`flex items-center justify-between gap-4 ${prominent ? 'text-lg font-bold text-slate-950' : 'text-slate-600'}`}>
      <dt>{label}</dt><dd className="font-semibold">{negative ? `−${formatted}` : formatted}</dd>
    </div>
  )
}

function BuilderState({ title, loading = false }: { title: string; loading?: boolean }) {
  return (
    <div className="grid min-h-[55vh] place-items-center rounded-2xl border border-slate-200 bg-white p-8 text-center">
      <div>
        {loading ? <LoaderCircle className="mx-auto size-8 animate-spin text-blue-600" /> : <CircleAlert className="mx-auto size-8 text-slate-400" />}
        <h2 className="mt-4 text-lg font-semibold text-slate-900">{title}</h2>
        <Link to="/quotations" className="mt-4 inline-flex min-h-11 items-center text-sm font-semibold text-blue-600">Return to quotations</Link>
      </div>
    </div>
  )
}
