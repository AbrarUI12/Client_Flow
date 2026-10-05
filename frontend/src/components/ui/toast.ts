import { createContext, useContext } from 'react'

export type ToastTone = 'success' | 'error' | 'info'

export type ToastInput = {
  title: string
  description?: string
  tone?: ToastTone
}

export type ToastContextValue = {
  notify: (toast: ToastInput) => void
}

export const ToastContext = createContext<ToastContextValue | null>(null)

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast must be used inside ToastProvider')
  return context
}
