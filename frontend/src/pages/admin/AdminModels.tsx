import { useState, useEffect } from 'react'
import { DashboardLayout } from '../../components/Layout'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import {
  getAdminModels,
  refreshAdminModels,
  toggleAdminModel,
  type AvailableModel,
} from '../../api/admin'
import { useLanguage } from '../../i18n/LanguageContext'
import { RefreshCw, CheckCircle, XCircle, Cpu, AlertCircle } from 'lucide-react'

export default function AdminModelsPage() {
  const { t } = useLanguage()
  const [models, setModels] = useState<AvailableModel[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [toggling, setToggling] = useState<string | null>(null)
  const [error, setError] = useState('')

  const fetch = async () => {
    setLoading(true)
    try {
      const data = await getAdminModels()
      setModels(data)
    } catch { setError(t('common.error')) }
    finally { setLoading(false) }
  }

  useEffect(() => { fetch() }, [])

  const handleRefresh = async () => {
    setRefreshing(true)
    setError('')
    try {
      const data = await refreshAdminModels()
      setModels(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || t('common.error'))
    } finally { setRefreshing(false) }
  }

  const handleToggle = async (m: AvailableModel) => {
    setToggling(m.model_id)
    try {
      const updated = await toggleAdminModel(m.model_id, !m.enabled)
      setModels((prev) => prev.map((x) => x.model_id === updated.model_id ? updated : x))
    } catch { }
    finally { setToggling(null) }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">{t('admin.modelMgmt')}</h1>
          <Button onClick={handleRefresh} loading={refreshing} icon={<RefreshCw className="w-4 h-4" />} size="sm">
            {t('admin.refreshModels')}
          </Button>
        </div>

        {error && (
          <div className="flex items-center gap-3 bg-red-50 text-red-700 px-4 py-3 rounded-xl text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            {error}
          </div>
        )}

        <Card>
          {loading ? (
            <p className="text-gray-400 text-sm">{t('common.loading')}</p>
          ) : models.length === 0 ? (
            <div className="text-center py-8">
              <Cpu className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 text-sm mb-4">{t('admin.noModels')}</p>
              <Button size="sm" onClick={handleRefresh} loading={refreshing} icon={<RefreshCw className="w-4 h-4" />}>
                {t('admin.refreshModels')}
              </Button>
            </div>
          ) : (
            <div className="space-y-1">
              {models.map((m) => (
                <div key={m.id} className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 rounded-lg transition-colors">
                  <div className="flex items-center gap-3 min-w-0">
                    <button
                      onClick={() => handleToggle(m)}
                      disabled={toggling === m.model_id}
                      className={`shrink-0 w-5 h-5 rounded flex items-center justify-center transition-colors ${
                        m.enabled ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-400'
                      }`}
                    >
                      {m.enabled ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                    </button>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{m.name || m.model_id}</p>
                      <p className="text-xs text-gray-400 font-mono truncate">{m.model_id}</p>
                    </div>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${m.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {m.enabled ? t('admin.enable') : t('admin.disable')}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </DashboardLayout>
  )
}
