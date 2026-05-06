import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { saveSession } from '../lib/session'
import type { Role } from '../types/api'

const ROLES: { role: Role; label: string; sublabel: string; icon: string }[] = [
  { role: 'customer',     label: 'Customer',    sublabel: 'ลูกค้าทั่วไป',   icon: '🧑‍💼' },
  { role: 'admin',        label: 'Admin',       sublabel: 'ทีมหลังบ้าน',    icon: '🛡️' },
  { role: 'ai-engineer',  label: 'AI Engineer', sublabel: 'ผู้ดูแลระบบ AI', icon: '🤖' },
]

export function LoginPage() {
  const navigate = useNavigate()
  const [role, setRole] = useState<Role>('customer')
  const [rememberMe, setRememberMe] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [emailValue, setEmailValue] = useState('demo@shopeasy.local')
  const [passwordValue, setPasswordValue] = useState('demo1234')

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
                onClick={() => setRole(r)}
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
          onClick={() => {
            saveSession(role)
            navigate(role === 'customer' ? '/customer' : role === 'admin' ? '/admin' : '/ai-control')
          }}
        >
          Sign in →
        </button>

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
