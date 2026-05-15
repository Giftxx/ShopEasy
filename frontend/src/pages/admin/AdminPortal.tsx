import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../../lib/api'
import { clearSession, readSession } from '../../lib/session'
import type {
  Approval,
  CaseDetail,
  CaseSummary,
  ProactiveAlert,
  RefundRequest,
} from '../../types/api'
import { RagTab } from '../ai/tabs/RagTab'

type AdminTab = 'cases' | 'alerts' | 'policies'

const NAV: { key: AdminTab; label: string; icon: string }[] = [
  { key: 'cases',    label: 'Cases',            icon: '▣' },
  { key: 'alerts',   label: 'Proactive Alerts', icon: '◉' },
  { key: 'policies', label: 'Policies / RAG',   icon: '✎' },
]

// ── Taxonomy helpers ─────────────────────────────────────────────────────────

const CATEGORY_OPTIONS: { key: string; label: string; match: (t?: string | null) => boolean }[] = [
  { key: 'all',               label: 'All',               match: () => true },
  { key: 'refund',            label: 'Refund',            match: (t) => (t ?? '').toLowerCase() === 'refund' },
  { key: 'shipping_delay',    label: 'Shipping Delay',    match: (t) => (t ?? '').toLowerCase() === 'shipping_delay' },
  { key: 'product_complaint', label: 'Product Complaint', match: (t) => (t ?? '').toLowerCase() === 'product_complaint' },
  { key: 'general_inquiry',   label: 'General Inquiry',   match: (t) => !['refund', 'shipping_delay', 'product_complaint'].includes((t ?? '').toLowerCase()) },
]

const CASE_STATUS_OPTIONS: { key: string; label: string }[] = [
  { key: 'all',         label: 'Any status' },
  { key: 'open',        label: 'Open' },
  { key: 'in_progress', label: 'In Progress' },
  { key: 'resolved',    label: 'Resolved' },
  { key: 'closed',      label: 'Closed' },
]

const APPROVAL_STATUS_OPTIONS: { key: string; label: string }[] = [
  { key: 'all',                label: 'Any approval' },
  { key: 'pending_review',     label: 'Pending Review' },
  { key: 'approved',           label: 'Approved' },
  { key: 'rejected',           label: 'Rejected' },
  { key: 'needs_human_review', label: 'Needs Human Review' },
]

const PRIORITY_TONE: Record<string, string> = {
  low:      'badge--low',
  medium:   'badge--medium',
  high:     'badge--high',
  critical: 'badge--critical',
}

const CASE_STATUS_TONE: Record<string, string> = {
  open:        'badge--open',
  in_progress: 'badge--inprogress',
  resolved:    'badge--resolved',
  closed:      'badge--closed',
}

const APPROVAL_TONE: Record<string, string> = {
  pending_review:     'badge--pending',
  pending:            'badge--pending',
  approved:           'badge--approved',
  rejected:           'badge--rejected',
  needs_human_review: 'badge--human',
}

function normCaseStatus(s?: string | null): string {
  return (s ?? 'open').toLowerCase()
}

function normPriority(p?: string | null): string {
  const v = (p ?? 'medium').toLowerCase()
  if (['low', 'medium', 'high', 'critical'].includes(v)) return v
  if (v === 'urgent') return 'critical'
  return 'medium'
}

function categoryLabel(t?: string | null): string {
  switch ((t ?? '').toLowerCase()) {
    case 'refund':            return 'Refund'
    case 'shipping_delay':    return 'Shipping Delay'
    case 'product_complaint': return 'Product Complaint'
    default:                  return 'General Inquiry'
  }
}

function caseAssignedTeam(t?: string | null): string {
  switch ((t ?? '').toLowerCase()) {
    case 'refund':            return 'Refund Ops'
    case 'shipping_delay':    return 'Logistics'
    case 'product_complaint': return 'Quality'
    default:                  return 'Support'
  }
}

