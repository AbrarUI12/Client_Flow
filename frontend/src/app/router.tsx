import { createBrowserRouter, Navigate } from 'react-router-dom'

import { AppShell, FeaturePlaceholder } from '../components/layout/AppShell'
import { LoginPage } from '../features/auth/LoginPage'
import { ProtectedRoute } from '../features/auth/ProtectedRoute'
import { DashboardPlaceholderPage } from '../features/dashboard/DashboardPlaceholderPage'
import { ConnectionPage } from '../features/health/ConnectionPage'

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/status',
    element: <ConnectionPage />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          { index: true, element: <Navigate to="/dashboard" replace /> },
          { path: '/dashboard', element: <DashboardPlaceholderPage /> },
          { path: '/leads', element: <FeaturePlaceholder title="Lead management" /> },
          { path: '/quotations', element: <FeaturePlaceholder title="Quotations" /> },
          { path: '/follow-ups', element: <FeaturePlaceholder title="Follow-ups" /> },
        ],
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
])
