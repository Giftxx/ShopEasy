import type { ReactNode } from 'react'

export function SvgIcon({ path, viewBox = '0 0 24 24' }: { path: ReactNode; viewBox?: string }) {
  return (
    <svg viewBox={viewBox} aria-hidden="true" className="ai-svg-icon">
      {path}
    </svg>
  )
}
