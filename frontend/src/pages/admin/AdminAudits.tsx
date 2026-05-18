import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  ChevronLeft,
  ChevronRight,
  Filter,
} from 'lucide-react'
import { DashboardLayout } from '../../components/Layout'
import {
  getAdminAudits,
  type AdminAudit,
  type PaginatedResult,
} from '../../api/admin'

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

function SeverityBlock({ label, count, color }: { label: string; count: number; color: string }) {
  if (count === 0) return null
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${color}`}>
      {label}: {count}
    </span>
  )
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return '-'
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h}h ${m}m`
}

export default function AdminAuditsPage() {
  const [data, setData] = useState<PaginatedResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')

  const fetch = (p: number, s: string) => {
    setLoading(true)
    getAdminAudits(p, 20, s)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetch(page, statusFilter)
  }, [page, statusFilter])

  const handleFilterChange = (newStatus: string) => {
    setStatusFilter(newStatus)
    setPage(1)
  }

  const totalPages = data ? Math.ceil(data.total / data.size) : 1

  return (
    <DashboardLayout>
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Tous les audits</h1>
        <p className="mt-1 text-sm text-gray-500">Audits de tous les utilisateurs</p>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <Filter className="w-4 h-4 text-gray-400" />
        {['', 'pending', 'analyzing_code', 'analyzing_docker', 'completed', 'failed'].map((s) => (
          <button
            key={s}
            onClick={() => handleFilterChange(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              statusFilter === s
                ? 'bg-primary-100 text-primary-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {s === '' ? 'Tous' : s === 'pending' ? 'En attente' : s === 'analyzing_code' ? 'Analyse code' : s === 'analyzing_docker' ? 'Docker' : s === 'completed' ? 'Terminés' : 'Échecs'}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Audit</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Utilisateur</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Statut</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vulnérabilités</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Début</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fin</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Durée</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                    <div className="flex justify-center">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600" />
                    </div>
                  </td>
                </tr>
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">Aucun audit trouvé</td>
                </tr>
              ) : (
                data?.items.map((a: AdminAudit) => (
                  <tr key={a.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link to={`/admin/audits/${a.id}`} className="text-sm font-medium text-primary-600 hover:text-primary-700">
                        {a.name}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{a.user_email}</td>
                    <td className="px-6 py-4 whitespace-nowrap"><StatusBadge status={a.status} /></td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex gap-1">
                        <SeverityBlock label="C" count={a.vulnerabilities_critical} color="bg-red-100 text-red-700" />
                        <SeverityBlock label="H" count={a.vulnerabilities_high} color="bg-orange-100 text-orange-700" />
                        <SeverityBlock label="M" count={a.vulnerabilities_medium} color="bg-yellow-100 text-yellow-700" />
                        <SeverityBlock label="L" count={a.vulnerabilities_low} color="bg-blue-100 text-blue-700" />
                        {a.total_vulnerabilities === 0 && <span className="text-xs text-gray-400">-</span>}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(a.created_at).toLocaleString('fr-FR')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {a.completed_at ? new Date(a.completed_at).toLocaleString('fr-FR') : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDuration(a.duration_seconds)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {data && data.total > data.size && (
          <div className="px-6 py-3 flex items-center justify-between border-t border-gray-200">
            <span className="text-sm text-gray-500">
              {data.total} résultat{(data.total > 1 ? 's' : '')} — page {data.page} sur {totalPages}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1 rounded hover:bg-gray-100 disabled:opacity-50"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="p-1 rounded hover:bg-gray-100 disabled:opacity-50"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}
      </div>
      </div>
    </DashboardLayout>
  )
}
