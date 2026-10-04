import { ArrowRight, Database, RefreshCw, Server, Wifi, WifiOff } from 'lucide-react'

import { apiUrl } from '../../lib/apiClient'
import { useHealthQuery } from './api'

export function ConnectionPage() {
  const healthQuery = useHealthQuery()
  const isConnected = healthQuery.isSuccess

  return (
    <main className="relative flex min-h-screen overflow-hidden bg-[#f4f7fb] px-5 py-8 sm:px-8 lg:px-12">
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        <div className="absolute -left-24 -top-28 h-96 w-96 rounded-full bg-blue-300/20 blur-3xl" />
        <div className="absolute -bottom-40 -right-24 h-[30rem] w-[30rem] rounded-full bg-cyan-200/30 blur-3xl" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(15,39,71,0.035)_1px,transparent_1px),linear-gradient(90deg,rgba(15,39,71,0.035)_1px,transparent_1px)] bg-[size:48px_48px]" />
      </div>

      <section className="relative mx-auto grid w-full max-w-6xl overflow-hidden rounded-[2rem] border border-white/80 bg-white shadow-[0_32px_90px_-36px_rgba(15,39,71,0.45)] lg:grid-cols-[1.05fr_0.95fr]">
        <div className="flex min-h-[34rem] flex-col justify-between bg-[#0b1f3a] p-8 text-white sm:p-12 lg:min-h-[42rem] lg:p-14">
          <div>
            <div className="flex items-center gap-3" aria-label="ClientFlow">
              <span className="grid size-11 place-items-center rounded-xl bg-blue-500 shadow-lg shadow-blue-950/30">
                <span className="text-lg font-bold">CF</span>
              </span>
              <span className="text-xl font-semibold tracking-tight">ClientFlow</span>
            </div>

            <div className="mt-20 max-w-md lg:mt-28">
              <p className="text-xs font-bold uppercase tracking-[0.24em] text-blue-300">
                Workspace foundation
              </p>
              <h1 className="mt-5 text-4xl font-semibold leading-[1.08] tracking-[-0.035em] sm:text-5xl">
                The client journey starts here.
              </h1>
              <p className="mt-6 max-w-sm text-base leading-7 text-slate-300">
                A focused workspace for leads, quotations, and the follow-ups that move work forward.
              </p>
            </div>
          </div>

          <div className="mt-16 grid grid-cols-2 gap-3 text-sm text-slate-300">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <Server className="mb-3 size-5 text-blue-300" aria-hidden="true" />
              FastAPI service
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <Database className="mb-3 size-5 text-emerald-300" aria-hidden="true" />
              PostgreSQL config
            </div>
          </div>
        </div>

        <div className="flex items-center p-8 sm:p-12 lg:p-14">
          <div className="w-full">
            <p className="text-sm font-semibold text-blue-600">Development status</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-[-0.03em] text-slate-900">
              Frontend to API connection
            </h2>
            <p className="mt-3 leading-7 text-slate-600">
              This check confirms that the React application can reach the versioned ClientFlow API.
            </p>

            <div
              className={`mt-9 rounded-2xl border p-5 ${
                healthQuery.isPending
                  ? 'border-slate-200 bg-slate-50'
                  : isConnected
                    ? 'border-emerald-200 bg-emerald-50/70'
                    : 'border-red-200 bg-red-50/70'
              }`}
              role="status"
              aria-live="polite"
            >
              <div className="flex items-start gap-4">
                <span
                  className={`grid size-11 shrink-0 place-items-center rounded-xl ${
                    healthQuery.isPending
                      ? 'bg-slate-200 text-slate-600'
                      : isConnected
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'bg-red-100 text-red-700'
                  }`}
                >
                  {healthQuery.isPending ? (
                    <RefreshCw className="size-5 animate-spin" aria-hidden="true" />
                  ) : isConnected ? (
                    <Wifi className="size-5" aria-hidden="true" />
                  ) : (
                    <WifiOff className="size-5" aria-hidden="true" />
                  )}
                </span>

                <div className="min-w-0">
                  <p className="font-semibold text-slate-900">
                    {healthQuery.isPending
                      ? 'Checking API availability…'
                      : isConnected
                        ? 'Connected and ready'
                        : 'API unavailable'}
                  </p>
                  <p className="mt-1 break-all text-sm leading-6 text-slate-600">
                    {isConnected
                      ? `${healthQuery.data.service} · v${healthQuery.data.version}`
                      : healthQuery.isError
                        ? `Could not reach ${apiUrl}`
                        : apiUrl}
                  </p>
                </div>
              </div>
            </div>

            <dl className="mt-8 space-y-4 border-y border-slate-200 py-6 text-sm">
              <div className="flex items-center justify-between gap-4">
                <dt className="text-slate-500">Web application</dt>
                <dd className="font-medium text-slate-800">React + TypeScript</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="text-slate-500">API endpoint</dt>
                <dd className="max-w-[65%] truncate font-mono text-xs text-slate-700">{apiUrl}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="text-slate-500">Environment</dt>
                <dd className="font-medium text-slate-800">Development</dd>
              </div>
            </dl>

            {healthQuery.isError ? (
              <button
                type="button"
                onClick={() => void healthQuery.refetch()}
                className="mt-8 inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
              >
                Try connection again
                <RefreshCw className="size-4" aria-hidden="true" />
              </button>
            ) : (
              <div className="mt-8 flex items-center gap-2 text-sm font-medium text-slate-500">
                Session 1 foundation
                <ArrowRight className="size-4" aria-hidden="true" />
                Authentication next
              </div>
            )}
          </div>
        </div>
      </section>
    </main>
  )
}
