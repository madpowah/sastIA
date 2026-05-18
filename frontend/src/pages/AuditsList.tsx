import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { DashboardLayout } from '../components/Layout'
import { useLanguage } from '../i18n/LanguageContext'
import { Button } from '../components/ui/Button'
import {
  FileText,
  Search,
  ExternalLink,
  ArrowRight,
  RefreshCw,
  Filter,
} from 'lucide-react'

interface Audit {
  id: string
  name: string
  status: string
  vulnerabilities_critical: number
  vulnerabilities_high: number
  vulnerabilities_medium: number
  vulnerabilities_low: number
  total_vulnerabilities: number
  created_at: string
  completed_at: string | null
}

export default function AuditsList() {
  const { t } = useLanguage()

  const statusLabels: Record<string, { label: string; color: string }> = {
    pending: { label: t('audit.status.pending'), color: 'bg-yellow-100 text-yellow-700' },
    analyzing_code: { label: t('audit.status.analyzing_code'), color: 'bg-blue-100 text-blue-700' },
    analyzing_docker: { label: t('audit.status.analyzing_docker'), color: 'bg-purple-100 text-purple-700' },
    completed: { label: t('audit.status.completed'), color: 'bg-green-100 text-green-700' },
    failed: { label: t('audit.status.failed'), color: 'bg-red-100 text-red-700' },
  }
  const [audits, setAudits] = useState<Audit[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')

  const fetchAudits = async () => {
    try {
      const { data } = await api.get('/audits/')
      setAudits(data)
    } catch (err) {
      console.error('Failed to fetch audits', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAudits()
  }, [])

  const filteredAudits = filter === 'all' ? audits : audits.filter(a => a.status === filter)

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{t('nav.myAudits')}</h1>
            <p className="text-gray-500 mt-1">{t('audit.listSubtitle')}</p>
          </div>
          <Link to="/audits/new">
            <Button icon={<Search className="w-4 h-4" />}>
              {t('dashboard.newAudit')}
            </Button>
          </Link>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 overflow-x-auto pb-2">
          <Filter className="w-5 h-5 text-gray-400 shrink-0" />
          {[
            { value: 'all', label: t('common.all') },
            { value: 'pending', label: t('audit.status.pending') },
            { value: 'analyzing_code', label: t('audit.status.analyzing_code') },
            { value: 'analyzing_docker', label: t('audit.status.analyzing_docker') },
            { value: 'completed', label: t('audit.status.completed') },
            { value: 'failed', label: t('audit.status.failed') },
          ].map((f) => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-colors ${
                filter === f.value
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* List */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="w-8 h-8 text-primary-600 animate-spin" />
          </div>
        ) : filteredAudits.length > 0 ? (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="divide-y divide-gray-100">
              {filteredAudits.map((audit) => (
                <Link
                  key={audit.id}
                  to={`/audits/${audit.id}`}
                  className="flex items-center justify-between px-6 py-5 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="p-2 rounded-xl bg-gray-50">
                      <FileText className="w-5 h-5 text-gray-500" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{audit.name}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(audit.created_at).toLocaleDateString(t('common.dateFormat'), {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    {audit.status === 'completed' && (
                      <>
                        {audit.vulnerabilities_critical > 0 && (
                          <div className="text-center">
                            <p className="text-lg font-bold text-red-600">{audit.vulnerabilities_critical}</p>
                            <p className="text-xs text-red-500">crit.</p>
                          </div>
                        )}
                        {audit.vulnerabilities_high > 0 && (
                          <div className="text-center">
                            <p className="text-lg font-bold text-orange-600">{audit.vulnerabilities_high}</p>
                            <p className="text-xs text-orange-500">haut</p>
                          </div>
                        )}
                        {audit.vulnerabilities_medium > 0 && (
                          <div className="text-center">
                            <p className="text-lg font-bold text-yellow-600">{audit.vulnerabilities_medium}</p>
                            <p className="text-xs text-yellow-500">moy.</p>
                          </div>
                        )}
                      </>
                    )}
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusLabels[audit.status]?.color || 'bg-gray-100 text-gray-700'}`}>
                      {statusLabels[audit.status]?.label || audit.status}
                    </span>
                    <ExternalLink className="w-4 h-4 text-gray-300" />
                  </div>
                </Link>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-16 bg-white rounded-2xl border border-gray-100 shadow-sm">
            <FileText className="w-16 h-16 text-gray-200 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">{t('dashboard.noAudits')}</h3>
            <p className="text-gray-500 mb-6">
               {filter === 'all' ? t('audit.noAuditYet') : t('audit.noAuditFilter')}
            </p>
            {filter === 'all' && (
              <Link to="/audits/new">
                <Button icon={<Search className="w-4 h-4" />}>
                  {t('dashboard.newAudit')}
                </Button>
              </Link>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
