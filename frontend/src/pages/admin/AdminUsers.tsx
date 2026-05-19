import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  Search,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  XCircle,
  Shield,
  Plus,
  Trash2,
  Key,
} from 'lucide-react'
import { DashboardLayout } from '../../components/Layout'
import { Button } from '../../components/ui/Button'
import {
  getAdminUsers,
  patchAdminUser,
  createAdminUser,
  deleteAdminUser,
  resetAdminUserPassword,
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

  // Create user
  const [showCreate, setShowCreate] = useState(false)
  const [createForm, setCreateForm] = useState({ email: '', password: '', full_name: '', company: '', is_admin: false })
  const [createSaving, setCreateSaving] = useState(false)

  // Delete confirm
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [deleteSaving, setDeleteSaving] = useState(false)

  // Reset password
  const [resetFor, setResetFor] = useState<string | null>(null)
  const [resetPw, setResetPw] = useState('')
  const [resetSaving, setResetSaving] = useState(false)

  const fetch = (p: number, q: string) => {
    setLoading(true)
    getAdminUsers(p, 20, q)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetch(page, search) }, [page, search])

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
    } finally { setToggling(null) }
  }

  const toggleAdmin = async (user: AdminUser) => {
    setToggling(user.id)
    try {
      await patchAdminUser(user.id, { is_admin: user.is_admin ? 0 : 1 })
      fetch(page, search)
    } finally { setToggling(null) }
  }

  const handleCreate = async () => {
    if (!createForm.email || createForm.password.length < 8 || !createForm.full_name) return
    setCreateSaving(true)
    try {
      await createAdminUser(createForm)
      setShowCreate(false)
      setCreateForm({ email: '', password: '', full_name: '', company: '', is_admin: false })
      setPage(1)
      fetch(1, search)
    } catch { } finally { setCreateSaving(false) }
  }

  const handleDelete = async () => {
    if (!deleteId) return
    setDeleteSaving(true)
    try {
      await deleteAdminUser(deleteId)
      setDeleteId(null)
      fetch(page, search)
    } finally { setDeleteSaving(false) }
  }

  const handleResetPassword = async () => {
    if (!resetFor || resetPw.length < 8) return
    setResetSaving(true)
    try {
      await resetAdminUserPassword(resetFor, resetPw)
      setResetFor(null)
      setResetPw('')
    } finally { setResetSaving(false) }
  }

  const totalPages = data ? Math.ceil(data.total / data.size) : 1

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">{t('admin.users')}</h1>
          <Button size="sm" onClick={() => setShowCreate(true)} icon={<Plus className="w-4 h-4" />}>
            {t('admin.createUser')}
          </Button>
        </div>

        {/* Create user modal */}
        {showCreate && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={() => setShowCreate(false)}>
            <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
              <h3 className="text-lg font-semibold mb-4">{t('admin.createUser')}</h3>
              <div className="space-y-3">
                <input type="text" placeholder="Full name" value={createForm.full_name} onChange={(e) => setCreateForm({ ...createForm, full_name: e.target.value })}
                  className="input-field" />
                <input type="email" placeholder="Email" value={createForm.email} onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                  className="input-field" />
                <input type="password" placeholder="Password (min 8)" value={createForm.password} onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
                  className="input-field" minLength={8} />
                <input type="text" placeholder="Company (optional)" value={createForm.company} onChange={(e) => setCreateForm({ ...createForm, company: e.target.value })}
                  className="input-field" />
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={createForm.is_admin} onChange={(e) => setCreateForm({ ...createForm, is_admin: e.target.checked })}
                    className="rounded border-gray-300" />
                  {t('admin.isAdmin')}
                </label>
              </div>
              <div className="flex justify-end gap-2 mt-4">
                <Button variant="outline" size="sm" onClick={() => setShowCreate(false)}>{t('settings.cancel')}</Button>
                <Button size="sm" onClick={handleCreate} loading={createSaving}>{t('admin.createUser')}</Button>
              </div>
            </div>
          </div>
        )}

        {/* Delete confirm modal */}
        {deleteId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={() => setDeleteId(null)}>
            <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-sm mx-4" onClick={(e) => e.stopPropagation()}>
              <p className="text-sm mb-4">{t('admin.confirmDelete')}</p>
              <div className="flex justify-end gap-2">
                <Button variant="outline" size="sm" onClick={() => setDeleteId(null)}>{t('settings.cancel')}</Button>
                <Button size="sm" onClick={handleDelete} loading={deleteSaving}>{t('admin.deleteUser')}</Button>
              </div>
            </div>
          </div>
        )}

        {/* Reset password modal */}
        {resetFor && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={() => { setResetFor(null); setResetPw('') }}>
            <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-sm mx-4" onClick={(e) => e.stopPropagation()}>
              <h3 className="text-sm font-semibold mb-3">{t('admin.resetPassword')}</h3>
              <input type="password" placeholder={t('admin.newPasswordPlaceholder')} value={resetPw}
                onChange={(e) => setResetPw(e.target.value)} className="input-field mb-3" minLength={8} />
              <div className="flex justify-end gap-2">
                <Button variant="outline" size="sm" onClick={() => { setResetFor(null); setResetPw('') }}>{t('settings.cancel')}</Button>
                <Button size="sm" onClick={handleResetPassword} loading={resetSaving} disabled={resetPw.length < 8}>{t('admin.resetPasswordBtn')}</Button>
              </div>
            </div>
          </div>
        )}

        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input type="text" placeholder={t('common.search')} value={searchInput} onChange={(e) => setSearchInput(e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg text-sm" />
          </div>
          <button type="submit" className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">
            {t('common.search')}
          </button>
        </form>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('admin.user')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('admin.company')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('admin.audits')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('admin.status')}</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Admin</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.detail.created')}</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('common.actions')}</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr><td colSpan={8} className="px-6 py-12 text-center"><div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 inline-block" /></td></tr>
                ) : data?.items.length === 0 ? (
                  <tr><td colSpan={8} className="px-6 py-12 text-center text-gray-500">{t('admin.noUsers')}</td></tr>
                ) : (
                  data?.items.map((u: AdminUser) => (
                    <tr key={u.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Link to={`/admin/users/${u.id}`} className="text-sm font-medium text-primary-600 hover:text-primary-700">{u.full_name}</Link>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{u.email}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{u.company || '-'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{u.audit_count}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1 text-xs font-medium ${u.is_active ? 'text-green-700' : 'text-red-700'}`}>
                          {u.is_active ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                          {u.is_active ? t('admin.active') : t('admin.inactive')}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {u.is_admin ? <span className="inline-flex items-center gap-1 text-xs font-medium text-purple-700"><Shield className="w-3 h-3" /> Admin</span>
                          : <span className="text-xs text-gray-400">-</span>}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(u.created_at).toLocaleDateString(t('common.dateFormat'))}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                        <div className="flex items-center justify-end gap-1">
                          <button onClick={() => toggleActive(u)} disabled={toggling === u.id}
                            className={`text-xs px-2 py-1 rounded ${u.is_active ? 'text-red-600 hover:bg-red-50' : 'text-green-600 hover:bg-green-50'}`}>
                            {u.is_active ? t('admin.deactivate') : t('admin.activate')}
                          </button>
                          <button onClick={() => toggleAdmin(u)} disabled={toggling === u.id}
                            className={`text-xs px-2 py-1 rounded ${u.is_admin ? 'text-orange-600 hover:bg-orange-50' : 'text-purple-600 hover:bg-purple-50'}`}>
                            {u.is_admin ? t('admin.demote') : t('admin.promote')}
                          </button>
                          <button onClick={() => setResetFor(u.id)} className="text-xs px-2 py-1 rounded text-blue-600 hover:bg-blue-50" title={t('admin.resetPassword')}>
                            <Key className="w-3 h-3" />
                          </button>
                          <button onClick={() => setDeleteId(u.id)} className="text-xs px-2 py-1 rounded text-red-600 hover:bg-red-50">
                            <Trash2 className="w-3 h-3" />
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
              <span className="text-sm text-gray-500">{data.total} — {t('common.page')} {data.page}/{totalPages}</span>
              <div className="flex gap-2">
                <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1} className="p-1 rounded hover:bg-gray-100 disabled:opacity-50"><ChevronLeft className="w-5 h-5" /></button>
                <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages} className="p-1 rounded hover:bg-gray-100 disabled:opacity-50"><ChevronRight className="w-5 h-5" /></button>
              </div>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
