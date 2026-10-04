import {
  Bell,
  BriefcaseBusiness,
  CheckSquare2,
  FileText,
  LayoutDashboard,
  LogOut,
  Menu,
  Users,
  X,
} from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '../../features/auth/authStore'

const navigation = [
  { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'Leads', to: '/leads', icon: Users },
  { label: 'Quotations', to: '/quotations', icon: FileText },
  { label: 'Follow-ups', to: '/follow-ups', icon: CheckSquare2 },
]

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { user, logout } = useAuth()

  return (
    <div className="flex h-full flex-col bg-[#0b1f3a] text-white">
      <div className="flex h-20 items-center gap-3 px-6">
        <span className="grid size-10 place-items-center rounded-xl bg-blue-500 font-bold shadow-lg shadow-blue-950/30">
          CF
        </span>
        <div>
          <p className="font-semibold tracking-tight">ClientFlow</p>
          <p className="text-xs text-slate-400">Sales workspace</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-6" aria-label="Primary navigation">
        <p className="px-3 text-[0.68rem] font-bold uppercase tracking-[0.2em] text-slate-500">
          Workspace
        </p>
        <div className="mt-3 space-y-1">
          {navigation.map(({ label, to, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={onNavigate}
              className={({ isActive }) =>
                `flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm font-medium transition ${
                  isActive
                    ? 'bg-blue-500 text-white shadow-lg shadow-blue-950/20'
                    : 'text-slate-300 hover:bg-white/8 hover:text-white'
                }`
              }
            >
              <Icon className="size-5" aria-hidden="true" />
              {label}
            </NavLink>
          ))}
        </div>
      </nav>

      <div className="border-t border-white/10 p-4">
        <div className="flex items-center gap-3 rounded-xl bg-white/5 p-3">
          <span className="grid size-9 shrink-0 place-items-center rounded-full bg-blue-100 text-sm font-bold text-blue-800">
            {user?.full_name
              .split(' ')
              .map((part) => part[0])
              .slice(0, 2)
              .join('')}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{user?.full_name}</p>
            <p className="truncate text-xs text-slate-400">{user?.business_name}</p>
          </div>
          <button
            type="button"
            onClick={() => void logout()}
            className="grid size-9 shrink-0 place-items-center rounded-lg text-slate-400 transition hover:bg-white/10 hover:text-white"
            aria-label="Log out"
            title="Log out"
          >
            <LogOut className="size-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  )
}

export function AppShell() {
  const location = useLocation()
  const [menuOpenedAt, setMenuOpenedAt] = useState<string | null>(null)
  const menuOpen = menuOpenedAt === location.pathname

  const currentPage = navigation.find((item) => location.pathname.startsWith(item.to))

  return (
    <div className="min-h-screen bg-[#f3f6fa] text-slate-900">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 lg:block">
        <SidebarContent />
      </aside>

      {menuOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            aria-label="Close navigation"
            className="absolute inset-0 bg-slate-950/50 backdrop-blur-sm"
            onClick={() => setMenuOpenedAt(null)}
          />
          <aside className="relative h-full w-[min(19rem,88vw)] shadow-2xl">
            <button
              type="button"
              onClick={() => setMenuOpenedAt(null)}
              className="absolute right-4 top-5 z-10 grid size-10 place-items-center rounded-xl text-slate-300 hover:bg-white/10 hover:text-white"
              aria-label="Close menu"
            >
              <X className="size-5" />
            </button>
            <SidebarContent onNavigate={() => setMenuOpenedAt(null)} />
          </aside>
        </div>
      )}

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-slate-200/80 bg-white/90 px-5 backdrop-blur sm:px-8">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMenuOpenedAt(location.pathname)}
              className="grid size-11 place-items-center rounded-xl border border-slate-200 text-slate-700 lg:hidden"
              aria-label="Open menu"
            >
              <Menu className="size-5" />
            </button>
            <div>
              <p className="text-xs font-medium text-slate-500">ClientFlow</p>
              <h1 className="text-lg font-semibold tracking-tight">{currentPage?.label || 'Workspace'}</h1>
            </div>
          </div>

          <button
            type="button"
            className="relative grid size-11 place-items-center rounded-xl border border-slate-200 bg-white text-slate-600 shadow-sm transition hover:border-slate-300 hover:text-slate-900"
            aria-label="Notifications"
          >
            <Bell className="size-5" />
            <span className="absolute right-2.5 top-2.5 size-2 rounded-full bg-blue-500 ring-2 ring-white" />
          </button>
        </header>

        <main className="p-5 sm:p-8 lg:p-10">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export function FeaturePlaceholder({ title }: { title: string }) {
  return (
    <section className="grid min-h-[65vh] place-items-center rounded-3xl border border-dashed border-slate-300 bg-white p-8 text-center">
      <div className="max-w-md">
        <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-blue-50 text-blue-600">
          <BriefcaseBusiness className="size-6" />
        </span>
        <h2 className="mt-5 text-2xl font-semibold tracking-tight">{title}</h2>
        <p className="mt-3 leading-7 text-slate-600">
          The protected workspace is ready. This feature is scheduled for its dedicated build session.
        </p>
      </div>
    </section>
  )
}
