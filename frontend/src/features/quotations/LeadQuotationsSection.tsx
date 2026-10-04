import { useQuery } from '@tanstack/react-query'
import { FilePlus2, LoaderCircle } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/authStore'
import { formatMoney } from '../leads/formatting'
import { getLeadQuotations } from './api'
import { formatPlainDate } from './formatting'
import { quotationKeys } from './queryKeys'
import { QuotationStatusBadge } from './QuotationStatusBadge'

export function LeadQuotationsSection({ leadId }: { leadId: string }) {
  const { user } = useAuth()
  const query = useQuery({
    queryKey: quotationKeys.leadList(leadId),
    queryFn: () => getLeadQuotations(leadId),
  })

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <div><h3 className="font-semibold text-slate-900">Quotations</h3><p className="mt-1 text-sm text-slate-600">Proposals connected to this lead.</p></div>
        <Link to={`/leads/${leadId}/quotes/new`} className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-blue-200 px-3 text-sm font-semibold text-blue-600"><FilePlus2 className="size-4" /> Create</Link>
      </div>
      {query.isPending ? <LoaderCircle aria-label="Loading quotations" className="mx-auto my-8 size-6 animate-spin text-blue-600" /> : query.isError ? <p className="mt-5 rounded-xl bg-red-50 p-3 text-sm text-red-700">Quotation summaries could not be loaded.</p> : query.data.items.length === 0 ? <p className="mt-5 rounded-xl bg-slate-50 p-4 text-sm text-slate-600">No quotations yet. Create a draft when this lead is ready for a proposal.</p> : <div className="mt-5 divide-y divide-slate-100">{query.data.items.map((quotation) => <Link key={quotation.id} to={`/quotations/${quotation.id}`} className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"><div><p className="text-sm font-semibold text-blue-600">{quotation.quote_number}</p><p className="mt-1 text-xs text-slate-500">{formatPlainDate(quotation.issue_date)} · {formatMoney(quotation.total, user?.currency_code)}</p></div><QuotationStatusBadge status={quotation.status} /></Link>)}</div>}
    </div>
  )
}
