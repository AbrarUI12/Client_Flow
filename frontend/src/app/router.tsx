import { createBrowserRouter, Navigate } from 'react-router-dom'

import { AppShell, FeaturePlaceholder } from '../components/layout/AppShell'
import { LoginPage } from '../features/auth/LoginPage'
import { ProtectedRoute } from '../features/auth/ProtectedRoute'
import { DashboardPlaceholderPage } from '../features/dashboard/DashboardPlaceholderPage'
import { ConnectionPage } from '../features/health/ConnectionPage'
import { LeadDetailPage } from '../features/leads/LeadDetailPage'
import { LeadFormPage } from '../features/leads/LeadFormPage'
import { LeadsPage } from '../features/leads/LeadsPage'

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
          { path: '/leads', element: <LeadsPage /> },
          { path: '/leads/new', element: <LeadFormPage mode="create" /> },
          { path: '/leads/:id/edit', element: <LeadFormPage mode="edit" /> },
          { path: '/leads/:id', element: <LeadDetailPage /> },
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
