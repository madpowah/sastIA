import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Shield, Eye, EyeOff, AlertCircle } from 'lucide-react'
import { Button } from '../components/ui/Button'

import { useLanguage } from '../i18n/LanguageContext'

export default function Register() {
  const { t } = useLanguage()
  const { register } = useAuth()
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    company: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    if (formData.password.length < 8) {
      setError(t('auth.passwordMin'))
      return
    }
    setLoading(true)
    try {
      await register(formData)
      navigate('/dashboard')
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
          <Link to="/" className="inline-flex items-center gap-3 mb-6">
            <Shield className="w-10 h-10 text-primary-600" />
            <span className="text-2xl font-bold gradient-text">SAST IA</span>
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">{t('auth.registerTitle')}</h1>
          <p className="text-gray-500 mt-2">{t('auth.registerSubtitle')}</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
          {error && (
            <div className="flex items-center gap-3 bg-red-50 text-red-700 px-4 py-3 rounded-xl mb-6 text-sm">
              <AlertCircle className="w-5 h-5 shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('auth.fullName')}</label>
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="input-field"
                    placeholder="Jean Dupont"
                    required
                  />
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('auth.email')}</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="input-field"
                    placeholder={t('auth.emailPlaceholder')}
                    required
                  />
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('auth.company')}</label>
                  <input
                    type="text"
                    value={formData.company}
                    onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                    className="input-field"
                    placeholder={t('auth.companyPlaceholder')}
                  />
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('auth.password')}</label>
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="input-field pr-12"
                      placeholder={t('auth.passwordPlaceholder')}
                      required
                      minLength={8}
                    />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="input-field"
                placeholder="vous@entreprise.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Entreprise</label>
              <input
                type="text"
                value={formData.company}
                onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                className="input-field"
                placeholder="Ma Société SAS (optionnel)"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Mot de passe</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="input-field pr-12"
                  placeholder="Minimum 8 caractères"
                  required
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <Button type="submit" loading={loading} className="w-full" size="lg">
              {t('auth.register')}
            </Button>

          <p className="text-center text-sm text-gray-500 mt-6">
            {t('auth.hasAccount')}{' '}
            <Link to="/login" className="text-primary-600 font-medium hover:text-primary-700">
              {t('auth.loginLink')}
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
