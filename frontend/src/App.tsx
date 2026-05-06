import type { ReactNode } from 'react'
import { useEffect, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { LoginPage } from './pages/LoginPage'
import { CustomerPortal } from './pages/customer/CustomerPortal'
import { AdminPortal } from './pages/admin/AdminPortal'
import { AiControlPortal } from './pages/ai/AiControlPortal'
import { readSession } from './lib/session'
import type { Role } from './types/api'
import './styles.css'

function ProtectedRoute({ allow, children }: { allow: Role[]; children: ReactNode }) {
  const session = readSession()
  if (!session || !allow.includes(session.role)) {
    return <Navigate to="/" replace />
  }
  return children
}

export default function App() {
  const [boot, setBoot] = useState(false)

  useEffect(() => {
    setBoot(true)
  }, [])

  if (!boot) return null

  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />
      <Route
        path="/customer"
        element={
          <ProtectedRoute allow={['customer']}>
            <CustomerPortal />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <ProtectedRoute allow={['admin']}>
            <AdminPortal />
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai-control"
        element={
          <ProtectedRoute allow={['ai-engineer']}>
            <AiControlPortal />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
