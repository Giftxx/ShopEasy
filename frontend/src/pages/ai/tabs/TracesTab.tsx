import { useEffect, useState } from 'react'
import { api } from '../../../lib/api'
import type { TraceDetail, TraceSummary } from '../../../types/api'

// ── Helpers ───────────────────────────────────────────────────────────────────

const WF_LABEL: Record<string, string> = {
  workflow_01_track_shipment: 'WF01 · Tracking',
  workflow_02_refund:         'WF02 · Refund',
  workflow_03_proactive:      'WF03 · Proactive',
  admin_approval_action:      'Admin Action',
}
const WF_COLOR: Record<string, string> = {
  workflow_01_track_shipment: '#89b4f7',
  workflow_02_refund:         '#f5a878',
  workflow_03_proactive:      '#f08898',
  admin_approval_action:      '#b8a0e8',
}
const STATUS_DOT: Record<string, string> = {
  success:   '#76c9a0',
  failed:    '#f09090',
  completed: '#89b4f7',
  fallback:  '#f0c870',
  error:     '#f09090',
  running:   '#f0c870',
}
const TOOL_COLOR: Record<string, string> = {
  detect_intent:        '#b8a0e8',
  get_shipments:        '#76c9a0',
  validate_refund:      '#f0c870',
  search_policy:        '#b8a0e8',
  assess_risk:          '#f09090',
  generate_response:    '#f5a878',
  send_alert:           '#f0d878',
  ingest_event:         '#a8b8cc',
  process_cancellation: '#89b4f7',
  approve_approval:     '#b8a0e8',
}

function dotColor(s?: string | null) { return STATUS_DOT[s ?? ''] ?? '#94a3b8' }

function relTime(iso?: string | null): string {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    const diff = (Date.now() - d.getTime()) / 1000
    if (diff < 60) return `${Math.round(diff)}s ago`
    if (diff < 3600) return `${Math.round(diff / 60)}m ago`
    if (diff < 86400) return `${Math.round(diff / 3600)}h ago`
    return `${Math.round(diff / 86400)}d ago`
  } catch { return '—' }
}

function shortId(id: string) {
  return id.length > 18 ? `${id.slice(0, 8)}…${id.slice(-6)}` : id
}

// ── Filter pills config ───────────────────────────────────────────────────────

const WF_FILTERS = [
  { label: 'All', value: '' },
  { label: 'WF01', value: 'workflow_01_track_shipment' },
  { label: 'WF02', value: 'workflow_02_refund' },
  { label: 'WF03', value: 'workflow_03_proactive' },
]
const STATUS_FILTERS = [
  { label: 'All', value: '' },
  { label: 'Success', value: 'success' },
  { label: 'Completed', value: 'completed' },
  { label: 'Failed', value: 'failed' },
  { label: 'Fallback', value: 'fallback' },
]

// ── Component ─────────────────────────────────────────────────────────────────

