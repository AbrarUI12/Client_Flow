import { quotationStatusLabels } from './formatting'
import type { QuotationStatus } from './types'

const styles: Record<QuotationStatus, string> = {
  DRAFT: 'bg-slate-100 text-slate-700 ring-slate-500/15',
  SENT: 'bg-blue-50 text-blue-700 ring-blue-600/15',
  ACCEPTED: 'bg-emerald-50 text-emerald-700 ring-emerald-600/15',
  REJECTED: 'bg-red-50 text-red-700 ring-red-600/15',
}

export function QuotationStatusBadge({ status }: { status: QuotationStatus }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${styles[status]}`}>
      {quotationStatusLabels[status]}
    </span>
  )
}
