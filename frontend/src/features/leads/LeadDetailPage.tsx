import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  Building2,
  CalendarClock,
  CircleAlert,
  FilePlus2,
  LoaderCircle,
  Mail,
  Pencil,
  Phone,
  Trash2,
} from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ApiError } from '../../lib/apiClient'
import { useAuth } from '../auth/authStore'
import { archiveLead, getLead } from './api'
import { formatDate, formatMoney, sourceLabels } from './formatting'
import { leadKeys } from './queryKeys'
import { StatusBadge } from './StatusBadge'

export function LeadDetailPage() {
  const { id = '' } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [confirmArchive, setConfirmArchive] = useState(false)

  const leadQuery = useQuery({
    queryKey: leadKeys.detail(id),
    queryFn: () => getLead(id),
    enabled: Boolean(id),
    retry: (failureCount, error) => !(error instanceof ApiError && error.status === 404) && failureCount < 2,
  })

  const archiveMutation = useMutation({
    mutationFn: () => archiveLead(id),
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey: leadKeys.detail(id) })
      await queryClient.invalidateQueries({ queryKey: leadKeys.lists() })
      navigate('/leads', { replace: true })
    },
  })

  if (leadQuery.isPending) {
    return <DetailState icon={<LoaderCircle className="size-6 animate-spin" />} title="Loading lead…" />
  }

  if (leadQuery.isError) {
    const missing = leadQuery.error instanceof ApiError && leadQuery.error.status === 404
    return (
      <DetailState
        icon={<CircleAlert className="size-6" />}
        title={missing ? 'Lead not found' : 'Lead could not be loaded'}
        description={
          missing
            ? 'This lead may have been archived, removed, or belongs to another workspace.'
            : 'Check your connection and try again.'
        }
        retry={missing ? undefined : () => void leadQuery.refetch()}
      />
    )
  }

  const lead = leadQuery.data

  return (
    <section className="mx-auto max-w-6xl">
      <Link to="/leads" className="mb-5 inline-flex min-h-11 items-center gap-2 text-sm font-semibold text-slate-600 hover:text-slate-900">
        <ArrowLeft className="size-4" aria-hidden="true" /> Back to leads
      </Link>

      <div className="flex flex-col gap-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-3xl font-bold tracking-tight text-slate-950">{lead.contact_name}</h2>
            <StatusBadge status={lead.status} />
          </div>
          <p className="mt-2 text-slate-600">{lead.company || 'No company added'}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to={`/quotations/new?lead_id=${lead.id}`} className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50">
            <FilePlus2 className="size-4" aria-hidden="true" /> Create quotation
          </Link>
          <Link to={`/leads/${lead.id}/edit`} className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-blue-600 px-4 text-sm font-semibold text-white hover:bg-blue-700">
            <Pencil className="size-4" aria-hidden="true" /> Edit
          </Link>
        </div>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1.35fr)_minmax(18rem,.65fr)]">
        <div className="space-y-5">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
            <h3 className="text-lg font-semibold text-slate-900">Contact and opportunity</h3>
            <dl className="mt-6 grid gap-6 sm:grid-cols-2">
              <DetailItem icon={<Building2 />} label="Company" value={lead.company || 'Not provided'} />
              <DetailItem icon={<Mail />} label="Email" value={lead.email || 'Not provided'} href={lead.email ? `mailto:${lead.email}` : undefined} />
              <DetailItem icon={<Phone />} label="Phone" value={lead.phone || 'Not provided'} href={lead.phone ? `tel:${lead.phone}` : undefined} />
              <DetailItem label="Source" value={lead.source ? sourceLabels[lead.source] : 'Not specified'} />
              <DetailItem label="Estimated value" value={formatMoney(lead.estimated_value, user?.currency_code)} />
              <DetailItem label="Created" value={formatDate(lead.created_at, user?.timezone)} />
            </dl>
            <div className="mt-7 border-t border-slate-200 pt-6">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Notes</p>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-slate-700">{lead.notes || 'No notes added yet.'}</p>
            </div>
          </div>

          <ReservedSection
            title="Quotations"
            description="Quotes connected to this lead will appear here."
            action="Create quotation"
            to={`/quotations/new?lead_id=${lead.id}`}
            icon={<FilePlus2 className="size-5" />}
          />
        </div>

        <div className="space-y-5">
          <ReservedSection
            title="Follow-ups"
            description="Scheduled conversations and reminders will appear here."
            action="Add follow-up"
            to={`/follow-ups/new?lead_id=${lead.id}`}
            icon={<CalendarClock className="size-5" />}
          />

          <div className="rounded-2xl border border-red-200 bg-white p-5 shadow-sm">
            <h3 className="font-semibold text-slate-900">Archive lead</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">Remove this lead from the active pipeline. Its record remains preserved.</p>
            <button type="button" onClick={() => setConfirmArchive(true)} className="mt-4 inline-flex min-h-11 items-center gap-2 rounded-xl border border-red-200 px-4 text-sm font-semibold text-red-700 hover:bg-red-50">
              <Trash2 className="size-4" aria-hidden="true" /> Archive lead
            </button>
          </div>
        </div>
      </div>

      {confirmArchive && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4 backdrop-blur-sm">
          <div role="dialog" aria-modal="true" aria-labelledby="archive-title" className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <h2 id="archive-title" className="text-xl font-bold text-slate-950">Archive {lead.contact_name}?</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">This lead will disappear from active lists and searches. This action cannot currently be undone in the app.</p>
            {archiveMutation.isError && <p role="alert" className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">The lead could not be archived. Please try again.</p>}
            <div className="mt-6 flex justify-end gap-3">
              <button type="button" disabled={archiveMutation.isPending} onClick={() => setConfirmArchive(false)} className="min-h-11 rounded-xl border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50">Cancel</button>
              <button type="button" disabled={archiveMutation.isPending} onClick={() => archiveMutation.mutate()} className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-red-600 px-4 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60">
                {archiveMutation.isPending && <LoaderCircle className="size-4 animate-spin" />}
                {archiveMutation.isPending ? 'Archiving…' : 'Archive lead'}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}

function DetailItem({ icon, label, value, href }: { icon?: React.ReactNode; label: string; value: string; href?: string }) {
  return (
    <div className="flex gap-3">
      {icon && <span className="mt-0.5 text-slate-400 [&>svg]:size-4">{icon}</span>}
      <div>
        <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</dt>
        <dd className="mt-1 text-sm font-medium text-slate-800">{href ? <a href={href} className="text-blue-600 hover:underline">{value}</a> : value}</dd>
      </div>
    </div>
  )
}

function ReservedSection({ title, description, action, to, icon }: { title: string; description: string; action: string; to: string; icon: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-semibold text-slate-900">{title}</h3>
          <p className="mt-1 text-sm leading-6 text-slate-600">{description}</p>
        </div>
        <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-blue-50 text-blue-600">{icon}</span>
      </div>
      <Link to={to} className="mt-5 inline-flex min-h-11 items-center text-sm font-semibold text-blue-600 hover:text-blue-700">{action} →</Link>
    </div>
  )
}

function DetailState({ icon, title, description, retry }: { icon: React.ReactNode; title: string; description?: string; retry?: () => void }) {
  return (
    <div className="grid min-h-[55vh] place-items-center rounded-2xl border border-slate-200 bg-white p-8 text-center">
      <div className="max-w-md">
        <span className="mx-auto grid size-12 place-items-center rounded-full bg-slate-100 text-slate-500">{icon}</span>
        <h2 className="mt-4 text-xl font-semibold text-slate-900">{title}</h2>
        {description && <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>}
        <div className="mt-5 flex justify-center gap-3">
          {retry && <button type="button" onClick={retry} className="min-h-11 rounded-xl border border-slate-300 px-4 text-sm font-semibold">Retry</button>}
          <Link to="/leads" className="inline-flex min-h-11 items-center rounded-xl bg-blue-600 px-4 text-sm font-semibold text-white">Return to leads</Link>
        </div>
      </div>
    </div>
  )
}
