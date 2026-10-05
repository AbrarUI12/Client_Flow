import { ArrowLeft, SearchX } from 'lucide-react'
import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <section className="grid min-h-[65vh] place-items-center rounded-3xl border border-slate-200 bg-white p-6 text-center shadow-sm sm:p-10">
      <div className="max-w-md">
        <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-blue-50 text-blue-700">
          <SearchX className="size-6" aria-hidden="true" />
        </span>
        <p className="mt-5 text-sm font-bold uppercase tracking-[0.18em] text-blue-700">404</p>
        <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">Page not found</h2>
        <p className="mt-3 leading-7 text-slate-600">
          This address does not match a ClientFlow page. Return to the dashboard or use the main
          navigation to continue.
        </p>
        <Link
          to="/dashboard"
          className="mt-6 inline-flex min-h-11 items-center gap-2 rounded-xl bg-blue-600 px-5 text-sm font-semibold text-white hover:bg-blue-700"
        >
          <ArrowLeft className="size-4" aria-hidden="true" />
          Return to dashboard
        </Link>
      </div>
    </section>
  )
}
