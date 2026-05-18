import api from './client'

export interface ModelInfo {
  id: string
  name: string
  provider: string
  built_in: boolean
}

export interface ProviderGroup {
  provider: string
  name: string
  models: ModelInfo[]
}

export interface ProviderInfo {
  id: string
  name: string
  base_url: string
  api_key: string | null
  models_json: string | null
  created_at: string
}

export async function getProviderGroups(): Promise<ProviderGroup[]> {
  const { data } = await api.get('/providers/groups')
  return data
}

export async function getAvailableModels(): Promise<ModelInfo[]> {
  const { data } = await api.get('/providers/models')
  return data
}

export async function getProviders(): Promise<ProviderInfo[]> {
  const { data } = await api.get('/providers/')
  return data
}

export async function createProvider(params: {
  name: string
  base_url: string
  api_key?: string
}): Promise<ProviderInfo> {
  const { data } = await api.post('/providers/', params)
  return data
}

export async function deleteProvider(id: string): Promise<void> {
  await api.delete(`/providers/${id}`)
}

export async function fetchProviderModels(id: string): Promise<ModelInfo[]> {
  const { data } = await api.post(`/providers/${id}/fetch-models`)
  return data
}
