import { useState } from 'react'
import { DashboardLayout } from '../components/Layout'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { useLanguage } from '../i18n/LanguageContext'
import api from '../api/client'
import { CheckCircle, AlertCircle, Lock } from 'lucide-react'

export default function Settings() {
  const { t, lang, setLang } = useLanguage()

  const [pwData, setPwData] = useState({ current_password: '', new_password: '' })
  const [pwSaving, setPwSaving] = useState(false)
  const [pwSuccess, setPwSuccess] = useState('')
  const [pwError, setPwError] = useState('')

  const handleChangePassword = async () => {
    if (!pwData.current_password || pwData.new_password.length < 8) return
    setPwSaving(true)
    setPwError('')
    setPwSuccess('')
    try {
      await api.post('/auth/change-password', pwData)
      setPwSuccess(t('settings.passwordChanged'))
      setPwData({ current_password: '', new_password: '' })
    } catch (err: any) {
      setPwError(err.response?.data?.detail || t('common.error'))
    } finally {
      setPwSaving(false)
    }
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">{t('settings.title')}</h1>
          <p className="text-gray-500 mt-1">{t('settings.subtitle')}</p>
        </div>

        {pwError && (
          <div className="flex items-center gap-3 bg-red-50 text-red-700 px-4 py-3 rounded-xl mb-6 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            {pwError}
          </div>
        )}

        {/* Password */}
        <Card className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Lock className="w-5 h-5 text-primary-600" />
            {t('settings.password')}
          </h2>
          {pwSuccess && (
            <div className="flex items-center gap-3 bg-green-50 text-green-700 px-4 py-3 rounded-xl mb-4 text-sm">
              <CheckCircle className="w-5 h-5 shrink-0" />
              {pwSuccess}
            </div>
          )}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('settings.currentPassword')}</label>
              <input
                type="password"
                value={pwData.current_password}
                onChange={(e) => setPwData({ ...pwData, current_password: e.target.value })}
                className="input-field"
                placeholder={t('settings.currentPasswordPlaceholder')}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('settings.newPassword')}</label>
              <input
                type="password"
                value={pwData.new_password}
                onChange={(e) => setPwData({ ...pwData, new_password: e.target.value })}
                className="input-field"
                placeholder={t('settings.newPasswordPlaceholder')}
                minLength={8}
              />
            </div>
            <div className="flex justify-end">
              <Button onClick={handleChangePassword} loading={pwSaving} disabled={!pwData.current_password || pwData.new_password.length < 8}>
                {t('settings.updatePassword')}
              </Button>
            </div>
          </div>
        </Card>

        {/* Language */}
        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('settings.language')}</h2>
          <div className="flex gap-3">
            <button
              onClick={() => setLang('en')}
              className={`px-6 py-3 rounded-xl font-medium text-sm border-2 transition-all ${
                lang === 'en'
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-200 text-gray-600 hover:border-gray-300'
              }`}
            >
              English
            </button>
            <button
              onClick={() => setLang('fr')}
              className={`px-6 py-3 rounded-xl font-medium text-sm border-2 transition-all ${
                lang === 'fr'
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-200 text-gray-600 hover:border-gray-300'
              }`}
            >
              Français
            </button>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  )
}
