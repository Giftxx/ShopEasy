import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../../lib/api'
import { clearSession, readSession } from '../../lib/session'
import type { Approval, CaseDetail, CaseSummary, ProactiveAlert, RefundRequest } from '../../types/api'

type AdminTab = 'cases' | 'approvals' | 'refunds' | 'alerts'

const NAV: { key: AdminTab; label: string; icon: string }[] = [
  { key: 'cases',     label: 'Cases',            icon: '▣' },
  { key: 'approvals', label: 'Approvals',        icon: '✓' },
  { key: 'refunds',   label: 'Refund / Return',  icon: '↩' },
  { key: 'alerts',    label: 'Proactive Alerts', icon: '◉' },
]

function pillClass(status?: string | null): string {
  const s = (status ?? '').toLowerCase()
  if (['approved', 'resolved', 'closed', 'completed', 'success'].includes(s)) return 'status-pill--success'
  if (['pending', 'open', 'processing'].includes(s)) return 'status-pill--warning'
  if (['rejected', 'failed', 'high', 'critical'].includes(s)) return 'status-pill--danger'
  return ''
}

function riskClass(score?: number | null): string {
  if (score == null) return ''
  if (score >= 70) return 'risk--high'
  if (score >= 40) return 'risk--medium'
  return 'risk--low'
}

