import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

import { clearSession } from '../lib/session'

type PortalShellProps = {
  badge: string
  heading: string
  caption: string
  children: ReactNode
  variant?: 'default' | 'compact' | 'ai-control'
  hideHeader?: boolean
}

export function PortalShell({ badge, heading, caption, children, variant = 'default', hideHeader = false }: PortalShellProps) {
  const navigate = useNavigate()

  return (
    <div className={`portal-shell portal-shell--${variant}`}>
      {!hideHeader ? (
        <header className="portal-shell__header">
          <div className="portal-shell__intro">
            <span className="portal-shell__badge">{badge}</span>
            <h1>{heading}</h1>
            <p>{caption}</p>
          </div>
          <button
            type="button"
            className="ghost-button portal-shell__logout"
            onClick={() => {
              clearSession()
              navigate('/')
            }}
          >
            Logout
          </button>
        </header>
      ) : null}
      {children}
    </div>
  )
}
