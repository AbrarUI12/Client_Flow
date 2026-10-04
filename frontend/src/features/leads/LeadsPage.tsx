import { keepPreviousData, useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  ArrowRight,
  CircleAlert,
  Plus,
  RotateCcw,
  Search,
  UserRoundSearch,
} from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'

import { useAuth } from '../auth/authStore'
import { getLeads } from './api'
import { formatDate, formatMoney, sourceLabels, statusLabels } from './formatting'
import { leadKeys } from './queryKeys'
import { StatusBadge } from './StatusBadge'
import { leadSources, leadStatuses } from './types'
import type { Lead, LeadListParams } from './types'
import { useDebouncedValue } from './useDebouncedValue'

const pageSize = 10

function readEnum<T extends string>(value: string | null, values: readonly T[]): T | '' {
  return value && values.includes(value as T) ? (value as T) : ''
}

export function LeadsPage() {
  const { user } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const rawSearch = searchParams.get('search') || ''
  const debouncedSearch = useDebouncedValue(rawSearch.trim(), 350)
  const status = readEnum(searchParams.get('status'), leadStatuses)
  const source = readEnum(searchParams.get('source'), leadSources)
  const requestedPage = Number(searchParams.get('page') || '1')
  const page = Number.isInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1

  const params: LeadListParams = {
    page,
    pageSize,
    search: debouncedSearch,
    status,
    source,
  }

  const leadsQuery = useQuery({
    queryKey: leadKeys.list(params),
    queryFn: () => getLeads(params),
    placeholderData: keepPreviousData,
  })

  function setFilter(name: 'search' | 'status' | 'source', value: string) {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(name, value)
    else next.delete(name)
    next.delete('page')
    setSearchParams(next, { replace: name === 'search' })
  }

  function setPage(nextPage: number) {
    const next = new URLSearchParams(searchParams)
    if (nextPage > 1) next.set('page', String(nextPage))
    else next.delete('page')
    setSearchParams(next)
  }

  function clearFilters() {
    setSearchParams({})
  }

  const hasFilters = Boolean(rawSearch || status || source)
  const data = leadsQuery.data

  return (
    <section>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-blue-600">Sales pipeline</p>
          <h2 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">Leads</h2>
          <p className="mt-2 text-sm text-slate-600">Track every prospect from first contact to final outcome.</p>
        </div>
        <Link
          to="/leads/new"
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
        >
          <Plus className="size-4" aria-hidden="true" />
          Add Lead
        </Link>
      </div>

      <div className="mt-7 rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="grid gap-3 border-b border-slate-200 p-4 sm:grid-cols-[minmax(15rem,1fr)_12rem_12rem] sm:p-5">
          <label className="relative block">
            <span className="sr-only">Search leads</span>
            <Search className="pointer-events-none absolute left-3.5 top-3.5 size-4 text-slate-400" aria-hidden="true" />
            <input
              type="search"
              value={rawSearch}
              onChange={(event) => setFilter('search', event.target.value)}
              placeholder="Search name, company, email, phone…"
              className="min-h-11 w-full rounded-xl border border-slate-300 bg-white pl-10 pr-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
            />
          </label>

          <label>
            <span className="sr-only">Filter by status</span>
            <select
              value={status}
              onChange={(event) => setFilter('status', event.target.value)}
              className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
            >
              <option value="">All statuses</option>
              {leadStatuses.map((option) => (
                <option key={option} value={option}>{statusLabels[option]}</option>
              ))}
            </select>
          </label>

          <label>
            <span className="sr-only">Filter by source</span>
            <select
              value={source}
              onChange={(event) => setFilter('source', event.target.value)}
              className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
            >
              <option value="">All sources</option>
              {leadSources.map((option) => (
                <option key={option} value={option}>{sourceLabels[option]}</option>
              ))}
            </select>
          </label>
        </div>

        {leadsQuery.isPending ? (
          <LeadListSkeleton />
        ) : leadsQuery.isError ? (
          <div className="px-5 py-16 text-center">
            <CircleAlert className="mx-auto size-9 text-red-500" aria-hidden="true" />
            <h3 className="mt-4 font-semibold text-slate-900">Leads could not be loaded</h3>
            <p className="mt-1 text-sm text-slate-600">Check your connection and try again.</p>
            <button
              type="button"
              onClick={() => void leadsQuery.refetch()}
              className="mt-5 inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              <RotateCcw className="size-4" aria-hidden="true" /> Retry
            </button>
          </div>
        ) : data && data.items.length === 0 ? (
          <div className="px-5 py-16 text-center">
            <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-blue-50 text-blue-600">
              <UserRoundSearch className="size-6" aria-hidden="true" />
            </span>
            <h3 className="mt-4 text-lg font-semibold text-slate-900">
              {hasFilters ? 'No leads match these filters' : 'Add your first lead'}
            </h3>
            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-600">
              {hasFilters
                ? 'Try a different search or clear the filters to see your full pipeline.'
                : 'Create a lead to start tracking contacts, opportunities, and sales progress.'}
            </p>
            {hasFilters ? (
              <button
                type="button"
                onClick={clearFilters}
                className="mt-5 inline-flex min-h-11 items-center rounded-xl border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              >
                Clear filters
              </button>
            ) : (
              <Link to="/leads/new" className="mt-5 inline-flex min-h-11 items-center rounded-xl bg-blue-600 px-4 text-sm font-semibold text-white">
                Add Lead
              </Link>
            )}
          </div>
        ) : data ? (
          <>
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full border-collapse text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-5 py-3.5 font-semibold">Contact</th>
                    <th className="px-5 py-3.5 font-semibold">Status</th>
                    <th className="px-5 py-3.5 font-semibold">Source</th>
                    <th className="px-5 py-3.5 text-right font-semibold">Value</th>
                    <th className="px-5 py-3.5 font-semibold">Added</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.items.map((lead) => (
                    <LeadTableRow key={lead.id} lead={lead} currency={user?.currency_code} timezone={user?.timezone} />
                  ))}
                </tbody>
              </table>
            </div>

            <div className="divide-y divide-slate-100 md:hidden">
              {data.items.map((lead) => (
                <LeadCard key={lead.id} lead={lead} currency={user?.currency_code} />
              ))}
            </div>

            <div className="flex flex-col gap-3 border-t border-slate-200 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-slate-600">
                {data.total === 0 ? 'No leads' : `Page ${data.page} of ${Math.max(data.pages, 1)} · ${data.total} total`}
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setPage(page - 1)}
                  disabled={page <= 1}
                  className="inline-flex min-h-10 items-center gap-1.5 rounded-lg border border-slate-300 px-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <ArrowLeft className="size-4" aria-hidden="true" /> Previous
                </button>
                <button
                  type="button"
                  onClick={() => setPage(page + 1)}
                  disabled={page >= data.pages}
                  className="inline-flex min-h-10 items-center gap-1.5 rounded-lg border border-slate-300 px-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Next <ArrowRight className="size-4" aria-hidden="true" />
                </button>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </section>
  )
}

