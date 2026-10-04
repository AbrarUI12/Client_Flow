import { ArrowUpRight, CalendarClock, FileText, Users } from 'lucide-react'

import { useAuth } from '../auth/authStore'

const cards = [
  { label: 'Total leads', value: '—', icon: Users, tone: 'bg-blue-50 text-blue-700' },
  { label: 'Open quotes', value: '—', icon: FileText, tone: 'bg-violet-50 text-violet-700' },
  { label: 'Follow-ups due', value: '—', icon: CalendarClock, tone: 'bg-amber-50 text-amber-700' },
]

export function DashboardPlaceholderPage() {
  const { user } = useAuth()

  return (
    <div className="mx-auto max-w-7xl">
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold text-blue-600">Authenticated workspace</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-[-0.03em] text-slate-950">
            Good to see you, {user?.full_name.split(' ')[0]}.
          </h2>
          <p className="mt-2 text-slate-600">Your sales overview will come together here.</p>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-sm font-medium text-emerald-800">
          Session secured
        </div>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        {cards.map(({ label, value, icon: Icon, tone }) => (
          <article key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className={`grid size-11 place-items-center rounded-xl ${tone}`}>
                <Icon className="size-5" aria-hidden="true" />
              </span>
              <ArrowUpRight className="size-4 text-slate-300" aria-hidden="true" />
            </div>
            <p className="mt-6 text-sm text-slate-500">{label}</p>
            <p className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">{value}</p>
          </article>
        ))}
      </div>

      <section className="mt-6 overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-6 py-5">
          <h3 className="font-semibold text-slate-900">Foundation complete</h3>
          <p className="mt-1 text-sm text-slate-500">
            Authentication and the protected application shell are ready for business features.
          </p>
        </div>
        <div className="grid gap-4 p-6 sm:grid-cols-3">
          {['JWT session active', 'User profile loaded', 'Protected routes enabled'].map((item) => (
            <div key={item} className="rounded-2xl bg-slate-50 p-4 text-sm font-medium text-slate-700">
              {item}
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
