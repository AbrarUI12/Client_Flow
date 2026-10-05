import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Check, CircleAlert, Download, LoaderCircle, Pencil, Send, X } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ApiError, saveDownloadedFile } from '../../lib/apiClient'
import { useAuth } from '../auth/authStore'
import { formatMoney } from '../leads/formatting'
import { leadKeys } from '../leads/queryKeys'
import { downloadQuotationPdf, getQuotation, transitionQuotation } from './api'
import { formatPlainDate } from './formatting'
import { quotationKeys } from './queryKeys'
import { QuotationStatusBadge } from './QuotationStatusBadge'
import type { QuotationStatus } from './types'

export function QuotationDetailPage() {
  const { id = '' } = useParams()
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [actionError, setActionError] = useState('')
  const quotationQuery = useQuery({
    queryKey: quotationKeys.detail(id),
    queryFn: () => getQuotation(id),
    enabled: Boolean(id),
    retry: (count, error) => !(error instanceof ApiError && error.status === 404) && count < 2,
  })
  const statusMutation = useMutation({
    mutationFn: (status: QuotationStatus) => transitionQuotation(id, status),
    onSuccess: async (quotation) => {
      setActionError('')
      queryClient.setQueryData(quotationKeys.detail(id), quotation)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: quotationKeys.lists() }),
        queryClient.invalidateQueries({ queryKey: leadKeys.all }),
      ])
    },
    onError: (error) => setActionError(error instanceof ApiError ? error.message : 'The status could not be updated.'),
  })
  const pdfMutation = useMutation({
    mutationFn: () => downloadQuotationPdf(id),
    onSuccess: (file) => {
      setActionError('')
      saveDownloadedFile(file)
    },
    onError: (error) => setActionError(error instanceof ApiError ? error.message : 'The PDF could not be downloaded.'),
  })

  if (quotationQuery.isPending) return <DetailState title="Loading quotation…" loading />
  if (quotationQuery.isError) return <DetailState title="Quotation not found" />
  const quotation = quotationQuery.data

  return (
    <section className="mx-auto max-w-6xl">
      <Link to="/quotations" className="mb-5 inline-flex min-h-11 items-center gap-2 text-sm font-semibold text-slate-600"><ArrowLeft className="size-4" /> Back to quotations</Link>
      <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-5 border-b border-slate-200 p-5 sm:p-7 lg:flex-row lg:items-start lg:justify-between">
          <div><div className="flex flex-wrap items-center gap-3"><h1 className="text-3xl font-bold tracking-tight">{quotation.quote_number}</h1><QuotationStatusBadge status={quotation.status} /></div><p className="mt-2 text-sm text-slate-600">Issued {formatPlainDate(quotation.issue_date)} · Valid until {formatPlainDate(quotation.valid_until)}</p></div>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => pdfMutation.mutate()} disabled={pdfMutation.isPending} className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-wait disabled:opacity-60">{pdfMutation.isPending ? <LoaderCircle className="size-4 animate-spin" /> : <Download className="size-4" />} {pdfMutation.isPending ? 'Preparing PDF…' : 'Download PDF'}</button>
            {quotation.status === 'DRAFT' && <Link to={`/quotations/${quotation.id}/edit`} className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-300 px-4 text-sm font-semibold"><Pencil className="size-4" /> Edit</Link>}
            <StatusActions status={quotation.status} pending={statusMutation.isPending} onAction={(status) => statusMutation.mutate(status)} />
          </div>
        </div>
        {actionError && <p role="alert" className="mx-5 mt-5 rounded-xl bg-red-50 p-3 text-sm text-red-700 sm:mx-7">{actionError}</p>}

        <div className="grid gap-8 p-5 sm:p-7 lg:grid-cols-2">
          <Identity title="From" name={user?.business_name || 'ClientFlow business'} lines={[user?.business_address, user?.business_phone, user?.email]} />
          <Identity title="Prepared for" name={quotation.lead.contact_name} lines={[quotation.lead.company, quotation.lead.email]} leadId={quotation.lead_id} />
        </div>

        <div className="overflow-x-auto border-y border-slate-200">
          <table className="w-full min-w-[42rem] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-5 py-3.5 sm:px-7">Description</th><th className="px-5 py-3.5 text-right">Quantity</th><th className="px-5 py-3.5 text-right">Unit price</th><th className="px-5 py-3.5 text-right sm:px-7">Line total</th></tr></thead>
            <tbody className="divide-y divide-slate-100">{quotation.items.map((item) => <tr key={item.id}><td className="px-5 py-4 font-medium sm:px-7">{item.description}</td><td className="px-5 py-4 text-right text-slate-600">{item.quantity}</td><td className="px-5 py-4 text-right text-slate-600">{formatMoney(item.unit_price, user?.currency_code)}</td><td className="px-5 py-4 text-right font-semibold sm:px-7">{formatMoney(item.line_total, user?.currency_code)}</td></tr>)}</tbody>
          </table>
        </div>

        <div className="grid gap-8 p-5 sm:p-7 lg:grid-cols-[1fr_22rem]">
          <div><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Notes</p><p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-slate-700">{quotation.notes || 'No notes were added.'}</p></div>
          <dl className="space-y-3 text-sm"><Amount label="Subtotal" value={quotation.subtotal} currency={user?.currency_code} /><Amount label={`Discount (${quotation.discount_percent}%)`} value={`-${quotation.discount_amount}`} currency={user?.currency_code} /><Amount label={`Tax (${quotation.tax_percent}%)`} value={quotation.tax_amount} currency={user?.currency_code} /><div className="border-t border-slate-200 pt-4"><Amount label="Total" value={quotation.total} currency={user?.currency_code} prominent /></div></dl>
        </div>
      </div>
    </section>
  )
}

