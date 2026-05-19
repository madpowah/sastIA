import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api from '../api/client'
import { Shield, AlertCircle, CheckCircle } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { useLanguage } from '../i18n/LanguageContext'

export default function ChangePassword() {
  const { t } = useLanguage()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const force = params.get('force') === '1'
  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    if (newPw.length < 8) { setError(t('auth.passwordMin')); return }
    if (newPw !== confirmPw) { setError(t('auth.passwordsNoMatch')); return }
    setLoading(true)
    try {
      await api.post('/auth/change-password', { current_password: currentPw, new_password: newPw })
      setSuccess(t('settings.passwordChanged'))
      setTimeout(() => navigate('/dashboard'), 1500)
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.error'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-white to-teal-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Shield className="w-10 h-10 text-primary-600 mx-auto mb-3" />
          <h1 className="text-3xl font-bold text-gray-900">{t('settings.password')}</h1>
          <p className="text-gray-500 mt-2">
            {force ? t('auth.forceChangePassword') : t('settings.password')}
          </p>
        </div>
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
          {error && (
            <div className="flex items-center gap-3 bg-red-50 text-red-700 px-4 py-3 rounded-xl mb-4 text-sm">
              <AlertCircle className="w-5 h-5 shrink-0" />
              {error}
            </div>
          )}
          {success && (
            <div className="flex items-center gap-3 bg-green-50 text-green-700 px-4 py-3 rounded-xl mb-4 text-sm">
              <CheckCircle className="w-5 h-5 shrink-0" />
              {success}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('settings.currentPassword')}</label>
              <input type="password" value={currentPw} onChange={(e) => setCurrentPw(e.target.value)}
                className="input-field" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('settings.newPassword')}</label>
              <input type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)}
                className="input-field" minLength={8} required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('auth.confirmPassword')}</label>
              <input type="password" value={confirmPw} onChange={(e) => setConfirmPw(e.target.value)}
                className="input-field" minLength={8} required />
            </div>
            <Button type="submit" loading={loading} className="w-full" size="lg">
              {t('settings.updatePassword')}
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
