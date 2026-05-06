import { SvgIcon } from '../components/SvgIcon'
import { SectionHeader } from '../components/SectionHeader'

const AGENTS = [
  { name: 'Router Agent', color: '#4f86ff' },
  { name: 'Order Agent', color: '#4ed4a0' },
  { name: 'Shipping Agent', color: '#f0b847' },
  { name: 'Policy Agent', color: '#ff7ac9' },
  { name: 'Refund Agent', color: '#ff6fc2' },
  { name: 'Risk Agent', color: '#ff6256' },
  { name: 'Supervisor Agent', color: '#ff9846' },
  { name: 'Support Agent', color: '#5bd4cb' },
]

export function WorkspaceTab() {
  return (
    <div className="ai-control-workspace">
      <div className="ai-control-workspace__header">
        <SectionHeader
          num="1"
          title="Multi-Agent Workspace"
          subtitle="ออกแบบและจัดการ Multi-Agent"
          caption="สร้าง, แก้ไข และจัดการ Agent, ความสามารถ, เครื่องมือ และ Flow การทำงาน"
        />
      </div>

      <div className="ai-workspace-grid">
        <div className="ai-agent-list-panel ai-control-surface ai-control-surface--inner">
          <strong className="ai-panel-label">Agents</strong>
          {AGENTS.map((agent) => (
            <div key={agent.name} className="ai-agent-item">
              <span className="ai-agent-dot" style={{ background: agent.color }} />
              {agent.name}
            </div>
          ))}
          <button type="button" className="ai-link-button">+ Add Agent</button>
        </div>

        <div className="ai-flow-panel ai-control-surface ai-control-surface--inner">
          <div className="ai-flow-topbar">
            <div className="ai-flow-label">Agent Flow (LangGraph)</div>
            <div className="ai-flow-controls">
              <div className="ai-zoom-group">
                <button type="button">-</button>
                <span>100%</span>
                <button type="button">+</button>
              </div>
              <button type="button" className="ai-icon-button" aria-label="Expand">
                <SvgIcon path={<path d="M8 4H4v4M16 4h4v4M20 16v4h-4M8 20H4v-4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />} />
              </button>
              <button type="button" className="ai-secondary-button ai-secondary-button--compact">Edit Flow</button>
            </div>
          </div>

          <svg viewBox="0 0 840 440" className="ai-flow-svg">
            <defs>
              <marker id="arr" markerWidth="12" markerHeight="12" refX="6" refY="6" orient="auto">
                <path d="M0,0 L0,12 L12,6 z" fill="#9ca3af" />
              </marker>
            </defs>
            <line x1="180" y1="90" x2="260" y2="90" stroke="#aeb8c8" strokeWidth="3" markerEnd="url(#arr)" />
            <rect x="60" y="60" width="120" height="56" rx="12" fill="#f7fbff" stroke="#5a8dff" strokeWidth="2.8" />
            <text x="120" y="95" textAnchor="middle" fontSize="17.2" fontWeight="600" fill="#183153">Router</text>
            <rect x="260" y="60" width="148" height="56" rx="12" fill="#f0fff8" stroke="#54d1a4" strokeWidth="2.8" />
            <text x="334" y="95" textAnchor="middle" fontSize="16.8" fontWeight="600" fill="#183153">Order Agent</text>
            <line x1="408" y1="90" x2="480" y2="90" stroke="#aeb8c8" strokeWidth="3" markerEnd="url(#arr)" />
            <rect x="480" y="60" width="164" height="56" rx="12" fill="#fffaf0" stroke="#f0b847" strokeWidth="2.8" />
            <text x="562" y="95" textAnchor="middle" fontSize="16.4" fontWeight="600" fill="#183153">Shipping Agent</text>

            <line x1="120" y1="116" x2="120" y2="216" stroke="#aeb8c8" strokeWidth="3" />
            <line x1="120" y1="216" x2="260" y2="216" stroke="#aeb8c8" strokeWidth="3" markerEnd="url(#arr)" />
            <rect x="260" y="188" width="148" height="56" rx="12" fill="#fff5fb" stroke="#ff7bc7" strokeWidth="2.8" />
            <text x="334" y="223" textAnchor="middle" fontSize="16.8" fontWeight="600" fill="#183153">Policy Agent</text>
            <line x1="408" y1="216" x2="480" y2="216" stroke="#aeb8c8" strokeWidth="3" markerEnd="url(#arr)" />
            <rect x="480" y="188" width="164" height="56" rx="12" fill="#fff4fb" stroke="#ff68c0" strokeWidth="2.8" />
            <text x="562" y="223" textAnchor="middle" fontSize="16.4" fontWeight="600" fill="#183153">Refund Agent</text>

            <rect x="60" y="316" width="120" height="56" rx="12" fill="#fff7f7" stroke="#ff6a60" strokeWidth="2.8" />
            <text x="120" y="351" textAnchor="middle" fontSize="16.8" fontWeight="600" fill="#183153">Risk Agent</text>
            <line x1="180" y1="344" x2="260" y2="344" stroke="#aeb8c8" strokeWidth="3" markerEnd="url(#arr)" />
            <rect x="260" y="316" width="148" height="56" rx="12" fill="#fff7ef" stroke="#ff9a46" strokeWidth="2.8" />
            <text x="334" y="351" textAnchor="middle" fontSize="15.8" fontWeight="600" fill="#183153">Supervisor Agent</text>
            <line x1="408" y1="344" x2="480" y2="344" stroke="#aeb8c8" strokeWidth="3" markerEnd="url(#arr)" />
            <rect x="480" y="316" width="164" height="56" rx="12" fill="#f0fffd" stroke="#59d6ce" strokeWidth="2.8" />
            <text x="562" y="351" textAnchor="middle" fontSize="16.4" fontWeight="600" fill="#183153">Support Agent</text>
          </svg>

          <div className="ai-flow-actions">
            <button type="button" className="ai-link-chip">
              <SvgIcon path={<path d="M8 5v14l11-7z" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />} />
              Test Flow
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