export function TracesTab() {
  const [traces, setTraces]           = useState<TraceSummary[]>([])
  const [selected, setSelected]       = useState<TraceDetail | null>(null)
  const [loadingList, setLoadingList] = useState(true)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [wfFilter, setWfFilter]       = useState('')
  const [stFilter, setStFilter]       = useState('')

  // Load trace list
  async function loadList(wf?: string, st?: string) {
    setLoadingList(true)
    try {
      const data = await api.getAgentTraces({
        workflow_name: wf || undefined,
        status: st || undefined,
      })
      setTraces(data)
      if (data[0]) openTrace(data[0].id)
      else setSelected(null)
    } finally {
      setLoadingList(false)
    }
  }

  async function openTrace(id: string) {
    setLoadingDetail(true)
    try {
      const detail = await api.getAgentTrace(id)
      setSelected(detail)
    } finally {
      setLoadingDetail(false)
    }
  }

  useEffect(() => { void loadList() }, [])

  function applyWf(v: string) {
    setWfFilter(v)
    void loadList(v, stFilter)
  }
  function applySt(v: string) {
    setStFilter(v)
    void loadList(wfFilter, v)
  }

  // Timeline steps for selected trace
  const toolLogs = selected?.tool_logs ?? []
  const totalSteps = 1 + toolLogs.length + (selected?.final_response ? 1 : 0)

  return (
    <div className="trc-shell">

      {/* ── Left: list ── */}
      <div className="trc-list-col">

        {/* Filter pills */}
        <div className="trc-filters">
          <div className="trc-filter-group">
            {WF_FILTERS.map(f => (
              <button key={f.value} type="button"
                className={`trc-pill${wfFilter === f.value ? ' is-active' : ''}`}
                onClick={() => applyWf(f.value)}
              >{f.label}</button>
            ))}
          </div>
          <div className="trc-filter-group">
            {STATUS_FILTERS.map(f => (
              <button key={f.value} type="button"
                className={`trc-pill${stFilter === f.value ? ' is-active' : ''}`}
                onClick={() => applySt(f.value)}
              >{f.label}</button>
            ))}
          </div>
        </div>

        {/* Trace rows */}
        <div className="trc-rows">
          {loadingList && <p className="trc-empty">Loading…</p>}
          {!loadingList && traces.length === 0 && <p className="trc-empty">ไม่พบ trace ตรงตามเงื่อนไข</p>}
          {traces.map(t => {
            const wfColor = WF_COLOR[t.workflow_name] ?? '#94a3b8'
            const isActive = selected?.id === t.id
            return (
              <button key={t.id} type="button"
                className={`trc-row${isActive ? ' is-active' : ''}`}
                style={{ borderLeftColor: wfColor }}
                onClick={() => void openTrace(t.id)}
              >
                <div className="trc-row__top">
                  <span className="trc-row__wf" style={{ color: wfColor }}>
                    {WF_LABEL[t.workflow_name] ?? t.workflow_name}
                  </span>
                  <span className="trc-row__dot" style={{ background: dotColor(t.status) }} />
                </div>
                <div className="trc-row__intent">{t.intent ?? '—'}</div>
                <div className="trc-row__foot">
                  <span className="trc-row__id">{shortId(t.id)}</span>
                  <span className="trc-row__time">{relTime(t.started_at)}</span>
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* ── Right: detail ── */}
      <div className="trc-detail">
        {loadingDetail && <p className="trc-empty">Loading detail…</p>}

        {!loadingDetail && !selected && (
          <div className="trc-placeholder">
            <span className="trc-placeholder__icon">· · ·</span>
            <p>เลือก trace จากรายการซ้ายมือ</p>
          </div>
        )}

        {!loadingDetail && selected && (
          <>
            {/* Detail header */}
            <div className="trc-detail__head">
              <div className="trc-detail__head-left">
                <span className="trc-detail__wf"
                  style={{ borderLeftColor: WF_COLOR[selected.workflow_name] ?? '#94a3b8' }}>
                  {WF_LABEL[selected.workflow_name] ?? selected.workflow_name}
                </span>
                <span className="trc-detail__intent">{selected.intent}</span>
              </div>
              <div className="trc-detail__head-right">
                {selected.confidence != null && (
                  <span className="trc-detail__conf">{Math.round(selected.confidence * 100)}% conf</span>
                )}
                <span className="trc-detail__status" style={{ color: dotColor(selected.status) }}>
                  ● {selected.status}
                </span>
                {selected.requires_human_approval && (
                  <span className="trc-detail__human">Human Review</span>
                )}
              </div>
            </div>

            {/* Stats row */}
            <div className="trc-stats">
              <div className="trc-stat">
                <span className="trc-stat__label">Steps</span>
                <span className="trc-stat__val">{totalSteps}</span>
              </div>
              <div className="trc-stat">
                <span className="trc-stat__label">Tools called</span>
                <span className="trc-stat__val">{toolLogs.length}</span>
              </div>
              <div className="trc-stat">
                <span className="trc-stat__label">Total latency</span>
                <span className="trc-stat__val">
                  {toolLogs.reduce((s, l) => s + (l.latency_ms ?? 0), 0) > 1000
                    ? `${(toolLogs.reduce((s, l) => s + (l.latency_ms ?? 0), 0) / 1000).toFixed(1)}s`
                    : `${toolLogs.reduce((s, l) => s + (l.latency_ms ?? 0), 0)}ms`}
                </span>
              </div>
              <div className="trc-stat">
                <span className="trc-stat__label">Started</span>
                <span className="trc-stat__val">{relTime(selected.started_at)}</span>
              </div>
            </div>

            {/* Timeline */}
            <div className="trc-timeline">

              {/* Step 1: Intent */}
              <div className="trc-step">
                <div className="trc-step__left">
                  <span className="trc-step__dot" style={{ background: '#b8a0e8', boxShadow: '0 0 0 3px #ede9fe' }} />
                  {(toolLogs.length > 0 || selected.final_response) && <span className="trc-step__line" />}
                </div>
                <div className="trc-step__body">
                  <div className="trc-step__row">
                    <span className="trc-step__name">Intent Detected</span>
                    <span className="trc-step__badge" style={{ background: '#f0ebff', color: '#8b6fcc' }}>
                      {selected.intent}
                    </span>
                  </div>
                  {selected.confidence != null && (
                    <div className="trc-step__detail">Confidence: {Math.round(selected.confidence * 100)}%</div>
                  )}
                </div>
              </div>

              {/* Steps: Tool logs */}
              {toolLogs.map((log, i) => {
                const tc = TOOL_COLOR[log.tool_name ?? ''] ?? '#94a3b8'
                const ok = log.status !== 'failed' && log.status !== 'error'
                const isLast = i === toolLogs.length - 1 && !selected.final_response
                return (
                  <div key={log.id} className="trc-step">
                    <div className="trc-step__left">
                      <span className="trc-step__dot"
                        style={{ background: ok ? tc : '#f09090', boxShadow: `0 0 0 3px ${ok ? tc : '#f09090'}44` }} />
                      {!isLast && <span className="trc-step__line" />}
                    </div>
                    <div className="trc-step__body">
                      <div className="trc-step__row">
                        <span className="trc-step__name" style={{ color: tc }}>
                          {log.tool_name}
                        </span>
                        <span className="trc-step__agent">{log.agent_name}</span>
                        {log.latency_ms != null && (
                          <span className="trc-step__lat" style={{ color: ok ? '#9ca3af' : '#ef4444' }}>
                            {log.latency_ms < 1000 ? `${log.latency_ms}ms` : `${(log.latency_ms / 1000).toFixed(1)}s`}
                          </span>
                        )}
                      </div>
                      {log.error_message && (
                        <div className="trc-step__error">{log.error_message}</div>
                      )}
                    </div>
                  </div>
                )
              })}

              {/* Final step: response */}
              {selected.final_response && (
                <div className="trc-step">
                  <div className="trc-step__left">
                    <span className="trc-step__dot" style={{ background: '#76c9a0', boxShadow: '0 0 0 3px #dcf5ec' }} />
                  </div>
                  <div className="trc-step__body">
                    <div className="trc-step__row">
                      <span className="trc-step__name">Response</span>
                      <span className="trc-step__lat">{relTime(selected.ended_at)}</span>
                    </div>
                    <div className="trc-step__response">
                      {selected.final_response.length > 200
                        ? `${selected.final_response.slice(0, 200)}…`
                        : selected.final_response}
                    </div>
                  </div>
                </div>
              )}

            </div>

            {/* Trace ID footer */}
            <div className="trc-detail__footer">
              trace id: <span className="trc-detail__id">{selected.id}</span>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
