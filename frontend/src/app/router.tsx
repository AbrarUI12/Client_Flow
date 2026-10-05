import { createBrowserRouter, Navigate } from 'react-router-dom'

import { AppShell } from '../components/layout/AppShell'
import { LoginPage } from '../features/auth/LoginPage'
import { ProtectedRoute } from '../features/auth/ProtectedRoute'
import { DashboardPage } from '../features/dashboard/DashboardPage'
import { FollowUpsPage } from '../features/followups/FollowUpsPage'
import { ConnectionPage } from '../features/health/ConnectionPage'
import { LeadDetailPage } from '../features/leads/LeadDetailPage'
import { LeadFormPage } from '../features/leads/LeadFormPage'
import { LeadsPage } from '../features/leads/LeadsPage'
import { QuotationBuilderPage } from '../features/quotations/QuotationBuilderPage'
import { QuotationDetailPage } from '../features/quotations/QuotationDetailPage'
import { QuotationsPage } from '../features/quotations/QuotationsPage'

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
          { path: '/dashboard', element: <DashboardPage /> },
          { path: '/leads', element: <LeadsPage /> },
          { path: '/leads/new', element: <LeadFormPage mode="create" /> },
          { path: '/leads/:id/edit', element: <LeadFormPage mode="edit" /> },
          { path: '/leads/:id', element: <LeadDetailPage /> },
          { path: '/quotations', element: <QuotationsPage /> },
          { path: '/quotations/:id/edit', element: <QuotationBuilderPage mode="edit" /> },
          { path: '/quotations/:id', element: <QuotationDetailPage /> },
          { path: '/leads/:leadId/quotes/new', element: <QuotationBuilderPage mode="create" /> },
          { path: '/follow-ups', element: <FollowUpsPage /> },
        ],
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
])
