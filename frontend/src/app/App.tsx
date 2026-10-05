import { RouterProvider } from 'react-router-dom'

import { ToastProvider } from '../components/ui/ToastProvider'
import { AuthProvider } from '../features/auth/AuthContext'
import { router } from './router'

function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </ToastProvider>
  )
}

export default App
