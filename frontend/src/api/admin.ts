import api from './client'

export interface AdminUser {
  id: string
  email: string
  full_name: string
  company: string | null
  is_active: number
  is_admin: number
  created_at: string
  audit_count: number
}

export interface AdminAudit {
  id: string
  user_id: string
  user_email: string
  name: string
  status: string
  docker_status: string
  vulnerabilities_critical: number
  vulnerabilities_high: number
  vulnerabilities_medium: number
  vulnerabilities_low: number
  total_vulnerabilities: number
  created_at: string
  completed_at: string | null
  duration_seconds: number | null
  error_message: string | null
}

export interface AdminDashboard {
  total_users: number
  total_audits: number
  audits_by_status: Record<string, number>
  audits_by_day: { day: string; count: number }[]
  recent_audits: AdminAudit[]
  recent_users: AdminUser[]
}

export interface PaginatedResult {
  items: any[]
  total: number
  page: number
  size: number
}

export async function getAdminDashboard(): Promise<AdminDashboard> {
  const { data } = await api.get('/admin/dashboard')
  return data
}

export async function getAdminUsers(page = 1, size = 20, q = ''): Promise<PaginatedResult> {
  const { data } = await api.get('/admin/users', { params: { page, size, q } })
  return data
}

export async function getAdminUser(id: string): Promise<{ user: AdminUser; audits: AdminAudit[] }> {
  const { data } = await api.get(`/admin/users/${id}`)
  return data
}

export async function patchAdminUser(id: string, body: { is_active?: number; is_admin?: number }): Promise<AdminUser> {
  const { data } = await api.patch(`/admin/users/${id}`, null, { params: body })
  return data
}

export async function getAdminAudits(page = 1, size = 20, status = '', userId = ''): Promise<PaginatedResult> {
  const { data } = await api.get('/admin/audits', { params: { page, size, status, user_id: userId } })
  return data
}

export async function getAdminAudit(id: string): Promise<{ audit: AdminAudit; report_markdown: string | null; error_message: string | null }> {
  const { data } = await api.get(`/admin/audits/${id}`)
  return data
}

export async function getAdminAuditLog(id: string): Promise<{ log: string }> {
  const { data } = await api.get(`/admin/audits/${id}/log`)
  return data
}

export async function retryAdminAudit(id: string): Promise<{ status: string; audit_id: string }> {
  const { data } = await api.post(`/admin/audits/${id}/retry`)
  return data
}
