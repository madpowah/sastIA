import { useState, useEffect } from 'react'
import { DashboardLayout } from '../components/Layout'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import {
  getProviders,
  createProvider,
  deleteProvider,
  fetchProviderModels,
  getProviderGroups,
  ProviderGroup,
  ModelInfo,
  ProviderInfo,
} from '../api/providers'
import {
  Plus,
  Trash2,
  RefreshCw,
  Globe,
  Key,
  Server,
  CheckCircle,
  AlertCircle,
  Cpu,
} from 'lucide-react'

export default function Settings() {
  const [groups, setGroups] = useState<ProviderGroup[]>([])
  const [customProviders, setCustomProviders] = useState<ProviderInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({ name: '', base_url: '', api_key: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [fetchingId, setFetchingId] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    try {
      const [g, provs] = await Promise.all([getProviderGroups(), getProviders()])
      setGroups(g)
      setCustomProviders(provs)
    } catch {
      setError('Erreur lors du chargement')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleAdd = async () => {
    if (!formData.name || !formData.base_url) return
    setSaving(true)
    setError('')
    try {
      await createProvider(formData)
      setFormData({ name: '', base_url: '', api_key: '' })
      setShowForm(false)
      await load()
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erreur lors de l'ajout")
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteProvider(id)
      await load()
    } catch {
      setError('Erreur lors de la suppression')
    }
  }

  const handleFetch = async (id: string) => {
    setFetchingId(id)
    setError('')
    try {
      await fetchProviderModels(id)
      await load()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la récupération des modèles')
    } finally {
      setFetchingId(null)
    }
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Paramètres</h1>
          <p className="text-gray-500 mt-1">Gérez vos providers et modèles d'IA</p>
        </div>

        {error && (
          <div className="flex items-center gap-3 bg-red-50 text-red-700 px-4 py-3 rounded-xl mb-6 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            {error}
          </div>
        )}

        {/* Providers and models */}
        <Card className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-primary-600" />
            Providers et modèles disponibles
          </h2>
          {loading ? (
            <p className="text-gray-400 text-sm">Chargement...</p>
          ) : groups.length === 0 ? (
            <p className="text-gray-400 text-sm">Aucun provider trouvé</p>
          ) : (
            <div className="space-y-4">
              {groups.map((g) => (
                <div key={g.provider} className="border border-gray-100 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <p className="font-semibold text-gray-900">{g.name}</p>
                      <p className="text-xs text-gray-400 font-mono">{g.provider}</p>
                    </div>
                  </div>
                  {g.models.length === 0 ? (
                    <p className="text-xs text-gray-400">Aucun modèle</p>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {g.models.map((m) => (
                        <span key={m.id} className="text-xs bg-primary-50 text-primary-700 px-2 py-0.5 rounded font-mono">
                          {m.id}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Custom providers */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Server className="w-5 h-5 text-primary-600" />
              Providers personnalisés
            </h2>
            <Button size="sm" onClick={() => setShowForm(!showForm)} icon={<Plus className="w-4 h-4" />}>
              Ajouter
            </Button>
          </div>

          {showForm && (
            <div className="bg-gray-50 rounded-xl p-4 mb-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nom du provider</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input-field"
                  placeholder="ex: OpenAI, Anthropic, Groq"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Globe className="w-4 h-4 inline mr-1" />
                  URL de base
                </label>
                <input
                  type="url"
                  value={formData.base_url}
                  onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                  className="input-field"
                  placeholder="ex: https://api.openai.com/v1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Key className="w-4 h-4 inline mr-1" />
                  Clé API
                </label>
                <input
                  type="password"
                  value={formData.api_key}
                  onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                  className="input-field"
                  placeholder="sk-..."
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" size="sm" onClick={() => setShowForm(false)}>Annuler</Button>
                <Button size="sm" onClick={handleAdd} loading={saving}>Ajouter</Button>
              </div>
            </div>
          )}

          {loading ? (
            <p className="text-gray-400 text-sm">Chargement...</p>
          ) : customProviders.length === 0 ? (
            <p className="text-gray-400 text-sm">Aucun provider personnalisé</p>
          ) : (
            <div className="space-y-3">
              {customProviders.map((p) => {
                const models: { id: string; name: string }[] = []
                if (p.models_json) {
                  try { models.push(...JSON.parse(p.models_json)) } catch {}
                }
                return (
                  <div key={p.id} className="border border-gray-200 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <p className="font-medium text-gray-900">{p.name}</p>
                        <p className="text-xs text-gray-400">{p.base_url}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleFetch(p.id)}
                          loading={fetchingId === p.id}
                          icon={<RefreshCw className="w-3 h-3" />}
                        >
                          Modèles
                        </Button>
                        <button
                          onClick={() => handleDelete(p.id)}
                          className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    {models.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {models.map((m) => (
                          <span key={m.id} className="text-xs bg-primary-50 text-primary-700 px-2 py-0.5 rounded font-mono">
                            {p.name}/{m.id}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </Card>
      </div>
    </DashboardLayout>
  )
}
