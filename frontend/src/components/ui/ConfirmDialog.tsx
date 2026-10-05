import { LoaderCircle, TriangleAlert } from 'lucide-react'
import { useEffect, useRef } from 'react'

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  busyLabel,
  tone = 'danger',
  busy = false,
  error,
  onCancel,
  onConfirm,
}: {
  open: boolean
  title: string
  description: string
  confirmLabel: string
  busyLabel?: string
  tone?: 'danger' | 'primary'
  busy?: boolean
  error?: string
  onCancel: () => void
  onConfirm: () => void
}) {
  const dialogRef = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  return (
    <dialog
      ref={dialogRef}
      onCancel={(event) => {
        event.preventDefault()
        if (!busy) onCancel()
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget && !busy) onCancel()
      }}
      aria-labelledby="confirmation-title"
      aria-describedby="confirmation-description"
      className="m-auto w-[calc(100%_-_2rem)] max-w-md rounded-2xl bg-white p-0 text-slate-900 shadow-2xl backdrop:bg-slate-950/55 backdrop:backdrop-blur-sm"
    >
      <div className="p-6">
        <span className="grid size-11 place-items-center rounded-xl bg-amber-50 text-amber-700">
          <TriangleAlert className="size-5" aria-hidden="true" />
        </span>
        <h2 id="confirmation-title" className="mt-4 text-xl font-bold text-slate-950">
          {title}
        </h2>
        <p id="confirmation-description" className="mt-3 text-sm leading-6 text-slate-600">
          {description}
        </p>
        {error && (
          <p role="alert" className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        )}
        <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button
            type="button"
            autoFocus
            disabled={busy}
            onClick={onCancel}
            className="min-h-11 rounded-xl border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={onConfirm}
            className={`inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-4 text-sm font-semibold text-white disabled:cursor-wait disabled:opacity-60 ${tone === 'danger' ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'}`}
          >
            {busy && <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />}
            {busy ? (busyLabel || confirmLabel) : confirmLabel}
          </button>
        </div>
      </div>
    </dialog>
  )
}
