import { useState, FormEvent, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import { DashboardLayout } from '../components/Layout'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { getProviderGroups, ProviderGroup, ModelInfo } from '../api/providers'
import { useLanguage } from '../i18n/LanguageContext'
import {
  Upload,
  FileCode,
  Shield,
  Link as LinkIcon,
  CheckCircle,
  AlertCircle,
  Server,
  Cpu,
} from 'lucide-react'

export default function NewAudit() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [providerGroups, setProviderGroups] = useState<ProviderGroup[]>([])
  const [selectedProvider, setSelectedProvider] = useState('')
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    repo_url: '',
    analysis_type: 'code',
    docker_analysis_enabled: false,
    model_id: '',
    report_language: 'en',
  })
  const [codeFile, setCodeFile] = useState<File | null>(null)
  const { t } = useLanguage()

  const currentModels = providerGroups.find((g) => g.provider === selectedProvider)?.models || []

  useEffect(() => {
    getProviderGroups().then((groups) => {
      setProviderGroups(groups)
      if (groups.length > 0 && !selectedProvider) {
        setSelectedProvider(groups[0].provider)
      }
    }).catch(() => {})
  }, [])

  useEffect(() => {
    if (selectedProvider && currentModels.length > 0 && !currentModels.find((m) => m.id === formData.model_id)) {
      setFormData((prev) => ({ ...prev, model_id: currentModels[0].id }))
    }
  }, [selectedProvider, providerGroups])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const form = new FormData()
      form.append('name', formData.name)
      form.append('description', formData.description)
      form.append('analysis_type', formData.analysis_type)
      form.append('docker_analysis_enabled', String(formData.docker_analysis_enabled))
      if (formData.repo_url) form.append('repo_url', formData.repo_url)
      if (formData.model_id) form.append('model_id', formData.model_id)
      form.append('report_language', formData.report_language)
      if (codeFile) form.append('code_file', codeFile)

      const { data } = await api.post('/audits/', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      await api.post(`/audits/${data.id}/start`)
      navigate(`/audits/${data.id}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la création de l\'audit')
    } finally {
      setLoading(false)
    }
  }

  return (
    <DashboardLayout>
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">{t('audit.newTitle')}</h1>
          <p className="text-gray-500 mt-1">{t('audit.newSubtitle')}</p>
        </div>

        {/* Steps */}
        <div className="flex items-center gap-4 mb-8">
          {[1, 2].map((s) => (
            <div key={s} className="flex items-center gap-4 flex-1">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold ${
                s <= step ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-400'
              }`}>
                {s < step ? <CheckCircle className="w-5 h-5" /> : s}
              </div>
              {s < 2 && <div className={`h-0.5 flex-1 ${s < step ? 'bg-primary-600' : 'bg-gray-200'}`} />}
            </div>
          ))}
        </div>

        <form onSubmit={handleSubmit}>
          {step === 1 && (
            <Card>
              <h2 className="text-lg font-semibold text-gray-900 mb-6">{t('audit.generalInfo')}</h2>
              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('audit.name')} *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="input-field"
                    placeholder={t('audit.namePlaceholder')}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('audit.description')}</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="input-field min-h-[100px] resize-y"
                    placeholder={t('audit.descriptionPlaceholder')}
                  />
                </div>
              </div>
              <div className="flex justify-end mt-8">
                <Button type="button" onClick={() => setStep(2)} disabled={!formData.name}>
                  {t('audit.next')}
                </Button>
              </div>
            </Card>
          )}

          {step === 2 && (
            <Card>
              <h2 className="text-lg font-semibold text-gray-900 mb-6">{t('audit.codeSource')}</h2>
              <div className="space-y-6">
                <div
                  className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
                    codeFile ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-primary-300 hover:bg-gray-50'
                  }`}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    accept=".zip,.tar.gz,.tgz,.py,.js,.ts,.java,.php,.go,.rs,.rb"
                    onChange={(e) => setCodeFile(e.target.files?.[0] || null)}
                  />
                  {codeFile ? (
                    <div>
                      <FileCode className="w-12 h-12 text-primary-600 mx-auto mb-3" />
                      <p className="font-medium text-gray-900">{codeFile.name}</p>
                      <p className="text-sm text-gray-500 mt-1">
                        {(codeFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  ) : (
                    <div>
                      <Upload className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                      <p className="font-medium text-gray-700">
                        {t('audit.dropCode')}
                      </p>
                      <p className="text-sm text-gray-500 mt-1">
                        {t('audit.dropHint')}
                      </p>
                    </div>
                  )}
                </div>

                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-200" />
                  </div>
                  <div className="relative flex justify-center">
                    <span className="bg-white px-4 text-sm text-gray-500">{t('audit.or')}</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('audit.gitUrl')}
                  </label>
                  <div className="relative">
                    <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="url"
                      value={formData.repo_url}
                      onChange={(e) => setFormData({ ...formData, repo_url: e.target.value })}
                      className="input-field pl-10"
                      placeholder={t('audit.gitPlaceholder')}
                    />
                  </div>
                </div>

                <div className="border-t border-gray-200 pt-6">
                  <label className="flex items-center gap-3 cursor-pointer mb-6">
                    <input
                      type="checkbox"
                      checked={formData.docker_analysis_enabled}
                      onChange={(e) => setFormData({ ...formData, docker_analysis_enabled: e.target.checked })}
                      className="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <div>
                      <p className="font-medium text-gray-900">{t('audit.dockerValidation')}</p>
                      <p className="text-sm text-gray-500">
                        {t('audit.dockerHint')}
                      </p>
                    </div>
                  </label>

                  <div className="border-t border-gray-100 pt-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                      <Cpu className="w-4 h-4" />
                      {t('audit.aiModel')}
                    </label>
                    <div className="grid grid-cols-5 gap-3">
                      <div className="col-span-2">
                        <select
                          value={selectedProvider}
                          onChange={(e) => setSelectedProvider(e.target.value)}
                          className="input-field"
                        >
                          {providerGroups.map((g) => (
                            <option key={g.provider} value={g.provider}>
                              {g.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="col-span-3">
                        <select
                          value={formData.model_id}
                          onChange={(e) => setFormData({ ...formData, model_id: e.target.value })}
                          className="input-field"
                        >
                          {currentModels.map((m) => (
                            <option key={m.id} value={m.id}>
                              {m.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      {t('audit.modelFormat')} : <code className="bg-gray-100 px-1 rounded">{selectedProvider || 'provider'}/{currentModels.find((m) => m.id === formData.model_id)?.id.split('/').slice(1).join('/') || 'modele'}</code>
                    </p>
                  </div>

                  <div className="border-t border-gray-100 pt-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">{t('audit.reportLanguage')}</label>
                    <select
                      value={formData.report_language}
                      onChange={(e) => setFormData({ ...formData, report_language: e.target.value })}
                      className="input-field"
                    >
                      <option value="en">English</option>
                      <option value="fr">Français</option>
                    </select>
                  </div>
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-3 bg-red-50 text-red-700 px-4 py-3 rounded-xl mt-6 text-sm">
                  <AlertCircle className="w-5 h-5 shrink-0" />
                  {error}
                </div>
              )}

              <div className="flex justify-between mt-8">
                <Button type="button" variant="outline" onClick={() => setStep(1)}>
                  {t('audit.back')}
                </Button>
                <Button type="submit" loading={loading} icon={<Shield className="w-4 h-4" />}>
                  {t('audit.launch')}
                </Button>
              </div>
            </Card>
          )}
        </form>
      </div>
    </DashboardLayout>
  )
}
