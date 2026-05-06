type StatCardProps = {
  label: string
  value: string
  hint: string
  tone?: 'neutral' | 'success' | 'warning' | 'danger'
}

export function StatCard({ label, value, hint, tone = 'neutral' }: StatCardProps) {
  return (
    <article className={`stat-card stat-card--${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{hint}</small>
    </article>
  )
}
