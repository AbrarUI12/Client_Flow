import {
  CheckSquare2,
  FileText,
  LayoutDashboard,
  LogOut,
  Menu,
  Users,
  X,
} from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '../../features/auth/authStore'
import { useDocumentTitle } from '../../lib/useDocumentTitle'

const navigation = [
  { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'Leads', to: '/leads', icon: Users },
  { label: 'Quotations', to: '/quotations', icon: FileText },
  { label: 'Follow-ups', to: '/follow-ups', icon: CheckSquare2 },
]

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { user, logout } = useAuth()
  const [loggingOut, setLoggingOut] = useState(false)

  async function handleLogout() {
    if (loggingOut) return
    setLoggingOut(true)
    await logout()
  }

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
            onClick={() => void handleLogout()}
            disabled={loggingOut}
            className="grid size-9 shrink-0 place-items-center rounded-lg text-slate-400 transition hover:bg-white/10 hover:text-white"
            aria-label={loggingOut ? 'Logging out' : 'Log out'}
            title={loggingOut ? 'Logging out' : 'Log out'}
          >
            <LogOut className="size-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  )
}

function pageName(pathname: string): string {
  if (pathname === '/dashboard') return 'Dashboard'
  if (pathname === '/leads') return 'Leads'
  if (pathname === '/leads/new') return 'Add lead'
  if (/^\/leads\/[^/]+\/edit$/.test(pathname)) return 'Edit lead'
  if (/^\/leads\/[^/]+\/quotes\/new$/.test(pathname)) return 'Build quotation'
  if (/^\/leads\/[^/]+$/.test(pathname)) return 'Lead details'
  if (pathname === '/quotations') return 'Quotations'
  if (/^\/quotations\/[^/]+\/edit$/.test(pathname)) return 'Edit quotation'
  if (/^\/quotations\/[^/]+$/.test(pathname)) return 'Quotation details'
  if (pathname === '/follow-ups') return 'Follow-ups'
  return 'Page not found'
}

function MobileNavigation({ open, onClose }: { open: boolean; onClose: () => void }) {
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
      id="mobile-navigation"
      aria-label="Main navigation"
      onCancel={(event) => {
        event.preventDefault()
        onClose()
      }}
      onClose={onClose}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
      className="fixed inset-y-0 left-0 m-0 h-dvh max-h-none w-[min(19rem,88vw)] max-w-none overflow-visible bg-transparent p-0 shadow-2xl lg:hidden"
    >
      <button
        type="button"
        autoFocus
        onClick={onClose}
        className="absolute right-4 top-5 z-10 grid size-10 place-items-center rounded-xl text-slate-300 hover:bg-white/10 hover:text-white"
        aria-label="Close menu"
      >
        <X className="size-5" aria-hidden="true" />
      </button>
      <SidebarContent onNavigate={onClose} />
    </dialog>
  )
}

export function AppShell() {
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const { user } = useAuth()
  const currentPage = pageName(location.pathname)
  useDocumentTitle(currentPage)

  return (
    <div className="min-h-screen bg-[#f3f6fa] text-slate-900">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 lg:block">
        <SidebarContent />
      </aside>

      <MobileNavigation open={menuOpen} onClose={() => setMenuOpen(false)} />

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-slate-200/80 bg-white/90 px-5 backdrop-blur sm:px-8">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMenuOpen(true)}
              className="grid size-11 place-items-center rounded-xl border border-slate-200 text-slate-700 lg:hidden"
              aria-label="Open menu"
              aria-expanded={menuOpen}
              aria-controls="mobile-navigation"
            >
              <Menu className="size-5" aria-hidden="true" />
            </button>
            <div>
              <p className="text-xs font-medium text-slate-500">ClientFlow</p>
              <h1 className="text-lg font-semibold tracking-tight">{currentPage}</h1>
            </div>
          </div>

          <div className="flex min-w-0 items-center gap-3" aria-label="Current workspace">
            <div className="hidden min-w-0 text-right sm:block">
              <p className="truncate text-sm font-semibold text-slate-800">{user?.business_name}</p>
              <p className="truncate text-xs text-slate-500">{user?.full_name}</p>
            </div>
            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-blue-50 text-sm font-bold text-blue-700 ring-1 ring-blue-100">
              {user?.full_name
                .split(' ')
                .map((part) => part[0])
                .slice(0, 2)
                .join('')}
            </span>
          </div>
        </header>

        <main className="p-5 sm:p-8 lg:p-10">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
