export function DonutChart({ segments, r = 60 }: { segments: { pct: number; color: string }[]; r?: number }) {
  const circ = 2 * Math.PI * r
  let offset = 0
  const arcs = segments.map(({ pct, color }) => {
    const stroke = (pct / 100) * circ
    const arc = { stroke, offset: -offset, color }
    offset += stroke
    return arc
  })

  return (
    <svg width={r * 2 + 20} height={r * 2 + 20} viewBox={`0 0 ${r * 2 + 20} ${r * 2 + 20}`}>
      <circle cx={r + 10} cy={r + 10} r={r} fill="none" stroke="#f3f4f6" strokeWidth="18" />
      {arcs.map((arc, i) => (
        <circle
          key={i}
          cx={r + 10}
          cy={r + 10}
          r={r}
          fill="none"
          stroke={arc.color}
          strokeWidth="18"
          strokeDasharray={`${arc.stroke} ${circ}`}
          strokeDashoffset={arc.offset}
          transform={`rotate(-90 ${r + 10} ${r + 10})`}
        />
      ))}
    </svg>
  )
}
