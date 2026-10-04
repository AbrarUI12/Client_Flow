import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowRight, Eye, EyeOff, LockKeyhole, ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { z } from 'zod'

import { ApiError } from '../../lib/apiClient'
import { useAuth } from './authStore'

const loginSchema = z.object({
  email: z.email('Enter a valid email address.'),
  password: z.string().min(1, 'Enter your password.'),
})

type LoginForm = z.infer<typeof loginSchema>

type LoginLocationState = {
  from?: string
}

export function LoginPage() {
  const { login, status } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [showPassword, setShowPassword] = useState(false)
  const [serverError, setServerError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: 'demo@clientflow.app', password: '' },
  })

  const destination = (location.state as LoginLocationState | null)?.from || '/dashboard'

  useEffect(() => {
    if (status === 'authenticated') {
      navigate(destination, { replace: true })
    }
  }, [destination, navigate, status])

  if (status === 'authenticated') {
    return <Navigate to={destination} replace />
  }

  const onSubmit = handleSubmit(async (values) => {
    setServerError(null)
    try {
      await login(values)
      navigate(destination, { replace: true })
    } catch (error) {
      setServerError(
        error instanceof ApiError ? error.message : 'Unable to sign in. Please try again.',
      )
    }
  })

  return (
    <main className="grid min-h-screen bg-[#f3f6fb] lg:grid-cols-[1.05fr_0.95fr]">
      <section className="relative hidden overflow-hidden bg-[#0b1f3a] p-14 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_15%_20%,rgba(59,130,246,0.28),transparent_32%),radial-gradient(circle_at_85%_80%,rgba(16,185,129,0.16),transparent_30%)]" />
        <div className="relative flex items-center gap-3">
          <span className="grid size-11 place-items-center rounded-xl bg-blue-500 text-lg font-bold shadow-lg shadow-blue-950/30">
            CF
          </span>
          <span className="text-xl font-semibold">ClientFlow</span>
        </div>

        <div className="relative max-w-lg">
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-blue-300">
            Lead to close
          </p>
          <h1 className="mt-5 text-5xl font-semibold leading-[1.08] tracking-[-0.04em]">
            Keep every client opportunity moving.
          </h1>
          <p className="mt-6 max-w-md text-lg leading-8 text-slate-300">
            Organize leads, prepare accurate quotations, and stay ahead of every follow-up in one focused workspace.
          </p>
        </div>

        <div className="relative flex items-center gap-3 text-sm text-slate-300">
          <ShieldCheck className="size-5 text-emerald-300" aria-hidden="true" />
          Secure, private business records
        </div>
      </section>

      <section className="flex items-center justify-center px-5 py-10 sm:px-10">
        <div className="w-full max-w-md">
          <div className="mb-10 flex items-center gap-3 lg:hidden">
            <span className="grid size-10 place-items-center rounded-xl bg-blue-600 font-bold text-white">
              CF
            </span>
            <span className="text-xl font-semibold text-slate-900">ClientFlow</span>
          </div>

          <p className="text-sm font-semibold text-blue-600">Welcome back</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-[-0.03em] text-slate-950">
            Sign in to your workspace
          </h2>
          <p className="mt-3 text-slate-600">Use the demo account to explore ClientFlow.</p>

          <form className="mt-8 space-y-5" onSubmit={onSubmit} noValidate>
            <div>
              <label className="text-sm font-medium text-slate-800" htmlFor="email">
                Email address
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                aria-invalid={Boolean(errors.email)}
                className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                {...register('email')}
              />
              {errors.email && <p className="mt-2 text-sm text-red-600">{errors.email.message}</p>}
            </div>

            <div>
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-slate-800" htmlFor="password">
                  Password
                </label>
                <span className="text-xs text-slate-500">Demo access</span>
              </div>
              <div className="relative mt-2">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  aria-invalid={Boolean(errors.password)}
                  className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pr-12 text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  {...register('password')}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((visible) => !visible)}
                  className="absolute inset-y-0 right-0 grid w-12 place-items-center text-slate-500 hover:text-slate-800"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-2 text-sm text-red-600">{errors.password.message}</p>
              )}
            </div>

            {serverError && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
                {serverError}
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting || status === 'loading'}
              className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 font-semibold text-white shadow-lg shadow-blue-600/20 transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? 'Signing in…' : 'Sign in'}
              {!isSubmitting && <ArrowRight className="size-4" aria-hidden="true" />}
            </button>
          </form>

          <div className="mt-6 rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
            <div className="flex items-start gap-3">
              <LockKeyhole className="mt-0.5 size-4 shrink-0 text-blue-600" aria-hidden="true" />
              <div>
                <p className="font-medium text-slate-800">Demo credentials</p>
                <button
                  type="button"
                  className="mt-1 text-left text-blue-700 hover:underline"
                  onClick={() => {
                    setValue('email', 'demo@clientflow.app')
                    setValue('password', 'development-only-change-me')
                  }}
                >
                  Fill demo email and password
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}