export function AdminPortal() {
  const navigate = useNavigate()
  const session = readSession()
  const userName = session?.user?.name ?? 'Admin'

  const [searchParams, setSearchParams] = useSearchParams()
  const tab = (searchParams.get('tab') as AdminTab) ?? 'cases'
  const setTab = (t: AdminTab) => setSearchParams({ tab: t }, { replace: true })
  const [cases, setCases] = useState<CaseSummary[]>([])
  const [approvals, setApprovals] = useState<Approval[]>([])
  const [refunds, setRefunds] = useState<RefundRequest[]>([])
  const [alerts, setAlerts] = useState<ProactiveAlert[]>([])
  const [toast, setToast] = useState<{ msg: string; type: 'ok' | 'err' } | null>(null)
  const [selectedCase, setSelectedCase] = useState<CaseDetail | null>(null)
  const [caseLoading, setCaseLoading] = useState(false)
  const [openingAttId, setOpeningAttId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function notify(msg: string, type: 'ok' | 'err' = 'ok') {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }

  async function load() {
    setLoading(true)
    try {
      const [c, a, r, al] = await Promise.all([
        api.getCases(), api.getApprovals(), api.getRefundRequests(), api.getProactiveAlerts(),
      ])
      setCases(c); setApprovals(a); setRefunds(r); setAlerts(al)
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Load failed', 'err')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void load() }, [])

  async function openCase(id: string) {
    setCaseLoading(true); setTab('cases')
    try { setSelectedCase(await api.getCaseDetail(id)) }
    finally { setCaseLoading(false) }
  }

  async function handleApproval(type: 'approve' | 'reject', id: string) {
    try {
      if (type === 'approve') await api.approveApproval(id, 'Approved')
      else await api.rejectApproval(id, 'Rejected')
      notify(type === 'approve' ? 'Approved' : 'Rejected')
      await load()
    } catch { notify('Action failed', 'err') }
  }

  async function handleCloseCase(id: string) {
    try {
      await api.closeCase(id, 'Closed')
      notify('Case closed')
      await load()
      if (selectedCase?.id === id) await openCase(id)
    } catch { notify('Failed', 'err') }
  }

  async function handleResolveAlert(id: string) {
    try {
      await api.resolveAlert(id, 'Resolved')
      notify('Alert resolved')
      await load()
    } catch { notify('Failed', 'err') }
  }

  function openAttachment(id: string) {
    window.open(api.getAttachmentDirectUrl(id), '_blank', 'noopener,noreferrer')
  }

  const pendingApprovals = approvals.filter(a => a.status === 'pending')
  const openAlerts = alerts.filter(a => a.status !== 'resolved')

  return (
    <div className="op-app">
      {/* ── Sidebar ── */}
      <aside className="op-sidebar">
        <div className="op-brand">
          <div className="op-brand__logo">S</div>
          <div>
            <span className="op-brand__name">ShopEasy</span>
            <span className="op-brand__role">Admin Console</span>
          </div>
        </div>
        <nav className="op-nav">
          {NAV.map(item => (
            <button
              key={item.key}
              type="button"
              className={`op-nav-item${tab === item.key ? ' is-active' : ''}`}
              onClick={() => setTab(item.key)}
            >
              <span className="op-nav-item__icon">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="op-sidebar-stats">
          <div className="op-sstat"><strong>{cases.length}</strong><span>Cases</span></div>
          <div className="op-sstat op-sstat--warn"><strong>{pendingApprovals.length}</strong><span>Pending</span></div>
          <div className="op-sstat op-sstat--danger"><strong>{openAlerts.length}</strong><span>Alerts</span></div>
          <div className="op-sstat"><strong>{refunds.length}</strong><span>Refunds</span></div>
        </div>
        <div className="op-sidebar-footer">
          <div className="op-user">
            <div className="op-user__avatar">{userName.charAt(0).toUpperCase()}</div>
            <div className="op-user__info">
              <strong>{userName}</strong>
              <span>Admin</span>
            </div>
          </div>
          <button
            type="button"
            className="op-logout-btn"
            onClick={() => { clearSession(); navigate('/') }}
          >
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="op-main">
        <div className="op-topbar">
          <h2 className="op-topbar__title">{NAV.find(n => n.key === tab)?.label}</h2>
          <div className="op-topbar__right">
            {loading && <span className="op-loading-badge">Loading…</span>}
            {toast && <span className={`op-toast op-toast--${toast.type}`}>{toast.msg}</span>}
            <button type="button" className="op-btn op-btn--ghost" onClick={() => void load()} disabled={loading}>
              Refresh
            </button>
          </div>
        </div>

        <div className="op-content">
          {/* Cases */}
          {tab === 'cases' && (
            <div className="op-split">
              <div className="op-card">
                <div className="op-card__head">
                  <h3>All Cases</h3>
                  <span className="op-count">{cases.length}</span>
                </div>
                <div className="op-table">
                  {cases.map(c => (
                    <div
                      key={c.id}
                      className={`op-row op-row--clickable${selectedCase?.id === c.id ? ' is-selected' : ''}`}
                      onClick={() => void openCase(c.id)}
                    >
                      <div className="op-row__main">
                        <strong>{c.id}</strong>
                        <span>{c.case_type} · {c.order_id}</span>
                      </div>
                      <span className={`status-pill ${pillClass(c.priority)}`}>{c.priority ?? 'normal'}</span>
                      <span className={`status-pill ${pillClass(c.status)}`}>{c.status}</span>
                      <button
                        type="button"
                        className="op-btn op-btn--ghost"
                        onClick={e => { e.stopPropagation(); void handleCloseCase(c.id) }}
                      >
                        Close
                      </button>
                    </div>
                  ))}
                  {cases.length === 0 && <p className="op-empty">No cases</p>}
                </div>
              </div>

              <div className="op-card">
                <div className="op-card__head"><h3>Detail</h3></div>
                {caseLoading && <p className="op-empty">Loading...</p>}
                {!caseLoading && !selectedCase && <p className="op-empty">Select a case to inspect</p>}
                {!caseLoading && selectedCase && (
                  <div className="op-detail">
                    <div className="op-detail__header">
                      <div>
                        <strong className="op-detail__id">{selectedCase.id}</strong>
                        <span className="op-detail__meta">{selectedCase.case_type}</span>
                      </div>
                      <span className={`status-pill ${pillClass(selectedCase.status)}`}>{selectedCase.status}</span>
                    </div>
                    {selectedCase.refund_requests.length > 0 && (
                      <div className="op-detail-section">
                        <span className="op-detail-section__label">Refund Requests</span>
                        {selectedCase.refund_requests.map(r => (
                          <div key={r.id} className="op-detail-block">
                            <div className="op-detail-block__head">
                              <strong>{r.id}</strong>
                              <span className={`op-meta-chip ${riskClass(r.risk_score)}`}>Risk {r.risk_score}</span>
                              <span className={`status-pill ${pillClass(r.status)}`}>{r.status}</span>
                            </div>
                            {r.reason && <p className="op-detail-block__text">{r.reason}</p>}
                            {r.attachments.length > 0 && (
                              <div className="op-att-list">
                                {r.attachments.map(att => (
                                  <div key={att.id} className="op-att-row">
                                    <span>{att.file_name ?? att.id}</span>
                                    <button
                                      type="button"
                                      className="op-btn op-btn--ghost"
                                      onClick={() => openAttachment(att.id)}
                                      disabled={openingAttId === att.id}
                                    >
                                      {openingAttId === att.id ? '...' : 'Open'}
                                    </button>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                    {selectedCase.approvals.length > 0 && (
                      <div className="op-detail-section">
                        <span className="op-detail-section__label">Approvals</span>
                        {selectedCase.approvals.map(a => (
                          <div key={a.id} className="op-detail-block">
                            <div className="op-detail-block__head">
                              <strong>{a.id}</strong>
                      <span className={`op-meta-chip ${riskClass(a.risk_score)}`}>{a.risk_level}</span>
                              <span className={`status-pill ${pillClass(a.status)}`}>{a.status}</span>
                            </div>
                            <p className="op-detail-block__text">{a.requested_action}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Approvals */}
          {tab === 'approvals' && (
            <div className="op-card">
              <div className="op-card__head">
                <h3>Approvals Queue</h3>
                <span className="op-count">{approvals.length}</span>
              </div>
              <div className="op-table">
                {approvals.map(a => (
                  <div key={a.id} className="op-row op-row--wrap">
                    <div className="op-row__main" style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                        <strong>{a.id}</strong>
                        <span className={`status-pill ${pillClass(a.status)}`}>{a.status}</span>
                      </div>
                      <span>{a.requested_action}</span>
                      {a.ai_reason && <span className="op-ai-note">{a.ai_reason}</span>}
                    </div>
                    {a.status === 'pending' && (
                      <div className="op-btn-group">
                        <button type="button" className="op-btn op-btn--approve" onClick={() => void handleApproval('approve', a.id)}>Approve</button>
                        <button type="button" className="op-btn op-btn--reject" onClick={() => void handleApproval('reject', a.id)}>Reject</button>
                      </div>
                    )}
                  </div>
                ))}
                {approvals.length === 0 && <p className="op-empty">No approvals</p>}
              </div>
            </div>
          )}

          {/* Refunds */}
          {tab === 'refunds' && (
            <div className="op-card">
              <div className="op-card__head">
                <h3>Refund Requests</h3>
                <span className="op-count">{refunds.length}</span>
              </div>
              <div className="op-table">
                {refunds.map(r => (
                  <div key={r.id} className="op-row">
                    <div className="op-row__main">
                      <strong>{r.id}</strong>
                      <span>{r.order_id} · {r.customer_id}</span>
                      {r.reason && <span className="op-row__note">{r.reason}</span>}
                    </div>
                    <span className={`op-meta-chip ${riskClass(r.risk_score)}`}>Risk {r.risk_score}</span>
                    <span className={`status-pill ${pillClass(r.status)}`}>{r.status}</span>
                    {r.case_id && (
                      <button type="button" className="op-btn op-btn--ghost" onClick={() => void openCase(r.case_id!)}>Case</button>
                    )}
                  </div>
                ))}
                {refunds.length === 0 && <p className="op-empty">No refund requests</p>}
              </div>
            </div>
          )}

          {/* Alerts */}
          {tab === 'alerts' && (
            <div className="op-card">
              <div className="op-card__head">
                <h3>Proactive Alerts</h3>
                <span className="op-count">{openAlerts.length} open</span>
              </div>
              <div className="op-table">
                {alerts.map(a => (
                  <div key={a.id} className="op-row">
                    <div className="op-row__main">
                      <strong>{a.id}</strong>
                      <span>{a.shipment_id}{a.order_id ? ` · ${a.order_id}` : ''}</span>
                      {a.message_draft && (
                        <span className="op-row__note">
                          {a.message_draft.length > 90 ? `${a.message_draft.slice(0, 90)}…` : a.message_draft}
                        </span>
                      )}
                    </div>
                    <span className={`op-meta-chip ${riskClass(a.risk_score)}`}>Risk {a.risk_score}</span>
                    <span className={`status-pill ${pillClass(a.status)}`}>{a.status}</span>
                    {a.status !== 'resolved' && (
                      <button type="button" className="op-btn op-btn--ghost" onClick={() => void handleResolveAlert(a.id)}>Resolve</button>
                    )}
                  </div>
                ))}
                {alerts.length === 0 && <p className="op-empty">No alerts</p>}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
