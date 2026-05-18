import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../i18n/LanguageContext'
import { DashboardLayout } from '../components/Layout'
import { StatCard } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import {
  Search,
  Shield,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  TrendingUp,
  ArrowRight,
  FileText,
  ExternalLink,
  RefreshCw,
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

interface DashboardData {
  total_audits: number
  pending_audits: number
  completed_audits: number
  failed_audits: number
  total_critical: number
  total_high: number
  total_medium: number
  total_low: number
  recent_audits: Audit[]
}

const statusLabels: Record<string, { label: string; color: string }> = {
  pending: { label: 'En attente', color: 'bg-yellow-100 text-yellow-700' },
  analyzing_code: { label: 'Analyse code...', color: 'bg-blue-100 text-blue-700' },
  analyzing_docker: { label: 'Analyse Docker...', color: 'bg-purple-100 text-purple-700' },
  completed: { label: 'Terminé', color: 'bg-green-100 text-green-700' },
  failed: { label: 'Échec', color: 'bg-red-100 text-red-700' },
}

export default function Dashboard() {
  const { user } = useAuth()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const { t } = useLanguage()

  const fetchDashboard = async () => {
    setLoading(true)
    try {
      const { data: result } = await api.get('/audits/dashboard')
      setData(result)
    } catch (err) {
      console.error('Failed to fetch dashboard', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
  }, [])

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 text-primary-600 animate-spin" />
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {t('dashboard.greeting')}, {user?.full_name}
            </h1>
            <p className="text-gray-500 mt-1">{t('dashboard.summary')}</p>
          </div>
          <Link to="/audits/new">
            <Button icon={<Search className="w-4 h-4" />}>
              {t('dashboard.newAudit')}
            </Button>
          </Link>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            label={t('dashboard.total')}
            value={data?.total_audits || 0}
            icon={<Shield className="w-6 h-6 text-primary-600" />}
            color="bg-primary-50"
          />
          <StatCard
            label={t('dashboard.inProgress')}
            value={data?.pending_audits || 0}
            icon={<Clock className="w-6 h-6 text-yellow-600" />}
            color="bg-yellow-50"
          />
          <StatCard
            label={t('dashboard.completed')}
            value={data?.completed_audits || 0}
            icon={<CheckCircle className="w-6 h-6 text-green-600" />}
            color="bg-green-50"
          />
          <StatCard
            label={t('dashboard.failed')}
            value={data?.failed_audits || 0}
            icon={<XCircle className="w-6 h-6 text-red-600" />}
            color="bg-red-50"
          />
        </div>

        {/* Vulnerabilities Summary */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.vulnerabilities')}</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-red-50 rounded-xl p-4 border border-red-100">
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle className="w-4 h-4 text-red-600" />
                <span className="text-sm font-medium text-red-700">{t('dashboard.critical')}</span>
              </div>
              <p className="text-2xl font-bold text-red-700">{data?.total_critical || 0}</p>
            </div>
            <div className="bg-orange-50 rounded-xl p-4 border border-orange-100">
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle className="w-4 h-4 text-orange-600" />
                <span className="text-sm font-medium text-orange-700">{t('dashboard.high')}</span>
              </div>
              <p className="text-2xl font-bold text-orange-700">{data?.total_high || 0}</p>
            </div>
            <div className="bg-yellow-50 rounded-xl p-4 border border-yellow-100">
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle className="w-4 h-4 text-yellow-600" />
                <span className="text-sm font-medium text-yellow-700">{t('dashboard.medium')}</span>
              </div>
              <p className="text-2xl font-bold text-yellow-700">{data?.total_medium || 0}</p>
            </div>
            <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-700">{t('dashboard.low')}</span>
              </div>
              <p className="text-2xl font-bold text-blue-700">{data?.total_low || 0}</p>
            </div>
          </div>
        </div>

        {/* Recent Audits */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
          <div className="flex items-center justify-between p-6 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">{t('dashboard.recentAudits')}</h2>
            <Link to="/audits" className="text-sm font-medium text-primary-600 hover:text-primary-700 flex items-center gap-1">
              {t('dashboard.viewAll')} <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {data?.recent_audits && data.recent_audits.length > 0 ? (
            <div className="divide-y divide-gray-100">
              {data.recent_audits.map((audit) => (
                <Link
                  key={audit.id}
                  to={`/audits/${audit.id}`}
                  className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <FileText className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{audit.name}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(audit.created_at).toLocaleDateString('fr-FR', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric',
                        })}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="flex items-center gap-3 text-sm">
                      {audit.vulnerabilities_critical > 0 && (
                        <span className="badge-critical">{audit.vulnerabilities_critical} {t('dashboard.critAbbr')}</span>
                      )}
                      {audit.vulnerabilities_high > 0 && (
                        <span className="badge-high">{audit.vulnerabilities_high} {t('dashboard.highAbbr')}</span>
                      )}
                      {audit.vulnerabilities_medium > 0 && (
                        <span className="badge-medium">{audit.vulnerabilities_medium} {t('dashboard.medAbbr')}</span>
                      )}
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusLabels[audit.status]?.color || 'bg-gray-100 text-gray-700'}`}>
                      {statusLabels[audit.status]?.label || audit.status}
                    </span>
                    <ExternalLink className="w-4 h-4 text-gray-300" />
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 mb-2">{t('dashboard.noAudits')}</p>
              <p className="text-sm text-gray-400 mb-6">{t('dashboard.startFirstAudit')}</p>
              <Link to="/audits/new">
                <Button icon={<Search className="w-4 h-4" />}>
                  {t('dashboard.launchAudit')}
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
