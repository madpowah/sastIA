import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import api from '../api/client'
import { DashboardLayout } from '../components/Layout'
import { Button } from '../components/ui/Button'
import {
  ArrowLeft,
  Download,
  FileText,
  RefreshCw,
  AlertCircle,
} from 'lucide-react'

export default function Report() {
  const { id } = useParams<{ id: string }>()
  const [markdown, setMarkdown] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [auditName, setAuditName] = useState('')

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const { data } = await api.get(`/reports/${id}`)
        setMarkdown(data.markdown)
        setAuditName(data.audit_id)
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Rapport non disponible')
      } finally {
        setLoading(false)
      }
    }
    fetchReport()
  }, [id])

  const downloadPdf = async () => {
    try {
      const response = await api.get(`/reports/${id}/pdf`, {
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `rapport-audit-${auditName}.pdf`.replace(/\s+/g, '-').toLowerCase()
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to download PDF', err)
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 text-primary-600 animate-spin" />
        </div>
      </DashboardLayout>
    )
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="max-w-2xl mx-auto text-center py-12">
          <AlertCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Rapport non disponible</h2>
          <p className="text-gray-500 mb-6">{error}</p>
          <Link to={`/audits/${id}`}>
            <Button variant="outline" icon={<ArrowLeft className="w-4 h-4" />}>
              Retour à l'audit
            </Button>
          </Link>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <Link
            to={`/audits/${id}`}
            className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeft className="w-4 h-4" />
            Retour à l'audit
          </Link>
          <Button variant="outline" icon={<Download className="w-4 h-4" />} onClick={downloadPdf}>
            Télécharger PDF
          </Button>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8 lg:p-12">
          <div className="report-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {markdown || ''}
            </ReactMarkdown>
          </div>
        </div>

        <div className="flex justify-center mt-8">
          <Button icon={<Download className="w-4 h-4" />} onClick={downloadPdf}>
            Télécharger le rapport en PDF
          </Button>
        </div>
      </div>
    </DashboardLayout>
  )
}
