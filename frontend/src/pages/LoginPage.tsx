import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api } from '../lib/api'
import { saveSession } from '../lib/session'
import type { Role } from '../types/api'

const ROLES: { role: Role; label: string; sublabel: string; icon: string; email: string }[] = [
  {
    role: 'customer',
    label: 'Customer',
    sublabel: 'ลูกค้าทั่วไป',
    icon: '👤',
    email: 'customer_demo@shopeasy.local',
  },
  {
    role: 'admin',
    label: 'Admin',
    sublabel: 'ทีมหลังบ้าน',
    icon: '🛡️',
    email: 'admin_demo@shopeasy.local',
  },
  {
    role: 'ai-engineer',
    label: 'AI Engineer',
    sublabel: 'ผู้ดูแลระบบ AI',
    icon: '🤖',
    email: 'ai_system_admin@shopeasy.local',
  },
]

const ROLE_ROUTES: Record<string, string> = {
  customer: '/customer',
  admin: '/admin',
  'ai-engineer': '/ai-control',
  ai_control: '/ai-control',
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

  const [isRegisterMode, setIsRegisterMode] = useState(false)
  const [fullName, setFullName] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const googleButtonRef = useRef<HTMLDivElement | null>(null)
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined

  useEffect(() => {
    if (!googleClientId || !window.google || !googleButtonRef.current) return
    window.google.accounts.id.initialize({
      client_id: googleClientId,
      callback: (response) => {
        void handleGoogleCallback(response.credential)
      },
      cancel_on_tap_outside: true,
    })
    window.google.accounts.id.renderButton(googleButtonRef.current, {
      type: 'standard',
      theme: 'outline',
      size: 'large',
      text: 'continue_with',
      shape: 'pill',
      width: googleButtonRef.current.offsetWidth || 340,
    })
  }, [googleClientId])

  async function handleGoogleCallback(credential: string) {
    setLoading(true)
    setError(null)
    try {
      const resp = await api.googleLogin({ credential })
      saveSession({
        user: resp.user,
        access_token: resp.access_token,
        customer_id: resp.customer_id,
      })
      navigate(ROLE_ROUTES[resp.user.role] ?? '/customer')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Google login failed')
    } finally {
      setLoading(false)
    }
  }

  function handleRoleSelect(nextRole: Role) {
    setRole(nextRole)

    const found = ROLES.find((item) => item.role === nextRole)

    if (found && !isRegisterMode) {
      setEmailValue(found.email)
    }

    setError(null)
  }

  async function handleLogin() {
    setLoading(true)
    setError(null)

    try {
      const resp = await api.login({
        email: emailValue,
        password: passwordValue,
      })

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

  async function handleRegister() {
    setLoading(true)
    setError(null)

    if (!fullName.trim()) {
      setError('Please enter your name')
      setLoading(false)
      return
    }

    if (!emailValue.trim()) {
      setError('Please enter your email')
      setLoading(false)
      return
    }

    if (passwordValue.length < 6) {
      setError('Password must be at least 6 characters')
      setLoading(false)
      return
    }

    if (passwordValue !== confirmPassword) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    try {
      /*
        ถ้า backend มี api.register ให้เปลี่ยนเป็นแบบนี้:

        await api.register({
          name: fullName,
          email: emailValue,
          password: passwordValue,
          role,
        })

        หลังสมัครสำเร็จค่อย login ต่อ
      */

      const resp = await api.login({
        email: emailValue,
        password: passwordValue,
      })

      saveSession({
        user: resp.user,
        access_token: resp.access_token,
        customer_id: resp.customer_id,
      })

      navigate(ROLE_ROUTES[role])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Register failed')
    } finally {
      setLoading(false)
    }
  }

  function toggleAuthMode() {
    setIsRegisterMode((current) => !current)
    setError(null)

    if (!isRegisterMode) {
      setFullName('')
      setConfirmPassword('')
      setEmailValue('')
      setPasswordValue('')
    } else {
      const found = ROLES.find((item) => item.role === role)

      setFullName('')
      setConfirmPassword('')
      setEmailValue(found?.email ?? 'customer_demo@shopeasy.local')
      setPasswordValue('demo1234')
    }
  }

  return (
    <main className="login-page login-page--split">
      <section className="login-hero-panel">
        <div className="login-hero-panel__content">
          <p className="login-hero-panel__eyebrow">
            {isRegisterMode ? 'Start with' : 'Welcome to'}
          </p>

          <h1>
            Shop<span>Easy</span>
          </h1>

          <strong>
            {isRegisterMode ? 'Create your smart support account' : 'Agentic Support Platform'}
          </strong>

          <p>
            {isRegisterMode
              ? 'สมัครใช้งานเพื่อเริ่มต้นระบบช่วยเหลืออัจฉริยะสำหรับ Marketplace'
              : 'Shopee-inspired Marketplace AI Ops'}
          </p>

          <div className="login-hero-panel__line" />

          <div className="login-hero-illustration">
            <div className="login-laptop">
              <div className="login-laptop__screen">
                <div className="login-laptop__topbar" />
                <div className="login-laptop__row login-laptop__row--one" />
                <div className="login-laptop__row login-laptop__row--two" />
                <div className="login-laptop__chart" />
              </div>

              <div className="login-laptop__base" />
            </div>

            <div className="login-floating-card login-floating-card--one">💬</div>
            <div className="login-floating-card login-floating-card--two">🛡️</div>
            <div className="login-floating-card login-floating-card--three">🤖</div>
            <div className="login-floating-card login-floating-card--four">📦</div>
          </div>
        </div>
      </section>

      <section className="login-form-panel">
        <div className="login-card login-card--split">
          {isRegisterMode && (
            <div className="form-group">
              <label htmlFor="fullName">Full name</label>

              <div className="form-group__input-wrapper">
                <input
                  id="fullName"
                  type="text"
                  placeholder="Enter your name"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                />

                <span className="form-group__icon">✓</span>
              </div>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email</label>

            <div className="form-group__input-wrapper">
              <input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={emailValue}
                onChange={(event) => setEmailValue(event.target.value)}
              />

              <span className="form-group__icon">✓</span>
            </div>
          </div>

          <div className="form-group">
            <div className="form-group__header">
              <label htmlFor="password">Password</label>

              {!isRegisterMode && (
                <a href="#" className="form-group__forgot">
                  Forgot password?
                </a>
              )}
            </div>

            <div className="form-group__input-wrapper">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter your password"
                value={passwordValue}
                onChange={(event) => setPasswordValue(event.target.value)}
              />

              <button
                type="button"
                className="form-group__icon form-group__icon--toggle"
                onClick={() => setShowPassword((current) => !current)}
              >
                {showPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
          </div>

          {isRegisterMode && (
            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm password</label>

              <div className="form-group__input-wrapper">
                <input
                  id="confirmPassword"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Confirm your password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                />

                <span className="form-group__icon">✓</span>
              </div>
            </div>
          )}

          <div className="role-selector">
            <label className="role-selector__label">
              {isRegisterMode ? 'Register as' : 'Login as'}
            </label>

            <div className="role-selector__grid">
              {ROLES.map(({ role: roleItem, label, sublabel, icon }) => (
                <button
                  key={roleItem}
                  type="button"
                  id={`role-${roleItem}`}
                  className={`role-card${role === roleItem ? ' is-selected' : ''}`}
                  onClick={() => handleRoleSelect(roleItem)}
                >
                  <div className="role-card__icon">{icon}</div>
                  <strong>{label}</strong>
                  <small>{sublabel}</small>
                </button>
              ))}
            </div>
          </div>

          <label className="checkbox-group">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(event) => setRememberMe(event.target.checked)}
            />

            <span>Remember me</span>
          </label>

          <button
            type="button"
            className="primary-button primary-button--wide"
            disabled={loading}
            onClick={isRegisterMode ? handleRegister : handleLogin}
          >
            {loading
              ? isRegisterMode
                ? 'Creating account…'
                : 'Signing in…'
              : isRegisterMode
                ? 'Create account →'
                : 'Sign in →'}
          </button>

          {error && (
            <p className="login-error-message">
              {error}
            </p>
          )}

          <div className="login-divider">
            <span>or continue with</span>
          </div>

          {googleClientId ? (
            <div ref={googleButtonRef} className="google-button-container" />
          ) : (
            <button type="button" className="google-button" disabled title="Google login is not configured">
              <span>G</span>
              Continue with Google
            </button>
          )}

          <div className="register-prompt-card">
            <div>
              <span>
                {isRegisterMode ? 'Already have an account?' : "Don't have an account?"}
              </span>

              <strong>
                {isRegisterMode ? 'Sign in' : 'Create an account'}
              </strong>

              <p>
                {isRegisterMode
                  ? 'กลับไปหน้าเข้าสู่ระบบ ShopEasy'
                  : 'สมัครใช้งานเพื่อเริ่มต้นใช้งาน ShopEasy'}
              </p>
            </div>

            <button type="button" onClick={toggleAuthMode}>
              ›
            </button>
          </div>

          <footer className="login-card__footer">
            <div className="login-card__footer-text">
              <span>Secure • Reliable • Intelligent</span>
              <span>© 2024 ShopEasy. All rights reserved.</span>
            </div>
          </footer>
        </div>
      </section>
    </main>
  )
}