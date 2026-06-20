import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useLanguage } from '../i18n/LanguageContext'
import api from '../api/client'
import { DashboardLayout } from '../components/Layout'
import { Button } from '../components/ui/Button'
import {
  ArrowLeft,
  FileText,
  Shield,
  Clock,
  CheckCircle,
  XCircle,
  Download,
  ExternalLink,
  AlertTriangle,
  RefreshCw,
  Server,
  Cpu,
  Play,
} from 'lucide-react'

interface Audit {
  id: string
  name: string
  description: string | null
  status: string
  docker_status: string
  vulnerabilities_critical: number
  vulnerabilities_high: number
  vulnerabilities_medium: number
  vulnerabilities_low: number
  vulnerabilities_info: number
  total_vulnerabilities: number
  analysis_type: string
  docker_analysis_enabled: number
  report_markdown: string | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

const dockerStatusConfig = (t: (key: string) => string): Record<string, { label: string; color: string }> => ({
  not_started: { label: t('audit.docker.not_started'), color: 'text-gray-500' },
  pending: { label: t('audit.docker.pending'), color: 'text-blue-600' },
  success: { label: t('audit.docker.success'), color: 'text-green-600' },
  failed: { label: t('audit.docker.failed'), color: 'text-red-600' },
})

export default function AuditDetail() {
  const { id } = useParams<{ id: string }>()
  const { t } = useLanguage()

  const statusConfig: Record<string, { label: string; color: string; bg: string; icon: any }> = {
    pending: { label: t('audit.status.pending'), color: 'text-yellow-700', bg: 'bg-yellow-50 border-yellow-200', icon: Clock },
    analyzing_code: { label: t('audit.status.analyzing_code'), color: 'text-blue-700', bg: 'bg-blue-50 border-blue-200', icon: RefreshCw },
    analyzing_docker: { label: t('audit.status.analyzing_docker'), color: 'text-purple-700', bg: 'bg-purple-50 border-purple-200', icon: Server },
    completed: { label: t('audit.status.completed'), color: 'text-green-700', bg: 'bg-green-50 border-green-200', icon: CheckCircle },
    failed: { label: t('audit.status.failed'), color: 'text-red-700', bg: 'bg-red-50 border-red-200', icon: XCircle },
  }
  const startingRef = useRef(false)
  const [audit, setAudit] = useState<Audit | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchAudit = async () => {
    try {
      const { data } = await api.get(`/audits/${id}`)
      setAudit(data)
    } catch (err) {
      console.error('Failed to fetch audit', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAudit()
    const interval = setInterval(fetchAudit, 10000)
    return () => clearInterval(interval)
  }, [id])

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 text-primary-600 animate-spin" />
        </div>
      </DashboardLayout>
    )
  }

