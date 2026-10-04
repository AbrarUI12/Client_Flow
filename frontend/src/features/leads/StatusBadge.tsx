import { statusLabels } from './formatting'
import type { LeadStatus } from './types'

const statusStyles: Record<LeadStatus, string> = {
  NEW: 'bg-blue-50 text-blue-700 ring-blue-600/15',
  CONTACTED: 'bg-violet-50 text-violet-700 ring-violet-600/15',
  QUALIFIED: 'bg-amber-50 text-amber-800 ring-amber-600/20',
  QUOTED: 'bg-cyan-50 text-cyan-700 ring-cyan-600/15',
  WON: 'bg-emerald-50 text-emerald-700 ring-emerald-600/15',
  LOST: 'bg-slate-100 text-slate-600 ring-slate-500/15',
}

export function StatusBadge({ status }: { status: LeadStatus }) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${statusStyles[status]}`}
    >
      {statusLabels[status]}
    </span>
  )
}
