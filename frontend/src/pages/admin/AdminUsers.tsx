import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  Search,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  XCircle,
  Shield,
} from 'lucide-react'
import { DashboardLayout } from '../../components/Layout'
import {
  getAdminUsers,
  patchAdminUser,
  type AdminUser,
  type PaginatedResult,
} from '../../api/admin'
import { useLanguage } from '../../i18n/LanguageContext'

export default function AdminUsersPage() {
  const { t } = useLanguage()
  const [data, setData] = useState<PaginatedResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [toggling, setToggling] = useState<string | null>(null)

  const fetch = (p: number, q: string) => {
    setLoading(true)
    getAdminUsers(p, 20, q)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetch(page, search)
  }, [page, search])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearch(searchInput)
    setPage(1)
  }

  const toggleActive = async (user: AdminUser) => {
    setToggling(user.id)
    try {
      await patchAdminUser(user.id, { is_active: user.is_active ? 0 : 1 })
      fetch(page, search)
    } finally {
      setToggling(null)
    }
  }

  const toggleAdmin = async (user: AdminUser) => {
    setToggling(user.id)
    try {
      await patchAdminUser(user.id, { is_admin: user.is_admin ? 0 : 1 })
      fetch(page, search)
    } finally {
      setToggling(null)
    }
  }

  const totalPages = data ? Math.ceil(data.total / data.size) : 1

  return (
    <DashboardLayout>
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('admin.users')}</h1>
          <p className="mt-1 text-sm text-gray-500">Gérer les comptes de la plateforme</p>
        </div>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher par email ou nom..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
        <button
          type="submit"
          className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
        >
          Rechercher
        </button>
      </form>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Utilisateur</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Société</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Audits</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Statut</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Admin</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Inscrit le</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                    <div className="flex justify-center">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600" />
                    </div>
                  </td>
                </tr>
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-gray-500">Aucun utilisateur trouvé</td>
                </tr>
              ) : (
                data?.items.map((u: AdminUser) => (
                  <tr key={u.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link to={`/admin/users/${u.id}`} className="text-sm font-medium text-primary-600 hover:text-primary-700">
                        {u.full_name}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{u.email}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{u.company || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{u.audit_count}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center gap-1 text-xs font-medium ${u.is_active ? 'text-green-700' : 'text-red-700'}`}>
                        {u.is_active ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                        {u.is_active ? 'Actif' : 'Désactivé'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {u.is_admin ? (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-purple-700">
                          <Shield className="w-3 h-3" /> Admin
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(u.created_at).toLocaleDateString(t('common.dateFormat'))}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => toggleActive(u)}
                          disabled={toggling === u.id}
                          className={`text-xs px-2 py-1 rounded ${u.is_active ? 'text-red-600 hover:bg-red-50' : 'text-green-600 hover:bg-green-50'}`}
                        >
                          {u.is_active ? 'Désactiver' : 'Activer'}
                        </button>
                        <button
                          onClick={() => toggleAdmin(u)}
                          disabled={toggling === u.id}
                          className={`text-xs px-2 py-1 rounded ${u.is_admin ? 'text-orange-600 hover:bg-orange-50' : 'text-purple-600 hover:bg-purple-50'}`}
                        >
                          {u.is_admin ? 'Retirer admin' : 'Promouvoir'}
                        </button>
                      </div>
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
