import type { Role, User } from '../types/api'

export type SessionState = {
  role: Role
  label: string
  token: string
  user: User
  customer_id?: string | null
}

const SESSION_KEY = 'shopeasy-session'

export const roleLabels: Record<Role, string> = {
  customer: 'Customer',
  admin: 'Admin',
  'ai-engineer': 'AI Engineer',
}

// Map DB role value → frontend Role type
export function dbRoleToFrontend(dbRole: string): Role {
  if (dbRole === 'admin') return 'admin'
  if (dbRole === 'ai_control') return 'ai-engineer'
  return 'customer'
}

export function saveSession(params: {
  user: User
  access_token: string
  customer_id?: string | null
}): SessionState {
  const role = dbRoleToFrontend(params.user.role)
  const session: SessionState = {
    role,
    label: roleLabels[role],
    token: params.access_token,
    user: params.user,
    customer_id: params.customer_id,
  }
  localStorage.setItem(SESSION_KEY, JSON.stringify(session))
  return session
}

export function readSession(): SessionState | null {
  const raw = localStorage.getItem(SESSION_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as SessionState
  } catch {
    return null
  }
}

export function clearSession() {
  localStorage.removeItem(SESSION_KEY)
}