function deriveApprovalStatus(c: CaseSummary, approvalsByCase: Map<string, Approval[]>): string {
  const list = approvalsByCase.get(c.id) ?? []
  if (list.some((a) => (a.status ?? '').toLowerCase() === 'pending')) return 'pending_review'
  if (list.length === 0) return 'pending_review'
  const last = list[0]
  const v = (last.status ?? '').toLowerCase()
  if (v === 'approved') return 'approved'
  if (v === 'rejected') return 'rejected'
  if (v === 'escalated' || v === 'needs_human') return 'needs_human_review'
  return v || 'pending_review'
}

function fmtDate(iso?: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleString('th-TH', { day: 'numeric', month: 'short', year: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function riskClass(score?: number | null): string {
  if (score == null) return ''
  if (score >= 70) return 'risk--high'
  if (score >= 40) return 'risk--medium'
  return 'risk--low'
}

// ── Component ────────────────────────────────────────────────────────────────

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

  // Filters
  const [search, setSearch] = useState('')
  const [filterCategory, setFilterCategory] = useState<string>('all')
  const [filterCaseStatus, setFilterCaseStatus] = useState<string>('all')
  const [filterApprovalStatus, setFilterApprovalStatus] = useState<string>('all')

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
      if (selectedCase) await openCase(selectedCase.id)
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
    setOpeningAttId(id)
    window.open(api.getAttachmentDirectUrl(id), '_blank', 'noopener,noreferrer')
    setTimeout(() => setOpeningAttId(null), 800)
  }

  // Derived data ────────────────────────────────────────────────────────────
  const approvalsByCase = useMemo(() => {
    const m = new Map<string, Approval[]>()
    for (const a of approvals) {
      const k = a.case_id
      if (!k) continue
      if (!m.has(k)) m.set(k, [])
      m.get(k)!.push(a)
    }
    return m
  }, [approvals])

  const filteredCases = useMemo(() => {
    const q = search.trim().toLowerCase()
    const catMatcher = CATEGORY_OPTIONS.find((c) => c.key === filterCategory)?.match ?? (() => true)
    return cases.filter((c) => {
      if (!catMatcher(c.case_type)) return false
      if (filterCaseStatus !== 'all' && normCaseStatus(c.status) !== filterCaseStatus) return false
      if (filterApprovalStatus !== 'all' && deriveApprovalStatus(c, approvalsByCase) !== filterApprovalStatus) return false
      if (q) {
        const hay = `${c.id} ${c.customer_id ?? ''} ${c.order_id ?? ''}`.toLowerCase()
        if (!hay.includes(q)) return false
      }
      return true
    })
  }, [cases, approvalsByCase, filterCategory, filterCaseStatus, filterApprovalStatus, search])

  const pendingApprovals = approvals.filter(a => (a.status ?? '').toLowerCase() === 'pending')
  const openAlerts = alerts.filter(a => (a.status ?? '').toLowerCase() !== 'resolved')

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="op-app">
      {/* ── Sidebar (FIXED) ── */}
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
          {/* ──────────────────────── CASES ──────────────────────── */}
          {tab === 'cases' && (
            <>
              {/* Filter / Search bar */}
              <div className="op-filterbar">
                <div className="op-filterbar__row">
                  <div className="op-search">
                    <span className="op-search__icon">⌕</span>
                    <input
                      type="text"
                      placeholder="Search by Case ID, Customer, Order ID…"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                    />
                    {search && (
                      <button type="button" className="op-search__clear" onClick={() => setSearch('')}>×</button>
                    )}
                  </div>
                  <span className="op-filterbar__count">{filteredCases.length} of {cases.length}</span>
                </div>

                <div className="op-filterbar__group">
                  <span className="op-filterbar__label">Category</span>
                  <div className="op-chip-row">
                    {CATEGORY_OPTIONS.map((opt) => {
                      const count = opt.key === 'all'
                        ? cases.length
                        : cases.filter((c) => opt.match(c.case_type)).length
                      return (
                        <button
                          key={opt.key}
                          type="button"
                          className={`op-chip${filterCategory === opt.key ? ' is-active' : ''}`}
                          onClick={() => setFilterCategory(opt.key)}
                        >
                          {opt.label}
                          <span className="op-chip__count">{count}</span>
                        </button>
                      )
                    })}
                  </div>
                </div>

                <div className="op-filterbar__group">
                  <span className="op-filterbar__label">Case Status</span>
                  <div className="op-chip-row">
                    {CASE_STATUS_OPTIONS.map((opt) => (
                      <button
                        key={opt.key}
                        type="button"
                        className={`op-chip${filterCaseStatus === opt.key ? ' is-active' : ''}`}
                        onClick={() => setFilterCaseStatus(opt.key)}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="op-filterbar__group">
                  <span className="op-filterbar__label">Approval Status</span>
                  <div className="op-chip-row">
                    {APPROVAL_STATUS_OPTIONS.map((opt) => (
                      <button
                        key={opt.key}
                        type="button"
                        className={`op-chip${filterApprovalStatus === opt.key ? ' is-active' : ''}`}
                        onClick={() => setFilterApprovalStatus(opt.key)}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Layout: table + detail */}
              <div className="op-cases-layout">
                {/* Cases table */}
                <div className="op-card op-cases-card">
                  <div className="op-cases-table">
                    <div className="op-cases-table__head">
                      <span>Case ID</span>
                      <span>Category</span>
                      <span>Priority</span>
                      <span>Case Status</span>
                      <span>Approval</span>
                      <span>Created</span>
                      <span>Team</span>
                      <span>Action</span>
                    </div>
                    {filteredCases.map((c) => {
                      const cs = normCaseStatus(c.status)
                      const pr = normPriority(c.priority)
                      const ap = deriveApprovalStatus(c, approvalsByCase)
                      return (
                        <div
                          key={c.id}
                          className={`op-cases-table__row${selectedCase?.id === c.id ? ' is-selected' : ''}`}
                          onClick={() => void openCase(c.id)}
                        >
                          <span className="op-cell-id">
                            <strong>{c.id}</strong>
                            <small>{c.order_id ?? '—'}</small>
                          </span>
                          <span className="op-cell-category">{categoryLabel(c.case_type)}</span>
                          <span><span className={`op-badge ${PRIORITY_TONE[pr]}`}>{pr}</span></span>
                          <span><span className={`op-badge ${CASE_STATUS_TONE[cs]}`}>{cs.replace('_', ' ')}</span></span>
                          <span><span className={`op-badge ${APPROVAL_TONE[ap]}`}>{ap.replace(/_/g, ' ')}</span></span>
                          <span className="op-cell-time">{fmtDate(c.created_at)}</span>
                          <span className="op-cell-team">{caseAssignedTeam(c.case_type)}</span>
                          <span>
                            <button
                              type="button"
                              className="op-btn op-btn--ghost"
                              onClick={(e) => { e.stopPropagation(); void handleCloseCase(c.id) }}
                              disabled={cs === 'closed' || cs === 'resolved'}
                            >
                              {cs === 'closed' || cs === 'resolved' ? 'Done' : 'Close'}
                            </button>
                          </span>
                        </div>
                      )
                    })}
                    {filteredCases.length === 0 && (
                      <p className="op-empty">No cases match the current filters</p>
                    )}
                  </div>
                </div>

                {/* Detail panel */}
                <aside className="op-card op-detail-panel">
                  <div className="op-card__head">
                    <h3>Case Detail</h3>
                    {selectedCase && <span className="op-count">{selectedCase.id}</span>}
                  </div>
                  {caseLoading && <p className="op-empty">Loading…</p>}
                  {!caseLoading && !selectedCase && <p className="op-empty">Select a case to view full detail</p>}
                  {!caseLoading && selectedCase && (() => {
                    const cs = normCaseStatus(selectedCase.status)
                    const pr = normPriority(selectedCase.priority)
                    const ap = deriveApprovalStatus(selectedCase, approvalsByCase)
                    const pending = selectedCase.approvals.filter((a) => (a.status ?? '').toLowerCase() === 'pending')
                    const latestPending = pending[0] ?? null
                    return (
                      <div className="op-detail">
                        {/* Header summary */}
                        <div className="op-detail__hero">
                          <div>
                            <div className="op-detail__hero-id">{selectedCase.id}</div>
                            <div className="op-detail__hero-sub">{categoryLabel(selectedCase.case_type)}</div>
                          </div>
                          <div className="op-detail__hero-badges">
                            <span className={`op-badge ${PRIORITY_TONE[pr]}`}>{pr}</span>
                            <span className={`op-badge ${CASE_STATUS_TONE[cs]}`}>{cs.replace('_', ' ')}</span>
                            <span className={`op-badge ${APPROVAL_TONE[ap]}`}>{ap.replace(/_/g, ' ')}</span>
                          </div>
                        </div>

                        {/* Meta grid */}
                        <div className="op-detail__meta-grid">
                          <div><span>Customer</span><strong>{selectedCase.customer_id}</strong></div>
                          <div><span>Order / Reference</span><strong>{selectedCase.order_id ?? '—'}</strong></div>
                          <div><span>Assigned Team</span><strong>{caseAssignedTeam(selectedCase.case_type)}</strong></div>
                          <div><span>Created</span><strong>{fmtDate(selectedCase.created_at)}</strong></div>
                          <div><span>Last Updated</span><strong>{fmtDate(selectedCase.updated_at)}</strong></div>
                          <div><span>Source</span><strong>{selectedCase.created_by ?? 'web_chat'}</strong></div>
                        </div>

                        {/* AI Summary */}
                        {selectedCase.ai_summary && (
                          <section className="op-detail-section">
                            <span className="op-detail-section__label">AI Summary</span>
                            <div className="op-ai-card">
                              <span className="op-ai-card__icon">✦</span>
                              <p>{selectedCase.ai_summary}</p>
                            </div>
                          </section>
                        )}

                        {/* Refund Requests */}
                        {selectedCase.refund_requests.length > 0 && (
                          <section className="op-detail-section">
                            <span className="op-detail-section__label">Refund Requests</span>
                            {selectedCase.refund_requests.map(r => (
                              <div key={r.id} className="op-detail-block">
                                <div className="op-detail-block__head">
                                  <strong>{r.id}</strong>
                                  <span className={`op-meta-chip ${riskClass(r.risk_score)}`}>Risk {r.risk_score}</span>
                                  <span className={`op-badge ${APPROVAL_TONE[(r.status ?? '').toLowerCase()] ?? ''}`}>{r.status}</span>
                                </div>
                                {r.reason && <p className="op-detail-block__text">{r.reason}</p>}
                                {r.attachments.length > 0 && (
                                  <div className="op-att-list">
                                    {r.attachments.map(att => (
                                      <div key={att.id} className="op-att-row">
                                        <span>📎 {att.file_name ?? att.id}</span>
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
                          </section>
                        )}

                        {/* Pending approval */}
                        {latestPending && (
                          <section className="op-detail-section">
                            <span className="op-detail-section__label">Pending Approval</span>
                            <div className="op-detail-block">
                              <div className="op-detail-block__head">
                                <span className={`op-meta-chip ${riskClass(latestPending.risk_score)}`}>{latestPending.risk_level}</span>
                                <span className="op-badge badge--pending">pending review</span>
                              </div>
                              <p className="op-detail-block__text">{latestPending.requested_action}</p>
                              {latestPending.ai_reason && <p className="op-ai-note">AI: {latestPending.ai_reason}</p>}
                            </div>
                          </section>
                        )}

                        {/* Timeline */}
                        <section className="op-detail-section">
                          <span className="op-detail-section__label">Timeline</span>
                          <ul className="op-timeline">
                            <li><strong>Case opened</strong><span>{fmtDate(selectedCase.created_at)}</span></li>
                            {selectedCase.updated_at && selectedCase.updated_at !== selectedCase.created_at && (
                              <li><strong>Last updated</strong><span>{fmtDate(selectedCase.updated_at)}</span></li>
                            )}
                            {(approvalsByCase.get(selectedCase.id) ?? []).slice(0, 5).map((a) => (
                              <li key={a.id}>
                                <strong>Approval {a.status}</strong>
                                <span>{fmtDate(a.created_at)}</span>
                              </li>
                            ))}
                          </ul>
                        </section>

                        {/* Actions */}
                        <section className="op-detail-actions">
                          {latestPending && (
                            <>
                              <button type="button" className="op-btn op-btn--approve" onClick={() => void handleApproval('approve', latestPending.id)}>Approve</button>
                              <button type="button" className="op-btn op-btn--reject" onClick={() => void handleApproval('reject', latestPending.id)}>Reject</button>
                            </>
                          )}
                          <button
                            type="button"
                            className="op-btn op-btn--ghost"
                            onClick={() => void handleCloseCase(selectedCase.id)}
                            disabled={cs === 'closed' || cs === 'resolved'}
                          >
                            Close Case
                          </button>
                        </section>
                      </div>
                    )
                  })()}
                </aside>
              </div>
            </>
          )}

          {/* ──────────────────────── ALERTS ──────────────────────── */}
          {tab === 'alerts' && (
            <div className="op-card">
              <div className="op-card__head">
                <h3>Proactive Alerts</h3>
                <span className="op-count">{openAlerts.length} open</span>
              </div>
              <div className="op-table">
                {alerts.map(a => {
                  const isResolved = (a.status ?? '').toLowerCase() === 'resolved'
                  return (
                    <div key={a.id} className="op-row">
                      <div className="op-row__main">
                        <strong>{a.id}</strong>
                        <span>{a.shipment_id}{a.order_id ? ` · ${a.order_id}` : ''}</span>
                        {a.alert_type && (
                          <span className="op-row__note" style={{ fontWeight: 600, color: '#ff5d2e' }}>{a.alert_type}</span>
                        )}
                        {a.recommended_action && (
                          <span className="op-row__note">{a.recommended_action}</span>
                        )}
                        {a.message_draft && (
                          <span className="op-row__note">
                            {a.message_draft.length > 90 ? `${a.message_draft.slice(0, 90)}…` : a.message_draft}
                          </span>
                        )}
                      </div>
                      <span className={`op-meta-chip ${riskClass(a.risk_score)}`}>Risk {a.risk_score ?? '—'}</span>
                      <span className={`op-badge ${isResolved ? 'badge--resolved' : 'badge--open'}`}>
                        {isResolved ? 'Resolved' : 'Open'}
                      </span>
                      <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                        {/* Open Case: navigate to Cases tab and load the linked case */}
                        {a.case_id && (
                          <button
                            type="button"
                            className="op-btn op-btn--primary"
                            title={`เปิดเคส ${a.case_id} ในหน้า Cases`}
                            onClick={() => void openCase(a.case_id!)}
                          >
                            Open Case
                          </button>
                        )}
                        {!isResolved && (
                          <button
                            type="button"
                            className="op-btn op-btn--ghost"
                            onClick={() => void handleResolveAlert(a.id)}
                          >
                            Resolve
                          </button>
                        )}
                      </div>
                    </div>
                  )
                })}
                {alerts.length === 0 && <p className="op-empty">No alerts</p>}
              </div>
            </div>
          )}

          {/* ──────────────────────── POLICIES / RAG ──────────────────────── */}
          {tab === 'policies' && <RagTab />}
        </div>
      </div>
    </div>
  )
}
