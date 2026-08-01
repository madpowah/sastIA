import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import api from '../api/client'
import { DashboardLayout } from '../components/Layout'
import { useLanguage } from '../i18n/LanguageContext'
import { Button } from '../components/ui/Button'
import {
  ArrowLeft,
  Download,
  FileText,
  Archive,
  RefreshCw,
  AlertCircle,
  X,
  FileCode,
} from 'lucide-react'

export default function Report() {
  const { t } = useLanguage()
  const { id } = useParams<{ id: string }>()
  const [markdown, setMarkdown] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [auditName, setAuditName] = useState('')
  const [modalContent, setModalContent] = useState<string | null>(null)
  const [modalTitle, setModalTitle] = useState('')
  const [modalLoading, setModalLoading] = useState(false)
  const [modalError, setModalError] = useState('')
  const [modalRender, setModalRender] = useState(false)
  const contentRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const { data } = await api.get(`/reports/${id}`)
        setMarkdown(data.markdown)
        setAuditName(data.audit_id)
      } catch (err: any) {
        setError(err.response?.data?.detail || t('audit.detail.noReport'))
      } finally {
        setLoading(false)
      }
    }
    fetchReport()
  }, [id])

  useEffect(() => {
    const el = contentRef.current
    if (!el) return
    const handler = (e: MouseEvent) => {
      const target = (e.target as HTMLElement).closest('a')
      if (!target) return
      const href = target.getAttribute('href')
      if (!href) return
      let apiPath: string | null = null
      if (href.startsWith('/api/audits/')) {
        // Strip any #anchor — the modal shows the file top.
        apiPath = href.replace(/^\/api/, '').split('#')[0]
      } else if (/^(poc|exploit_tests|README|report|phase\d|phase\d[a-z]|validation_results|docker_environment)(\/|\.|#)/.test(href)) {
        // Relative artifact link (legacy reports before link rewriting)
        // Strip any #anchor (scroll target inside the artifact) — the modal shows the file top.
        const base = href.split('#')[0]
        apiPath = `/audits/${id}/artifacts/${base}`
      }
      if (!apiPath) return
      e.preventDefault()
      e.stopPropagation()
      const parts = decodeURIComponent(apiPath).split('/')
      const filename = parts[parts.length - 1]
      setModalTitle(filename)
      setModalContent(null)
      setModalError('')
      setModalLoading(true)
      setModalRender(false)
      api.get(apiPath, { responseType: 'text' })
        .then(({ data }) => {
          setModalContent(data)
          setModalLoading(false)
        })
        .catch(() => {
          setModalError('Failed to load artifact')
          setModalLoading(false)
        })
    }
    el.addEventListener('click', handler)
    return () => el.removeEventListener('click', handler)
  }, [id, markdown])

  const downloadPdf = async () => {
    try {
      const response = await api.get(`/reports/${id}/pdf`, { responseType: 'blob' })
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

  const downloadZip = async () => {
    try {
      const response = await api.get(`/reports/${id}/zip`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `rapport-complet-${auditName}.zip`.replace(/\s+/g, '-').toLowerCase()
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to download ZIP', err)
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
          <h2 className="text-xl font-semibold text-gray-900 mb-2">{t('audit.detail.noReport')}</h2>
          <p className="text-gray-500 mb-6">{error}</p>
          <Link to={`/audits/${id}`}>
            <Button variant="outline" icon={<ArrowLeft className="w-4 h-4" />}>
              {t('audit.backToAudit')}
            </Button>
          </Link>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <Link to={`/audits/${id}`}>
            <Button variant="outline" icon={<ArrowLeft className="w-4 h-4" />}>
              {t('audit.backToAudit')}
            </Button>
          </Link>
          <div className="flex gap-2">
            <Button onClick={downloadZip} variant="outline" icon={<Archive className="w-4 h-4" />}>
              ZIP
            </Button>
            <Button onClick={downloadPdf} icon={<FileText className="w-4 h-4" />}>
              {t('audit.detail.downloadPdf')}
            </Button>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8 lg:p-12">
          <div className="prose prose-gray max-w-none">
            <div className="report-content" ref={contentRef}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {markdown || ''}
              </ReactMarkdown>
            </div>
          </div>
        </div>

        <div className="flex justify-center mt-8 gap-3">
          <Button icon={<Download className="w-4 h-4" />} onClick={downloadZip} variant="outline">
            Télécharger le dossier complet (ZIP)
          </Button>
          <Button icon={<FileText className="w-4 h-4" />} onClick={downloadPdf}>
            {t('audit.detail.downloadPdf')}
          </Button>
        </div>
      </div>

      {modalContent !== null || modalLoading || modalError ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={() => { setModalContent(null); setModalLoading(false); setModalError('') }}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 shrink-0">
              <div className="flex items-center gap-3">
                <FileCode className="w-5 h-5 text-cyan-600" />
                <h2 className="text-lg font-semibold text-gray-900">{modalTitle}</h2>
                <span className="badge bg-purple-100 text-purple-700 text-xs">
                  {modalTitle.endsWith('.md') ? 'PoC' : 'Exploit Test'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {modalTitle.endsWith('.md') && (
                  <button onClick={() => setModalRender(!modalRender)} className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${modalRender ? 'bg-cyan-100 text-cyan-700' : 'bg-gray-100 text-gray-600'}`}>
                    {modalRender ? 'Code brut' : 'Afficher MD'}
                  </button>
                )}
                <button onClick={() => { setModalContent(null); setModalLoading(false); setModalError('') }} className="p-2 hover:bg-gray-100 rounded-xl transition-colors">
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-auto p-6">
              {modalLoading ? (
                <div className="flex items-center justify-center h-48">
                  <RefreshCw className="w-8 h-8 text-cyan-600 animate-spin" />
                </div>
              ) : modalError ? (
                <div className="flex items-center justify-center h-48 text-red-500">
                  <AlertCircle className="w-6 h-6 mr-2" /> {modalError}
                </div>
              ) : modalRender && modalTitle.endsWith('.md') ? (
                <div className="prose prose-sm max-w-none p-6">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {modalContent || ''}
                  </ReactMarkdown>
                </div>
              ) : (
                <pre className="bg-gray-900 text-cyan-100 rounded-xl p-6 overflow-x-auto text-sm font-mono leading-relaxed whitespace-pre-wrap">
                  {modalContent}
                </pre>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </DashboardLayout>
  )
}
