export function InfoPanel({ main, features }: { main: string[]; features: string[] }) {
  return (
    <div className="ai-info-panel ai-control-surface ai-control-surface--inner">
      <div>
        <strong className="ai-info-label">หน้าที่หลัก</strong>
        <ul className="ai-info-list">{main.map((item) => <li key={item}>{item}</li>)}</ul>
      </div>
      <div>
        <strong className="ai-info-label">Key Features</strong>
        <ul className="ai-info-list">{features.map((item) => <li key={item}>{item}</li>)}</ul>
      </div>
    </div>
  )
}
