import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from './authStore'

export function ProtectedRoute() {
  const { status } = useAuth()
  const location = useLocation()

  if (status === 'loading') {
    return (
      <main className="grid min-h-screen place-items-center bg-slate-100" aria-busy="true">
        <div className="text-center">
          <div className="mx-auto size-10 animate-spin rounded-full border-4 border-blue-100 border-t-blue-600" />
          <p className="mt-4 text-sm font-medium text-slate-600">Restoring your session…</p>
        </div>
      </main>
    )
  }

  if (status === 'anonymous') {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