function StatusActions({ status, pending, onAction }: { status: QuotationStatus; pending: boolean; onAction: (status: QuotationStatus) => void }) {
  if (status === 'DRAFT') return <button type="button" disabled={pending} onClick={() => onAction('SENT')} className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-blue-600 px-4 text-sm font-semibold text-white disabled:opacity-60">{pending ? <LoaderCircle className="size-4 animate-spin" /> : <Send className="size-4" />} Mark sent</button>
  if (status === 'SENT') return <><button type="button" disabled={pending} onClick={() => onAction('REJECTED')} className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-red-200 px-4 text-sm font-semibold text-red-700"><X className="size-4" /> Reject</button><button type="button" disabled={pending} onClick={() => onAction('ACCEPTED')} className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-emerald-600 px-4 text-sm font-semibold text-white"><Check className="size-4" /> Accept</button></>
  return null
}

function Identity({ title, name, lines, leadId }: { title: string; name: string; lines: Array<string | null | undefined>; leadId?: string }) {
  return <div><p className="text-xs font-bold uppercase tracking-wide text-slate-500">{title}</p><p className="mt-2 font-semibold text-slate-900">{leadId ? <Link to={`/leads/${leadId}`} className="text-blue-600 hover:underline">{name}</Link> : name}</p>{lines.filter(Boolean).map((line) => <p key={line} className="mt-1 text-sm text-slate-600">{line}</p>)}</div>
}

function Amount({ label, value, currency, prominent = false }: { label: string; value: string; currency?: string; prominent?: boolean }) {
  const negative = value.startsWith('-')
  return <div className={`flex justify-between gap-4 ${prominent ? 'text-lg font-bold' : 'text-slate-600'}`}><dt>{label}</dt><dd className="font-semibold text-slate-900">{negative ? '−' : ''}{formatMoney(negative ? value.slice(1) : value, currency)}</dd></div>
}

function DetailState({ title, loading = false }: { title: string; loading?: boolean }) {
  return <div className="grid min-h-[55vh] place-items-center rounded-2xl border border-slate-200 bg-white text-center"><div>{loading ? <LoaderCircle className="mx-auto size-8 animate-spin text-blue-600" /> : <CircleAlert className="mx-auto size-8 text-slate-400" />}<h2 className="mt-4 text-xl font-semibold">{title}</h2><Link to="/quotations" className="mt-4 inline-flex min-h-11 items-center text-sm font-semibold text-blue-600">Return to quotations</Link></div></div>
}
