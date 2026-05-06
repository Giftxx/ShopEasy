import type { Role } from '../types/api'

export type SessionState = {
  role: Role
  label: string
}

const SESSION_KEY = 'shopeasy-session'

export const roleLabels: Record<Role, string> = {
  customer: 'Customer',
  admin: 'Admin',
  'ai-engineer': 'AI Engineer',
}

export function saveSession(role: Role) {
  const session: SessionState = { role, label: roleLabels[role] }
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
