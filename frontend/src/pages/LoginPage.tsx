import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api } from '../lib/api'
import { saveSession } from '../lib/session'
import type { Role } from '../types/api'

const ROLES: { role: Role; label: string; sublabel: string; icon: string; email: string }[] = [
  { role: 'customer',    label: 'Customer',    sublabel: 'ลูกค้าทั่วไป',   icon: '🧑‍💼', email: 'customer_demo@shopeasy.local' },
  { role: 'admin',       label: 'Admin',       sublabel: 'ทีมหลังบ้าน',    icon: '🛡️',  email: 'admin_demo@shopeasy.local' },
  { role: 'ai-engineer', label: 'AI Engineer', sublabel: 'ผู้ดูแลระบบ AI', icon: '🤖',  email: 'ai_system_admin@shopeasy.local' },
]

const ROLE_ROUTES: Record<Role, string> = {
  customer: '/customer',
  admin: '/admin',
  'ai-engineer': '/ai-control',
}

export function LoginPage() {
  const navigate = useNavigate()
  const [role, setRole] = useState<Role>('customer')
  const [rememberMe, setRememberMe] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [emailValue, setEmailValue] = useState('customer_demo@shopeasy.local')
  const [passwordValue, setPasswordValue] = useState('demo1234')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function handleRoleSelect(r: Role) {
    setRole(r)
    const found = ROLES.find((x) => x.role === r)
    if (found) setEmailValue(found.email)
    setError(null)
  }

  async function handleLogin() {
    setLoading(true)
    setError(null)
    try {
      const resp = await api.login({ email: emailValue, password: passwordValue })
      saveSession({
        user: resp.user,
        access_token: resp.access_token,
        customer_id: resp.customer_id,
      })
      navigate(ROLE_ROUTES[role])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="login-page">
      <div className="login-card">
        <div className="login-card__header">
          <div className="login-card__logo-box">
            <div className="login-card__logo-icon">S</div>
            <div className="login-card__logo-text">
              <span className="login-card__logo-shop">Shop</span>
              <span className="login-card__logo-easy">Easy</span>
            </div>
          </div>
          <div className="login-card__tagline">Agentic Support Platform</div>
          <div className="login-card__description">Shopee-inspired Marketplace AI Ops</div>
        </div>

        <div className="form-group">
          <label htmlFor="email">Email</label>
          <div className="form-group__input-wrapper">
            <input 
              id="email" 
              type="email" 
              placeholder="you@example.com" 
              value={emailValue}
              onChange={(e) => setEmailValue(e.target.value)}
            />
            <span className="form-group__icon">✓</span>
          </div>
        </div>

        <div className="form-group">
          <div className="form-group__header">
            <label htmlFor="password">Password</label>
            <a href="#" className="form-group__forgot">Forgot password?</a>
          </div>
          <div className="form-group__input-wrapper">
            <input 
              id="password" 
              type={showPassword ? 'text' : 'password'} 
              placeholder="Enter your password" 
              value={passwordValue}
              onChange={(e) => setPasswordValue(e.target.value)}
            />
            <button 
              type="button" 
              className="form-group__icon form-group__icon--toggle"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? '👁️' : '👁️‍🗨️'}
            </button>
          </div>
        </div>

        {/* Role Selector */}
        <div className="role-selector">
          <label className="role-selector__label">Login as</label>
          <div className="role-selector__grid">
            {ROLES.map(({ role: r, label, sublabel, icon }) => (
              <button
                key={r}
                type="button"
                id={`role-${r}`}
                className={`role-card${role === r ? ' is-selected' : ''}`}
                onClick={() => handleRoleSelect(r)}
              >
                <div className="role-card__icon">{icon}</div>
                <strong>{label}</strong>
                <small>{sublabel}</small>
              </button>
            ))}
          </div>
        </div>

        <label className="checkbox-group">
          <input type="checkbox" checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} />
          <span>Remember me</span>
        </label>

        <button
          type="button"
          className="primary-button primary-button--wide"
          disabled={loading}
          onClick={handleLogin}
        >
          {loading ? 'Signing in…' : 'Sign in →'}
        </button>

        {error && (
          <p style={{ color: 'var(--color-danger, #ef4444)', marginTop: '0.5rem', fontSize: '0.875rem' }}>
            {error}
          </p>
        )}

        <footer className="login-card__footer">
          <div className="login-card__footer-badge">
            🛡️
          </div>
          <div className="login-card__footer-text">
            <span>Secure • Reliable • Intelligent</span>
            <span>© 2024 ShopEasy. All rights reserved.</span>
          </div>
        </footer>
      </div>
    </main>
  )
}
