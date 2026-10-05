import { useQuery } from '@tanstack/react-query'
import {
  AlertTriangle,
  ArrowRight,
  CalendarClock,
  CircleAlert,
  FileText,
  LoaderCircle,
  RotateCcw,
  Users,
  WalletCards,
} from 'lucide-react'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/authStore'
import { formatFollowUpDate } from '../followups/dateTime'
import type { FollowUp } from '../followups/types'
import { formatMoney } from '../leads/formatting'
import { statusLabels } from '../leads/formatting'
import { leadStatuses } from '../leads/types'
import { StatusBadge } from '../leads/StatusBadge'
import { getDashboardSummary } from './api'
import { dashboardKeys } from './queryKeys'

const pipelineTones = [
  'bg-blue-500',
  'bg-violet-500',
  'bg-amber-500',
  'bg-cyan-500',
  'bg-emerald-500',
  'bg-slate-500',
]

export function DashboardPage() {
  const { user } = useAuth()
  const summaryQuery = useQuery({
    queryKey: dashboardKeys.summary(),
    queryFn: getDashboardSummary,
  })

  if (summaryQuery.isPending) return <DashboardSkeleton />
  if (summaryQuery.isError) {
    return (
      <div className="grid min-h-[60vh] place-items-center rounded-2xl border border-red-200 bg-white p-8 text-center">
        <div>
          <CircleAlert className="mx-auto size-9 text-red-500" />
          <h2 className="mt-4 text-xl font-semibold">Dashboard could not be loaded</h2>
          <p className="mt-2 text-sm text-slate-600">Check the API connection and try again.</p>
          <button type="button" onClick={() => void summaryQuery.refetch()} className="mt-5 inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-300 px-4 text-sm font-semibold"><RotateCcw className="size-4" /> Retry</button>
        </div>
      </div>
    )
  }

  const summary = summaryQuery.data
  const maxPipeline = Math.max(...Object.values(summary.pipeline_counts), 1)
  const metrics = [
    { label: 'Total leads', value: String(summary.total_leads), icon: Users, tone: 'bg-blue-50 text-blue-700', to: '/leads' },
    { label: 'Open quotations', value: String(summary.open_quotation_count), icon: FileText, tone: 'bg-violet-50 text-violet-700', to: '/quotations' },
    { label: 'Open quote value', value: formatMoney(summary.open_quotation_value, user?.currency_code), icon: WalletCards, tone: 'bg-emerald-50 text-emerald-700', to: '/quotations' },
    { label: 'Overdue follow-ups', value: String(summary.overdue_followup_count), icon: AlertTriangle, tone: 'bg-amber-50 text-amber-700', to: '/follow-ups' },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold text-blue-600">Operational overview</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-[-0.03em] text-slate-950">
            Good to see you, {user?.full_name.split(' ')[0]}.
          </h2>
          <p className="mt-2 text-slate-600">Here is what needs attention across your sales workflow.</p>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-sm font-medium text-emerald-800">
          Session secured
        </div>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map(({ label, value, icon: Icon, tone, to }) => (
          <Link key={label} to={to} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
            <div className="flex items-center justify-between"><span className={`grid size-11 place-items-center rounded-xl ${tone}`}><Icon className="size-5" /></span><ArrowRight className="size-4 text-slate-300" /></div>
            <p className="mt-5 text-sm text-slate-500">{label}</p>
            <p className="mt-1 text-2xl font-bold tracking-tight text-slate-950">{value}</p>
          </Link>
        ))}
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(22rem,.85fr)]">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6" aria-labelledby="pipeline-heading">
          <div className="flex items-center justify-between gap-4"><div><h3 id="pipeline-heading" className="text-lg font-semibold">Lead pipeline</h3><p className="mt-1 text-sm text-slate-600">Active leads by current status.</p></div><Link to="/leads" className="text-sm font-semibold text-blue-600">View leads</Link></div>
          <div className="mt-6 space-y-4">
            {leadStatuses.map((status, index) => {
              const count = summary.pipeline_counts[status]
              return <div key={status}><div className="mb-1.5 flex justify-between text-sm"><span className="font-medium text-slate-700">{statusLabels[status]}</span><span className="font-bold text-slate-900">{count}</span></div><div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className={`h-full rounded-full ${pipelineTones[index]}`} style={{ width: `${(count / maxPipeline) * 100}%` }} /></div></div>
            })}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6" aria-labelledby="recent-heading">
          <div className="flex items-center justify-between"><div><h3 id="recent-heading" className="text-lg font-semibold">Recent leads</h3><p className="mt-1 text-sm text-slate-600">Latest additions to the pipeline.</p></div><Users className="size-5 text-slate-400" /></div>
          {summary.recent_leads.length === 0 ? <Empty text="No leads yet. Add one to start the pipeline." to="/leads/new" action="Add lead" /> : <div className="mt-5 divide-y divide-slate-100">{summary.recent_leads.map((lead) => <Link key={lead.id} to={`/leads/${lead.id}`} className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"><div className="min-w-0"><p className="truncate text-sm font-semibold text-slate-900">{lead.contact_name}</p><p className="mt-1 truncate text-xs text-slate-500">{lead.company || lead.email || 'No company'}</p></div><StatusBadge status={lead.status} /></Link>)}</div>}
        </section>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <FollowUpPanel title="Overdue follow-ups" description="From a previous local day." items={summary.overdue_followups} timeZone={user?.timezone || 'UTC'} empty="Nothing overdue." urgent />
        <FollowUpPanel title="Upcoming follow-ups" description="Today and the days ahead." items={summary.upcoming_followups} timeZone={user?.timezone || 'UTC'} empty="No upcoming follow-ups." />
      </div>
    </div>
  )
}

function FollowUpPanel({ title, description, items, timeZone, empty, urgent = false }: { title: string; description: string; items: FollowUp[]; timeZone: string; empty: string; urgent?: boolean }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex items-start justify-between gap-4"><div><h3 className="text-lg font-semibold">{title}</h3><p className="mt-1 text-sm text-slate-600">{description}</p></div><CalendarClock className={`size-5 ${urgent ? 'text-red-500' : 'text-blue-500'}`} /></div>
      {items.length === 0 ? <p className="mt-5 rounded-xl bg-slate-50 p-4 text-sm text-slate-500">{empty}</p> : <div className="mt-5 divide-y divide-slate-100">{items.map((item) => <Link key={item.id} to={`/leads/${item.lead_id}`} className="block py-3 first:pt-0 last:pb-0"><div className="flex justify-between gap-3"><p className="text-sm font-semibold text-slate-900">{item.lead.contact_name}</p><span className={`text-xs font-medium ${urgent ? 'text-red-600' : 'text-slate-500'}`}>{formatFollowUpDate(item.due_at, timeZone)}</span></div><p className="mt-1 line-clamp-1 text-sm text-slate-600">{item.note}</p></Link>)}</div>}
      <Link to="/follow-ups" className="mt-5 inline-flex min-h-10 items-center text-sm font-semibold text-blue-600">View all follow-ups →</Link>
    </section>
  )
}

function Empty({ text, to, action }: { text: string; to: string; action: string }) {
  return <div className="mt-5 rounded-xl bg-slate-50 p-4"><p className="text-sm text-slate-600">{text}</p><Link to={to} className="mt-2 inline-flex text-sm font-semibold text-blue-600">{action} →</Link></div>
}

function DashboardSkeleton() {
  return <div aria-label="Loading dashboard" className="mx-auto max-w-7xl animate-pulse"><div className="h-9 w-72 rounded bg-slate-200" /><div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[0, 1, 2, 3].map((item) => <div key={item} className="h-36 rounded-2xl border border-slate-200 bg-white" />)}</div><div className="mt-5 grid gap-5 xl:grid-cols-2"><div className="h-80 rounded-2xl bg-white" /><div className="h-80 rounded-2xl bg-white" /></div><div className="mt-5 flex justify-center"><LoaderCircle className="size-6 animate-spin text-blue-500" /></div></div>
}
