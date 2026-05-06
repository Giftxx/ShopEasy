export function SectionHeader({ num, title, subtitle, caption }: { num: string; title: string; subtitle: string; caption: string }) {
  return (
    <div className="ai-section-header">
      <div className="ai-section-badge">{num}</div>
      <div>
        <h2 className="ai-section-title">{title}</h2>
        <p className="ai-section-subtitle">{subtitle}</p>
        <p className="ai-section-caption">{caption}</p>
      </div>
    </div>
  )
}
