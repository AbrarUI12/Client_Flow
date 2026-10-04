import { createBrowserRouter, Navigate } from 'react-router-dom'

import { ConnectionPage } from '../features/health/ConnectionPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <ConnectionPage />,
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
])