function LeadTableRow({ lead, currency, timezone }: { lead: Lead; currency?: string; timezone?: string }) {
  return (
    <tr className="transition hover:bg-slate-50/80">
      <td className="px-5 py-4">
        <Link to={`/leads/${lead.id}`} className="font-semibold text-slate-900 hover:text-blue-600">{lead.contact_name}</Link>
        <p className="mt-0.5 text-xs text-slate-500">{lead.company || lead.email || 'No company added'}</p>
      </td>
      <td className="px-5 py-4"><StatusBadge status={lead.status} /></td>
      <td className="px-5 py-4 text-slate-600">{lead.source ? sourceLabels[lead.source] : '—'}</td>
      <td className="px-5 py-4 text-right font-medium text-slate-800">{formatMoney(lead.estimated_value, currency)}</td>
      <td className="px-5 py-4 text-slate-600">{formatDate(lead.created_at, timezone)}</td>
    </tr>
  )
}

function LeadCard({ lead, currency }: { lead: Lead; currency?: string }) {
  return (
    <Link to={`/leads/${lead.id}`} className="block p-5 transition hover:bg-slate-50">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate font-semibold text-slate-900">{lead.contact_name}</h3>
          <p className="mt-1 truncate text-sm text-slate-500">{lead.company || lead.email || 'No company added'}</p>
        </div>
        <StatusBadge status={lead.status} />
      </div>
      <div className="mt-4 flex items-center justify-between text-sm">
        <span className="text-slate-500">{lead.source ? sourceLabels[lead.source] : 'No source'}</span>
        <span className="font-semibold text-slate-800">{formatMoney(lead.estimated_value, currency)}</span>
      </div>
    </Link>
  )
}

function LeadListSkeleton() {
  return (
    <div className="animate-pulse p-5" aria-label="Loading leads">
      {[0, 1, 2, 3, 4].map((item) => (
        <div key={item} className="flex items-center gap-5 border-b border-slate-100 py-5 last:border-0">
          <div className="h-4 w-1/4 rounded bg-slate-200" />
          <div className="h-6 w-20 rounded-full bg-slate-100" />
          <div className="h-4 flex-1 rounded bg-slate-100" />
          <div className="h-4 w-24 rounded bg-slate-200" />
        </div>
      ))}
    </div>
  )
}
