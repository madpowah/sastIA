import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { DashboardLayout } from '../../components/Layout'
import { ArrowLeft, RefreshCw, FileText, Terminal, AlertTriangle } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import {
  getAdminAudit,
  getAdminAuditLog,
  retryAdminAudit,
  type AdminAudit,
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

function formatDuration(seconds: number | null): string {
  if (seconds === null) return '-'
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h}h ${m}m`
}

export default function AdminAuditDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [audit, setAudit] = useState<AdminAudit | null>(null)
  const [reportMd, setReportMd] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [logContent, setLogContent] = useState<string>('')
  const [tab, setTab] = useState<'report' | 'log'>('report')
  const [loading, setLoading] = useState(true)
  const [retrying, setRetrying] = useState(false)

  const fetchAudit = useCallback(() => {
    if (!id) return
    getAdminAudit(id).then((d) => {
      setAudit(d.audit)
      setReportMd(d.report_markdown)
      setErrorMsg(d.error_message)
    }).catch(console.error).finally(() => setLoading(false))
  }, [id])

  const fetchLog = useCallback(() => {
    if (!id) return
    getAdminAuditLog(id).then((d) => setLogContent(d.log)).catch(() => setLogContent('(worker indisponible)'))
  }, [id])

  useEffect(() => {
    fetchAudit()
  }, [fetchAudit])

  useEffect(() => {
    if (tab === 'log') fetchLog()
  }, [tab, fetchLog])

  // Auto-refresh log when audit is running
  useEffect(() => {
    if (!audit) return
    if (audit.status === 'analyzing_code' || audit.status === 'analyzing_docker') {
      const interval = setInterval(() => {
        fetchLog()
        fetchAudit()
      }, 5000)
      return () => clearInterval(interval)
    }
  }, [audit?.status, fetchLog, fetchAudit])

  const handleRetry = async () => {
    if (!id) return
    setRetrying(true)
    try {
      await retryAdminAudit(id)
      fetchAudit()
    } finally {
      setRetrying(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    )
  }

  if (!audit) {
    return <div className="text-red-600">Audit introuvable.</div>
  }

  const canRetry = audit.status === 'failed' || audit.status === 'pending'

  return (
    <DashboardLayout>
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/admin/audits" className="p-2 rounded-lg hover:bg-gray-100">
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">{audit.name}</h1>
              <StatusBadge status={audit.status} />
            </div>
            <p className="text-sm text-gray-500 mt-1">
              par <span className="font-medium">{audit.user_email}</span>
            </p>
          </div>
        </div>

        {canRetry && (
          <button
            onClick={handleRetry}
            disabled={retrying}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${retrying ? 'animate-spin' : ''}`} />
            Relancer l'analyse
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-xs text-gray-500 mb-1">Créé le</p>
          <p className="text-sm font-medium">{new Date(audit.created_at).toLocaleString('fr-FR')}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-xs text-gray-500 mb-1">Terminé le</p>
          <p className="text-sm font-medium">{audit.completed_at ? new Date(audit.completed_at).toLocaleString('fr-FR') : '-'}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-xs text-gray-500 mb-1">Durée</p>
          <p className="text-sm font-medium">{formatDuration(audit.duration_seconds)}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-xs text-gray-500 mb-1">Vulnérabilités</p>
          <p className="text-sm font-medium">{audit.total_vulnerabilities}</p>
        </div>
      </div>

      {errorMsg && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-red-800">Erreur</p>
            <pre className="text-sm text-red-700 mt-1 whitespace-pre-wrap">{errorMsg}</pre>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="border-b border-gray-200">
          <nav className="flex">
            <button
              onClick={() => setTab('report')}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                tab === 'report'
                  ? 'border-primary-600 text-primary-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <FileText className="w-4 h-4" />
              Rapport
            </button>
            <button
              onClick={() => setTab('log')}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                tab === 'log'
                  ? 'border-primary-600 text-primary-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <Terminal className="w-4 h-4" />
              Logs opencode
            </button>
          </nav>
        </div>

        <div className="p-6">
          {tab === 'report' ? (
            reportMd ? (
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown>{reportMd}</ReactMarkdown>
              </div>
            ) : (
              <p className="text-gray-500 text-sm">Aucun rapport disponible.</p>
            )
          ) : (
            <pre className="text-xs font-mono bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto max-h-[600px] whitespace-pre-wrap">
              {logContent || '(aucun log)'}
            </pre>
          )}
        </div>
      </div>
    </div>
    </DashboardLayout>
  )
}
