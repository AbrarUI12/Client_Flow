import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { ArrowLeft, ArrowRight, CircleAlert, FileText, RotateCcw, Search } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'

import { useAuth } from '../auth/authStore'
import { formatMoney } from '../leads/formatting'
import { useDebouncedValue } from '../leads/useDebouncedValue'
import { getQuotations } from './api'
import { formatPlainDate, quotationStatusLabels } from './formatting'
import { quotationKeys } from './queryKeys'
import { QuotationStatusBadge } from './QuotationStatusBadge'
import { quotationStatuses } from './types'
import type { Quotation, QuotationListParams, QuotationStatus } from './types'

const pageSize = 10

export function QuotationsPage() {
  const { user } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const rawSearch = searchParams.get('search') || ''
  const search = useDebouncedValue(rawSearch.trim(), 350)
  const rawStatus = searchParams.get('status')
  const status: QuotationStatus | '' = quotationStatuses.includes(rawStatus as QuotationStatus)
    ? (rawStatus as QuotationStatus)
    : ''
  const rawPage = Number(searchParams.get('page') || '1')
  const page = Number.isInteger(rawPage) && rawPage > 0 ? rawPage : 1
  const params: QuotationListParams = { page, pageSize, search, status }
  const quotationsQuery = useQuery({
    queryKey: quotationKeys.list(params),
    queryFn: () => getQuotations(params),
    placeholderData: keepPreviousData,
  })

  function updateParam(name: 'search' | 'status', value: string) {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(name, value)
    else next.delete(name)
    next.delete('page')
    setSearchParams(next, { replace: name === 'search' })
  }

  function changePage(nextPage: number) {
    const next = new URLSearchParams(searchParams)
    if (nextPage > 1) next.set('page', String(nextPage))
    else next.delete('page')
    setSearchParams(next)
  }

  const data = quotationsQuery.data
  const hasFilters = Boolean(rawSearch || status)

  return (
    <section>
      <div>
        <p className="text-sm font-semibold text-blue-600">Sales documents</p>
        <h2 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">Quotations</h2>
        <p className="mt-2 text-sm text-slate-600">Review proposals, totals, and customer decisions in one place.</p>
      </div>

      <div className="mt-7 rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="grid gap-3 border-b border-slate-200 p-4 sm:grid-cols-[minmax(15rem,1fr)_13rem] sm:p-5">
          <label className="relative">
            <span className="sr-only">Search quotations</span>
            <Search className="pointer-events-none absolute left-3.5 top-3.5 size-4 text-slate-400" />
            <input type="search" value={rawSearch} onChange={(event) => updateParam('search', event.target.value)} placeholder="Search quote or client…" className="min-h-11 w-full rounded-xl border border-slate-300 pl-10 pr-3 text-sm outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10" />
          </label>
          <label>
            <span className="sr-only">Filter quotations by status</span>
            <select value={status} onChange={(event) => updateParam('status', event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10">
              <option value="">All statuses</option>
              {quotationStatuses.map((option) => <option key={option} value={option}>{quotationStatusLabels[option]}</option>)}
            </select>
          </label>
        </div>

        {quotationsQuery.isPending ? (
          <ListSkeleton />
        ) : quotationsQuery.isError ? (
          <div className="px-5 py-16 text-center">
            <CircleAlert className="mx-auto size-9 text-red-500" />
            <h3 className="mt-4 font-semibold">Quotations could not be loaded</h3>
            <button type="button" onClick={() => void quotationsQuery.refetch()} className="mt-5 inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-300 px-4 text-sm font-semibold"><RotateCcw className="size-4" /> Retry</button>
          </div>
        ) : data && data.items.length === 0 ? (
          <div className="px-5 py-16 text-center">
            <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-blue-50 text-blue-600"><FileText className="size-6" /></span>
            <h3 className="mt-4 text-lg font-semibold">{hasFilters ? 'No quotations match these filters' : 'No quotations yet'}</h3>
            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-600">{hasFilters ? 'Try a different search or status.' : 'Open a lead and create its first quotation.'}</p>
            {hasFilters ? (
              <button type="button" onClick={() => setSearchParams({})} className="mt-5 min-h-11 rounded-xl border border-slate-300 px-4 text-sm font-semibold">Clear filters</button>
            ) : (
              <Link to="/leads" className="mt-5 inline-flex min-h-11 items-center rounded-xl bg-blue-600 px-4 text-sm font-semibold text-white">Choose a lead</Link>
            )}
          </div>
        ) : data ? (
          <>
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr><th className="px-5 py-3.5">Quote</th><th className="px-5 py-3.5">Client</th><th className="px-5 py-3.5">Dates</th><th className="px-5 py-3.5">Status</th><th className="px-5 py-3.5 text-right">Total</th></tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.items.map((quotation) => <QuotationRow key={quotation.id} quotation={quotation} currency={user?.currency_code} />)}
                </tbody>
              </table>
            </div>
            <div className="divide-y divide-slate-100 md:hidden">
              {data.items.map((quotation) => <QuotationCard key={quotation.id} quotation={quotation} currency={user?.currency_code} />)}
            </div>
            <div className="flex flex-col gap-3 border-t border-slate-200 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-slate-600">Page {data.page} of {Math.max(data.pages, 1)} · {data.total} total</p>
              <div className="flex gap-2">
                <button type="button" disabled={page <= 1} onClick={() => changePage(page - 1)} className="inline-flex min-h-10 items-center gap-1 rounded-lg border border-slate-300 px-3 text-sm font-semibold disabled:opacity-40"><ArrowLeft className="size-4" /> Previous</button>
                <button type="button" disabled={page >= data.pages} onClick={() => changePage(page + 1)} className="inline-flex min-h-10 items-center gap-1 rounded-lg border border-slate-300 px-3 text-sm font-semibold disabled:opacity-40">Next <ArrowRight className="size-4" /></button>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </section>
  )
}

function QuotationRow({ quotation, currency }: { quotation: Quotation; currency?: string }) {
  return (
    <tr className="hover:bg-slate-50">
      <td className="px-5 py-4"><Link to={`/quotations/${quotation.id}`} className="font-semibold text-blue-600 hover:underline">{quotation.quote_number}</Link></td>
      <td className="px-5 py-4"><p className="font-medium text-slate-900">{quotation.lead.contact_name}</p><p className="text-xs text-slate-500">{quotation.lead.company || 'No company'}</p></td>
      <td className="px-5 py-4 text-slate-600"><p>{formatPlainDate(quotation.issue_date)}</p><p className="text-xs">Valid to {formatPlainDate(quotation.valid_until)}</p></td>
      <td className="px-5 py-4"><QuotationStatusBadge status={quotation.status} /></td>
      <td className="px-5 py-4 text-right font-semibold">{formatMoney(quotation.total, currency)}</td>
    </tr>
  )
}

function QuotationCard({ quotation, currency }: { quotation: Quotation; currency?: string }) {
  return (
    <Link to={`/quotations/${quotation.id}`} className="block p-5 hover:bg-slate-50">
      <div className="flex items-start justify-between gap-3"><div><p className="font-semibold text-blue-600">{quotation.quote_number}</p><h3 className="mt-1 font-medium text-slate-900">{quotation.lead.contact_name}</h3></div><QuotationStatusBadge status={quotation.status} /></div>
      <div className="mt-4 flex items-end justify-between"><p className="text-xs text-slate-500">Valid to {formatPlainDate(quotation.valid_until)}</p><p className="font-semibold">{formatMoney(quotation.total, currency)}</p></div>
    </Link>
  )
}

function ListSkeleton() {
  return <div aria-label="Loading quotations" className="animate-pulse space-y-5 p-5">{[0, 1, 2, 3].map((item) => <div key={item} className="flex gap-5"><div className="h-5 w-28 rounded bg-slate-200" /><div className="h-5 flex-1 rounded bg-slate-100" /><div className="h-5 w-24 rounded bg-slate-200" /></div>)}</div>
}