  if (!audit) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-gray-500">Audit introuvable</p>
          <Link to="/dashboard" className="text-primary-600 mt-4 inline-block">Retour au tableau de bord</Link>
        </div>
      </DashboardLayout>
    )
  }

  const status = statusConfig[audit.status] || statusConfig.pending
  const StatusIcon = status.icon
  const isStillPending = audit.status === 'pending'
  const isAnalyzing = audit.status === 'analyzing_code' || audit.status === 'analyzing_docker'
  const isCompleted = audit.status === 'completed'
  const hasError = audit.status === 'failed'

  const startAnalysis = async () => {
    if (startingRef.current) return
    startingRef.current = true
    try {
      await api.post(`/audits/${audit.id}/start`)
      setAudit(prev => prev ? { ...prev, status: 'analyzing_code' } : null)
    } catch (err: any) {
      console.error('Failed to start analysis', err)
    } finally {
      startingRef.current = false
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <Link to="/dashboard" className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
          <ArrowLeft className="w-4 h-4" />
          Retour au tableau de bord
        </Link>

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{audit.name}</h1>
            <p className="text-gray-500 mt-1">
              {t('audit.detail.created')} {audit.created_at ? new Date(audit.created_at).toLocaleDateString(t('common.dateFormat'), {
                day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit'
              }) : '-'}
            </p>
          </div>
          <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${status.bg} ${status.color}`}>
            <StatusIcon className={`w-5 h-5 ${audit.status === 'analyzing_code' || audit.status === 'analyzing_docker' ? 'animate-spin' : ''}`} />
            <span className="font-medium">{status.label}</span>
          </div>
        </div>

        {hasError && audit.error_message && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-red-800">Erreur lors de l'analyse</p>
              <p className="text-sm text-red-600 mt-1">{audit.error_message}</p>
            </div>
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Type d'analyse</h2>
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-xl ${audit.docker_analysis_enabled ? 'bg-purple-50' : 'bg-blue-50'}`}>
                {audit.docker_analysis_enabled ? (
                  <Server className="w-6 h-6 text-purple-600" />
                ) : (
                  <Cpu className="w-6 h-6 text-blue-600" />
                )}
              </div>
              <div>
                <p className="font-medium text-gray-900">
                  {audit.docker_analysis_enabled ? 'Analyse complète + Docker' : 'Analyse de code uniquement'}
                </p>
                {audit.docker_analysis_enabled && (
                  <p className={`text-sm mt-1 ${dockerStatusConfig(t)[audit.docker_status]?.color || 'text-gray-500'}`}>
                    Docker : {dockerStatusConfig(t)[audit.docker_status]?.label || audit.docker_status}
                  </p>
                )}
              </div>
            </div>
          </div>

          {isCompleted && (
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('audit.detail.vulnerabilities')}</h2>
              <div className="flex items-center gap-2 mb-4">
                <span className="text-3xl font-bold text-gray-900">{audit.total_vulnerabilities}</span>
                <span className="text-gray-500">totales</span>
              </div>
              <div className="grid grid-cols-4 gap-3">
                <div className="text-center p-2 bg-red-50 rounded-lg">
                  <p className="text-lg font-bold text-red-700">{audit.vulnerabilities_critical}</p>
                  <p className="text-xs text-red-600">Crit.</p>
                </div>
                <div className="text-center p-2 bg-orange-50 rounded-lg">
                  <p className="text-lg font-bold text-orange-700">{audit.vulnerabilities_high}</p>
                  <p className="text-xs text-orange-600">Haut</p>
                </div>
                <div className="text-center p-2 bg-yellow-50 rounded-lg">
                  <p className="text-lg font-bold text-yellow-700">{audit.vulnerabilities_medium}</p>
                  <p className="text-xs text-yellow-600">Moy.</p>
                </div>
                <div className="text-center p-2 bg-blue-50 rounded-lg">
                  <p className="text-lg font-bold text-blue-700">{audit.vulnerabilities_low}</p>
                  <p className="text-xs text-blue-600">Basse</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        {isCompleted && (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('audit.detail.report')}</h2>
            <p className="text-gray-500 mb-6">
              Consultez le rapport détaillé de l'audit avec toutes les vulnérabilités détectées,
              les scores CVSS et les recommandations de correction.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link to={`/audits/${audit.id}/report`}>
                <Button icon={<FileText className="w-4 h-4" />}>
                  Voir le rapport
                </Button>
              </Link>
              <Button
                variant="outline"
                icon={<Download className="w-4 h-4" />}
                onClick={async () => {
                  try {
                    const response = await api.get(`/reports/${audit.id}/pdf`, {
                      responseType: 'blob',
                    })
                    const url = window.URL.createObjectURL(new Blob([response.data]))
                    const a = document.createElement('a')
                    a.href = url
                    a.download = `rapport-${audit.name}.pdf`.replace(/\s+/g, '-').toLowerCase()
                    a.click()
                    window.URL.revokeObjectURL(url)
                  } catch (err) {
                    console.error('Failed to download PDF', err)
                  }
                }}
              >
                {t('audit.detail.downloadPdf')}
              </Button>
            </div>
          </div>
        )}

        {isStillPending && (
          <div className="bg-gray-50 border border-gray-200 rounded-2xl p-8 text-center">
            <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">{t('audit.readyToLaunch')}</h2>
            <p className="text-gray-500 mb-6">
              {t('audit.detail.startHint')}
            </p>
            <Button
              onClick={startAnalysis}
              loading={startingRef.current}
              icon={<Play className="w-4 h-4" />}
              size="lg"
            >
              {t('audit.detail.startAnalysis')}
            </Button>
          </div>
        )}

        {isAnalyzing && (
          <div className="bg-blue-50 border border-blue-200 rounded-2xl p-8 text-center">
            <RefreshCw className="w-12 h-12 text-blue-500 mx-auto mb-4 animate-spin" />
            <h2 className="text-xl font-semibold text-blue-900 mb-2">Analyse en cours</h2>
            <p className="text-blue-700">
              {t('audit.processing')}
            </p>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
