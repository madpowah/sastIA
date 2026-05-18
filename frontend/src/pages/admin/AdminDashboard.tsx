import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  Users,
  FileText,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Shield,
} from 'lucide-react'
import { DashboardLayout } from '../../components/Layout'
import { getAdminDashboard, type AdminDashboard, type AdminAudit, type AdminUser } from '../../api/admin'

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
    pending: 'bg-yellow-100 text-yellow-700',
    analyzing_code: 'bg-blue-100 text-blue-700',
    analyzing_docker: 'bg-purple-100 text-purple-700',
  }
  const labels: Record<string, string> = {
    completed: 'Terminé',
    failed: 'Échoué',
    pending: 'En attente',
    analyzing_code: 'Analyse code...',
    analyzing_docker: 'Analyse Docker...',
  }
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-700'}`}>
      {labels[status] || status}
    </span>
  )
}

export default function AdminDashboardPage() {
  const [data, setData] = useState<AdminDashboard | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAdminDashboard()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    )
  }

  if (!data) {
    return <div className="text-red-600">Erreur de chargement du tableau de bord.</div>
  }

  const statusColors: Record<string, string> = {
    completed: 'text-green-600',
    failed: 'text-red-600',
    pending: 'text-yellow-600',
    analyzing_code: 'text-blue-600',
    analyzing_docker: 'text-purple-600',
  }

  return (
    <DashboardLayout>
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Administration</h1>
        <p className="mt-1 text-sm text-gray-500">Tableau de bord global de la plateforme</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Utilisateurs</p>
              <p className="text-2xl font-bold text-gray-900">{data.total_users}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-indigo-100 rounded-lg">
              <FileText className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Audits</p>
              <p className="text-2xl font-bold text-gray-900">{data.total_audits}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Terminés</p>
              <p className="text-2xl font-bold text-gray-900">{data.audits_by_status.completed || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-red-100 rounded-lg">
              <XCircle className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Échecs</p>
              <p className="text-2xl font-bold text-gray-900">{data.audits_by_status.failed || 0}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">Répartition par statut</h2>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {Object.entries(data.audits_by_status).length === 0 ? (
                <p className="text-gray-500 text-sm">Aucun audit</p>
              ) : (
                Object.entries(data.audits_by_status).map(([status, count]) => (
                  <div key={status} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className={`w-4 h-4 ${statusColors[status] || 'text-gray-400'}`} />
                      <span className="text-sm text-gray-700">{status}</span>
                    </div>
                    <span className="text-sm font-medium">{count}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">Audits (7 derniers jours)</h2>
          </div>
          <div className="p-6">
            <div className="space-y-2">
              {data.audits_by_day.length === 0 ? (
                <p className="text-gray-500 text-sm">Aucun audit cette semaine</p>
              ) : (
                data.audits_by_day.map((d) => (
                  <div key={d.day} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{d.day}</span>
                    <span className="text-sm font-medium">{d.count}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Derniers utilisateurs</h2>
            <Link to="/admin/users" className="text-sm text-primary-600 hover:text-primary-700">
              Voir tout
            </Link>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {data.recent_users.map((u: AdminUser) => (
                <Link
                  key={u.id}
                  to={`/admin/users/${u.id}`}
                  className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                      <Users className="w-4 h-4 text-gray-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{u.full_name}</p>
                      <p className="text-xs text-gray-500">{u.email}</p>
                    </div>
                  </div>
                  <span className="text-xs text-gray-400">{u.audit_count} audits</span>
                </Link>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Derniers audits</h2>
            <Link to="/admin/audits" className="text-sm text-primary-600 hover:text-primary-700">
              Voir tout
            </Link>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {data.recent_audits.map((a: AdminAudit) => (
                <Link
                  key={a.id}
                  to={`/admin/audits/${a.id}`}
                  className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                      <Shield className="w-4 h-4 text-gray-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{a.name}</p>
                      <p className="text-xs text-gray-500">{a.user_email}</p>
                    </div>
                  </div>
                  <StatusBadge status={a.status} />
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
    </DashboardLayout>
  )
}
