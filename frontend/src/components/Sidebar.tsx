import type { ReactNode } from 'react'

type NavItem = {
  key: string
  label: string
  icon: ReactNode
}

type SidebarProps = {
  title: string
  subtitle: string
  accent: string
  items: NavItem[]
  activeKey: string
  onSelect: (key: string) => void
  footer?: ReactNode
  className?: string
}

export function Sidebar({ title, subtitle, accent, items, activeKey, onSelect, footer, className }: SidebarProps) {
  return (
    <aside className={`sidebar${className ? ` ${className}` : ''}`}>
      <div className="sidebar__brand">
        <div className="sidebar__logo" style={{ background: accent }}>
          S
        </div>
        <div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
      </div>

      <nav className="sidebar__nav">
        {items.map((item) => (
          <button
            key={item.key}
            type="button"
            className={`sidebar__item ${activeKey === item.key ? 'is-active' : ''}`}
            onClick={() => onSelect(item.key)}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      {footer ? <div className="sidebar__footer">{footer}</div> : null}
    </aside>
  )
}
