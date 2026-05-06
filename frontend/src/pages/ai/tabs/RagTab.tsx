import { Surface } from '../../../components/Surface'
import { SectionHeader } from '../components/SectionHeader'

const POLICIES = [
  { name: 'Shipping Policy', category: 'Shipping', version: 'v3.2', color: '#10b981' },
  { name: 'Refund Policy', category: 'Refund', version: 'v4.1', color: '#3b82f6' },
  { name: 'Return Policy', category: 'Return', version: 'v2.0', color: '#3b82f6' },
  { name: 'Compensation Policy', category: 'Compensation', version: 'v1.5', color: '#3b82f6' },
  { name: 'Seller SLA Policy', category: 'Seller', version: 'v2.3', color: '#3b82f6' },
  { name: 'Address Change Policy', category: 'Order', version: 'v1.2', color: '#3b82f6' },
  { name: 'Escalation SOP', category: 'Process', version: 'v1.0', color: '#3b82f6' },
  { name: 'Fraud Review Policy', category: 'Fraud', version: 'v1.3', color: '#3b82f6' },
  { name: 'FAQ / Help Articles', category: 'FAQ', version: 'v2.8', color: '#3b82f6' },
]

export function RagTab() {
  return (
    <div className="ai-section ai-tab-shell">
      <SectionHeader
        num="3"
        title="Policies / RAG"
        subtitle="จัดการนโยบายและความรู้"
        caption="จัดการเอกสารนโยบาย, FAQ และองค์ความรู้สำหรับ RAG"
      />
      <Surface title="Policy Documents" rightSlot={<button type="button" className="ai-secondary-button ai-secondary-button--compact">New Policy</button>}>
        <div className="ai-policy-table">
          {POLICIES.map((policy) => (
            <div key={policy.name} className="ai-policy-row">
              <span className="ai-policy-icon" style={{ background: `${policy.color}22`, color: policy.color }}>P</span>
              <span className="ai-policy-name">{policy.name}</span>
              <span className="ai-policy-cat">{policy.category}</span>
              <span className="ai-policy-ver">{policy.version}</span>
            </div>
          ))}
        </div>
        <div className="ai-action-row">
          <button type="button" className="primary-button">+ Upload Document</button>
          <button type="button" className="ghost-button">Re-index All</button>
        </div>
      </Surface>
    </div>
  )
}
