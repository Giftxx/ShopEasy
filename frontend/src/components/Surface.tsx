import type { ReactNode } from 'react'

type SurfaceProps = {
  title: string
  subtitle?: string
  rightSlot?: ReactNode
  children: ReactNode
}

export function Surface({ title, subtitle, rightSlot, children }: SurfaceProps) {
  return (
    <section className="surface">
      <header className="surface__header">
        <div>
          <h3>{title}</h3>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
        {rightSlot}
      </header>
      <div className="surface__body">{children}</div>
    </section>
  )
}
