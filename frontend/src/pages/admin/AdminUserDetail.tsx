import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Users, Mail, Building2, Calendar, Shield, ShieldOff } from 'lucide-react'
import {
  getAdminUser,
  patchAdminUser,
  type AdminUser,
  type AdminAudit,
} from '../../api/admin'
import { DashboardLayout } from '../../components/Layout'

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

export default function AdminUserDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [user, setUser] = useState<AdminUser | null>(null)
  const [audits, setAudits] = useState<AdminAudit[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    getAdminUser(id)
      .then((data) => {
        setUser(data.user)
        setAudits(data.audits)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [id])

  const toggleActive = async () => {
    if (!user) return
    const updated = await patchAdminUser(user.id, { is_active: user.is_active ? 0 : 1 })
    setUser(updated)
  }

  const toggleAdmin = async () => {
    if (!user) return
    const updated = await patchAdminUser(user.id, { is_admin: user.is_admin ? 0 : 1 })
    setUser(updated)
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      </DashboardLayout>
    )
  }

  if (!user) {
    return (
      <DashboardLayout>
        <div className="text-red-600">Utilisateur introuvable.</div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-5xl mx-auto">
        <div className="flex items-center gap-4">
          <Link to="/admin/users" className="p-2 rounded-lg hover:bg-gray-100">
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Détail utilisateur</h1>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center">
                <Users className="w-8 h-8 text-primary-600" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">{user.full_name}</h2>
                <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                  <span className="flex items-center gap-1"><Mail className="w-4 h-4" /> {user.email}</span>
                  {user.company && <span className="flex items-center gap-1"><Building2 className="w-4 h-4" /> {user.company}</span>}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={toggleActive}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
                  user.is_active
                    ? 'bg-red-100 text-red-700 hover:bg-red-200'
                    : 'bg-green-100 text-green-700 hover:bg-green-200'
                }`}
              >
                {user.is_active ? 'Désactiver' : 'Activer'}
              </button>
              <button
                onClick={toggleAdmin}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
                  user.is_admin
                    ? 'bg-orange-100 text-orange-700 hover:bg-orange-200'
                    : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                }`}
              >
                {user.is_admin ? 'Retirer admin' : 'Promouvoir admin'}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-100">
            <div>
              <p className="text-xs text-gray-500">Inscrit le</p>
              <p className="text-sm font-medium mt-1">{new Date(user.created_at).toLocaleDateString('fr-FR')}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Statut</p>
              <p className="text-sm font-medium mt-1">{user.is_active ? 'Actif' : 'Désactivé'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Rôle</p>
              <p className="text-sm font-medium mt-1">{user.is_admin ? 'Administrateur' : 'Utilisateur'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Audits</p>
              <p className="text-sm font-medium mt-1">{audits.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">Audits ({audits.length})</h2>
          </div>
          {audits.length === 0 ? (
            <div className="p-6 text-sm text-gray-500">Aucun audit</div>
          ) : (
            <div className="divide-y divide-gray-200">
              {audits.map((a) => (
                <Link
                  key={a.id}
                  to={`/admin/audits/${a.id}`}
                  className="flex items-center justify-between px-6 py-4 hover:bg-gray-50"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">{a.name}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(a.created_at).toLocaleDateString('fr-FR')}
                      {a.duration_seconds !== null ? ` — ${Math.floor(a.duration_seconds / 60)}min` : ''}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-500">
                      C:{a.vulnerabilities_critical} H:{a.vulnerabilities_high} M:{a.vulnerabilities_medium} L:{a.vulnerabilities_low}
                    </span>
                    <StatusBadge status={a.status} />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
