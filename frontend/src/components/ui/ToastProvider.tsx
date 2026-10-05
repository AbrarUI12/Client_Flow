import { CheckCircle2, CircleAlert, Info, X } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'

import { ToastContext } from './toast'
import type { ToastInput, ToastTone } from './toast'

type Toast = ToastInput & {
  id: number
}

const toneClasses: Record<ToastTone, string> = {
  success: 'border-emerald-200 bg-white text-emerald-700',
  error: 'border-red-200 bg-white text-red-700',
  info: 'border-blue-200 bg-white text-blue-700',
}

const icons = {
  success: CheckCircle2,
  error: CircleAlert,
  info: Info,
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const nextId = useRef(1)
  const timers = useRef(new Map<number, number>())

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
    const timer = timers.current.get(id)
    if (timer) window.clearTimeout(timer)
    timers.current.delete(id)
  }, [])

  const notify = useCallback(
    (input: ToastInput) => {
      const id = nextId.current++
      setToasts((current) => [...current.slice(-2), { ...input, id }])
      timers.current.set(id, window.setTimeout(() => dismiss(id), 5000))
    },
    [dismiss],
  )

  useEffect(
    () => () => {
      timers.current.forEach((timer) => window.clearTimeout(timer))
      timers.current.clear()
    },
    [],
  )

  return (
    <ToastContext.Provider value={{ notify }}>
      {children}
      <div
        className="pointer-events-none fixed inset-x-4 top-4 z-[80] flex flex-col items-end gap-3 sm:left-auto sm:w-[24rem]"
        aria-live="polite"
        aria-atomic="false"
      >
        {toasts.map((toast) => {
          const tone = toast.tone || 'info'
          const Icon = icons[tone]
          return (
            <div
              key={toast.id}
              role={tone === 'error' ? 'alert' : 'status'}
              className={`pointer-events-auto flex w-full items-start gap-3 rounded-2xl border p-4 shadow-xl shadow-slate-900/10 ${toneClasses[tone]}`}
            >
              <Icon className="mt-0.5 size-5 shrink-0" aria-hidden="true" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-slate-950">{toast.title}</p>
                {toast.description && (
                  <p className="mt-1 text-sm leading-5 text-slate-600">{toast.description}</p>
                )}
              </div>
              <button
                type="button"
                onClick={() => dismiss(toast.id)}
                className="grid size-8 shrink-0 place-items-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                aria-label="Dismiss notification"
              >
                <X className="size-4" aria-hidden="true" />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}
