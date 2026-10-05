import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  Building2,
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

import { ConfirmDialog } from '../../components/ui/ConfirmDialog'
import { useToast } from '../../components/ui/toast'
import { ApiError } from '../../lib/apiClient'
import { useAuth } from '../auth/authStore'
import { dashboardKeys } from '../dashboard/queryKeys'
import { followUpKeys } from '../followups/queryKeys'
import { LeadFollowUpsSection } from '../followups/LeadFollowUpsSection'
import { LeadQuotationsSection } from '../quotations/LeadQuotationsSection'
import { quotationKeys } from '../quotations/queryKeys'
import { archiveLead, getLead } from './api'
import { formatDate, formatMoney, sourceLabels } from './formatting'
import { leadKeys } from './queryKeys'
import { StatusBadge } from './StatusBadge'

export function LeadDetailPage() {
  const { id = '' } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { notify } = useToast()
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
      // Archiving hides the lead's quotations and follow-ups everywhere, including the dashboard.
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: leadKeys.lists() }),
        queryClient.invalidateQueries({ queryKey: quotationKeys.all }),
        queryClient.invalidateQueries({ queryKey: followUpKeys.all }),
        queryClient.invalidateQueries({ queryKey: dashboardKeys.all }),
      ])
      setConfirmArchive(false)
      notify({
        title: 'Lead archived',
        description: `${leadQuery.data?.contact_name || 'The lead'} was removed from the active pipeline.`,
        tone: 'success',
      })
      navigate('/leads', { replace: true })
    },
    onError: (error) => {
      notify({
        title: 'Lead was not archived',
        description: error instanceof ApiError ? error.message : 'Please try again.',
        tone: 'error',
      })
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
          <Link to={`/leads/${lead.id}/quotes/new`} className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50">
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

          <LeadQuotationsSection leadId={lead.id} />
        </div>

        <div className="space-y-5">
          <LeadFollowUpsSection lead={lead} />

          <div className="rounded-2xl border border-red-200 bg-white p-5 shadow-sm">
            <h3 className="font-semibold text-slate-900">Archive lead</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">Remove this lead from the active pipeline. Its record remains preserved.</p>
            <button type="button" onClick={() => setConfirmArchive(true)} className="mt-4 inline-flex min-h-11 items-center gap-2 rounded-xl border border-red-200 px-4 text-sm font-semibold text-red-700 hover:bg-red-50">
              <Trash2 className="size-4" aria-hidden="true" /> Archive lead
            </button>
          </div>
        </div>
      </div>

      <ConfirmDialog
        open={confirmArchive}
        title={`Archive ${lead.contact_name}?`}
        description="This lead will disappear from active lists and searches. This action cannot currently be undone in the app."
        confirmLabel="Archive lead"
        busyLabel="Archiving…"
        busy={archiveMutation.isPending}
        error={archiveMutation.isError ? 'The lead could not be archived. Please try again.' : undefined}
        onCancel={() => setConfirmArchive(false)}
        onConfirm={() => archiveMutation.mutate()}
      />
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
