import { useEffect, useState } from 'react'

import { PortalShell } from '../../components/PortalShell'
import { Sidebar } from '../../components/Sidebar'
import { StatCard } from '../../components/StatCard'
import { Surface } from '../../components/Surface'
import { api } from '../../lib/api'
import { readSession } from '../../lib/session'
import type { Approval, CaseDetail, CaseSummary, ProactiveAlert, RefundRequest } from '../../types/api'

const navItems = [
  { key: 'dashboard', label: 'Dashboard', icon: '📊' },
  { key: 'cases', label: 'Cases', icon: '🗂' },
  { key: 'approvals', label: 'Approvals', icon: '✅' },
  { key: 'refunds', label: 'Refund / Return', icon: '♻️' },
  { key: 'alerts', label: 'Proactive Alerts', icon: '📍' },
]

export function AdminPortal() {
  const session = readSession()
  const userName = session?.user?.name ?? 'Admin'

  const [activeTab, setActiveTab] = useState('dashboard')
  const [cases, setCases] = useState<CaseSummary[]>([])
  const [approvals, setApprovals] = useState<Approval[]>([])
  const [refunds, setRefunds] = useState<RefundRequest[]>([])
  const [alerts, setAlerts] = useState<ProactiveAlert[]>([])
  const [message, setMessage] = useState<string | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [selectedCase, setSelectedCase] = useState<CaseDetail | null>(null)
  const [caseDetailLoading, setCaseDetailLoading] = useState(false)
  const [openingAttachmentId, setOpeningAttachmentId] = useState<string | null>(null)

  function showMessage(msg: string) {
    setMessage(msg)
    setTimeout(() => setMessage(null), 4000)
  }

  async function load() {
    setLoadError(null)
    try {
      const [casesData, approvalsData, refundsData, alertsData] = await Promise.all([
        api.getCases(),
        api.getApprovals(),
        api.getRefundRequests(),
        api.getProactiveAlerts(),
      ])
      setCases(casesData)
      setApprovals(approvalsData)
      setRefunds(refundsData)
      setAlerts(alertsData)
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Load failed')
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function loadCaseDetail(caseId: string) {
    setCaseDetailLoading(true)
    try {
      const detail = await api.getCaseDetail(caseId)
      setSelectedCase(detail)
      setActiveTab('cases')
    } finally {
      setCaseDetailLoading(false)
    }
  }

  async function handleApprovalAction(type: 'approve' | 'reject', approvalId: string) {
    try {
      if (type === 'approve') {
        await api.approveApproval(approvalId, 'Approved from admin portal.')
        showMessage(`Approved ${approvalId}`)
      } else {
        await api.rejectApproval(approvalId, 'Rejected from admin portal.')
        showMessage(`Rejected ${approvalId}`)
      }
      await load()
    } catch (err) {
      showMessage(err instanceof Error ? err.message : 'Action failed')
    }
  }

  async function handleCloseCase(caseId: string) {
    try {
      await api.closeCase(caseId, 'Closed from admin portal.')
      showMessage(`Closed ${caseId}`)
      await load()
      if (selectedCase?.id === caseId) {
        await loadCaseDetail(caseId)
      }
    } catch (err) {
      showMessage(err instanceof Error ? err.message : 'Close failed')
    }
  }

  async function handleResolveAlert(alertId: string) {
    try {
      await api.resolveAlert(alertId, 'Resolved from admin portal.')
      showMessage(`Resolved ${alertId}`)
      await load()
    } catch (err) {
      showMessage(err instanceof Error ? err.message : 'Resolve failed')
    }
  }

  async function openAttachment(attachmentId: string) {
    setOpeningAttachmentId(attachmentId)
    try {
      const presign = await api.getAttachmentDownloadUrl(attachmentId)
      window.open(presign.upload_url, '_blank', 'noopener,noreferrer')
    } finally {
      setOpeningAttachmentId(null)
    }
  }

  return (
    <PortalShell
      badge="Admin Portal"
      heading="ShopEasy Operations Console"
      caption="ภาพรวมเคส อนุมัติ และงาน proactive สำหรับทีมหลังบ้าน"
    >
      <div className="portal-layout">
        <Sidebar
          title="ShopEasy"
          subtitle="Admin Console"
          accent="linear-gradient(135deg, #365eff, #6b4dff)"
          items={navItems}
          activeKey={activeTab}
          onSelect={setActiveTab}
          footer={
            <div className="sidebar-profile">
              <strong>{userName}</strong>
              <span>{session?.user?.email ?? 'admin'}</span>
            </div>
          }
        />

        <div className="portal-main">
          {/* Stats bar — always visible */}
          <div className="stats-grid">
            <StatCard label="Cases" value={String(cases.length)} hint="open / recent" />
            <StatCard label="Approvals" value={String(approvals.length)} hint="manual review queue" tone="warning" />
            <StatCard label="Refund Requests" value={String(refunds.length)} hint="customer refund workload" />
            <StatCard label="Proactive Alerts" value={String(alerts.length)} hint="delay monitoring" tone="danger" />
          </div>

          {loadError ? <div className="notice notice--error">{loadError}</div> : null}
          {message ? <div className="notice notice--success">{message}</div> : null}

          {/* ── Dashboard ── */}
          {activeTab === 'dashboard' && (
            <div className="dashboard-grid dashboard-grid--admin">
              <Surface title="Cases" subtitle="Case queue for operations">
                <div className="table-list">
                  {cases.map((item) => (
                    <article key={item.id} className="table-row">
                      <div>
                        <strong>{item.id}</strong>
                        <p>{item.order_id}</p>
                      </div>
                      <span>{item.case_type}</span>
                      <span>{item.priority}</span>
                      <span className="status-pill">{item.status}</span>
                      <button type="button" className="ghost-button" onClick={() => void loadCaseDetail(item.id)}>
                        View
                      </button>
                      <button type="button" className="ghost-button" onClick={() => void handleCloseCase(item.id)}>
                        Close
                      </button>
                    </article>
                  ))}
                </div>
              </Surface>

              <Surface title="Approvals" subtitle="Human-in-the-loop actions">
                <div className="table-list">
                  {approvals.slice(0, 3).map((item) => (
                    <article key={item.id} className="approval-card">
                      <div className="approval-card__top">
                        <strong>{item.id}</strong>
                        <span className="status-pill">{item.status}</span>
                      </div>
                      <p>{item.requested_action}</p>
                      <div className="approval-card__actions">
                        <button type="button" className="success-button" onClick={() => void handleApprovalAction('approve', item.id)}>
                          Approve
                        </button>
                        <button type="button" className="danger-button" onClick={() => void handleApprovalAction('reject', item.id)}>
                          Reject
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              </Surface>
            </div>
          )}

          {/* ── Cases ── */}
          {activeTab === 'cases' && (
            <div className="dashboard-grid dashboard-grid--admin">
              <Surface title="Cases" subtitle="Case queue for operations">
                <div className="table-list">
                  {cases.map((item) => (
                    <article key={item.id} className="table-row">
                      <div>
                        <strong>{item.id}</strong>
                        <p>{item.order_id}</p>
                      </div>
                      <span>{item.case_type}</span>
                      <span>{item.priority}</span>
                      <span className="status-pill">{item.status}</span>
                      <button type="button" className="ghost-button" onClick={() => void loadCaseDetail(item.id)}>
                        View
                      </button>
                      <button type="button" className="ghost-button" onClick={() => void handleCloseCase(item.id)}>
                        Close
                      </button>
                    </article>
                  ))}
                </div>
              </Surface>

              <Surface title="Case Detail" subtitle="Refund evidence and approval context">
                {caseDetailLoading ? <div className="notice">Loading case detail...</div> : null}
                {!caseDetailLoading && !selectedCase ? <div className="empty-state">Select a case to inspect evidence.</div> : null}
                {!caseDetailLoading && selectedCase ? (
                  <div className="admin-case-detail">
                    <div className="admin-case-detail__header">
                      <div>
                        <strong>{selectedCase.id}</strong>
                        <p>{selectedCase.case_type} · {selectedCase.status}</p>
                      </div>
                      <span className="status-pill">{selectedCase.priority ?? 'normal'}</span>
                    </div>

                    <div className="admin-case-detail__section">
                      <strong>Refund Requests</strong>
                      <div className="list-stack">
                        {selectedCase.refund_requests.map((refund) => (
                          <article key={refund.id} className="list-card">
                            <div>
                              <strong>{refund.id}</strong>
                              <p>{refund.reason}</p>
                            </div>
                            <div className="list-card__meta">
                              <span>Risk {refund.risk_score}</span>
                              <span className="status-pill">{refund.status}</span>
                            </div>
                            {refund.attachments.length > 0 ? (
                              <div className="admin-attachment-list">
                                {refund.attachments.map((attachment) => (
                                  <div key={attachment.id} className="admin-attachment-item">
                                    <div>
                                      <strong>{attachment.file_name ?? attachment.id}</strong>
                                      <p>{attachment.description ?? attachment.evidence_group ?? 'evidence'}</p>
                                    </div>
                                    <button
                                      type="button"
                                      className="ghost-button"
                                      onClick={() => void openAttachment(attachment.id)}
                                      disabled={openingAttachmentId === attachment.id}
                                    >
                                      {openingAttachmentId === attachment.id ? 'Opening...' : 'Open'}
                                    </button>
                                  </div>
                                ))}
                              </div>
                            ) : null}
                          </article>
                        ))}
                      </div>
                    </div>

                    <div className="admin-case-detail__section">
                      <strong>Approvals</strong>
                      <div className="list-stack">
                        {selectedCase.approvals.map((approval) => (
                          <article key={approval.id} className="list-card">
                            <div>
                              <strong>{approval.id}</strong>
                              <p>{approval.requested_action}</p>
                            </div>
                            <div className="list-card__meta">
                              <span>{approval.risk_level}</span>
                              <span className="status-pill">{approval.status}</span>
                            </div>
                          </article>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : null}
              </Surface>
            </div>
          )}

          {/* ── Approvals ── */}
          {activeTab === 'approvals' && (
            <Surface title="Approvals" subtitle="Human-in-the-loop actions">
              <div className="table-list">
                {approvals.map((item) => (
                  <article key={item.id} className="approval-card">
                    <div className="approval-card__top">
                      <strong>{item.id}</strong>
                      <span className="status-pill">{item.status}</span>
                    </div>
                    <p>{item.requested_action}</p>
                    <small>{item.ai_reason}</small>
                    <div className="approval-card__actions">
                      <button type="button" className="success-button" onClick={() => void handleApprovalAction('approve', item.id)}>
                        Approve
                      </button>
                      <button type="button" className="danger-button" onClick={() => void handleApprovalAction('reject', item.id)}>
                        Reject
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            </Surface>
          )}

          {/* ── Refunds ── */}
          {activeTab === 'refunds' && (
            <Surface title="Refund / Return" subtitle="Caseworker workspace">
              <div className="list-stack">
                {refunds.map((item) => (
                  <article key={item.id} className="list-card">
                    <div>
                      <strong>{item.id}</strong>
                      <p>{item.order_id}</p>
                    </div>
                    <div className="list-card__meta">
                      <span>Risk {item.risk_score}</span>
                      <span className="status-pill">{item.status}</span>
                    </div>
                  </article>
                ))}
              </div>
            </Surface>
          )}

          {/* ── Proactive Alerts ── */}
          {activeTab === 'alerts' && (
            <Surface title="Proactive Alerts" subtitle="Shipment delay watchlist">
              <div className="list-stack">
                {alerts.map((item) => (
                  <article key={item.id} className="list-card">
                    <div>
                      <strong>{item.id}</strong>
                      <p>{item.shipment_id}</p>
                    </div>
                    <div className="list-card__meta">
                      <span>Risk {item.risk_score}</span>
                      <button type="button" className="ghost-button" onClick={() => void handleResolveAlert(item.id)}>
                        Resolve
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            </Surface>
          )}
        </div>
      </div>
    </PortalShell>
  )
}
