import { Routes, Route, Navigate } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AdminRoute } from './components/AdminRoute'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import NewAudit from './pages/NewAudit'
import AuditsList from './pages/AuditsList'
import AuditDetail from './pages/AuditDetail'
import Report from './pages/Report'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminUsers from './pages/admin/AdminUsers'
import AdminAudits from './pages/admin/AdminAudits'
import AdminAuditDetail from './pages/admin/AdminAuditDetail'
import AdminUserDetail from './pages/admin/AdminUserDetail'
import Settings from './pages/Settings'
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/audits"
        element={
          <ProtectedRoute>
            <AuditsList />
          </ProtectedRoute>
        }
      />
      <Route
        path="/audits/new"
        element={
          <ProtectedRoute>
            <NewAudit />
          </ProtectedRoute>
        }
      />
      <Route
        path="/audits/:id"
        element={
          <ProtectedRoute>
            <AuditDetail />
          </ProtectedRoute>
        }
      />
      <Route
        path="/audits/:id/report"
        element={
          <ProtectedRoute>
            <Report />
          </ProtectedRoute>
        }
      />

      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        }
      />

      {/* Admin routes */}
      <Route
        path="/admin"
        element={
          <AdminRoute>
            <AdminDashboard />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/users"
        element={
          <AdminRoute>
            <AdminUsers />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/users/:id"
        element={
          <AdminRoute>
            <AdminUserDetail />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/audits"
        element={
          <AdminRoute>
            <AdminAudits />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/audits/:id"
        element={
          <AdminRoute>
            <AdminAuditDetail />
          </AdminRoute>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
