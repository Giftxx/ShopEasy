import { useEffect, useState } from 'react'
import { api } from '../../../lib/api'
import type { ToolLog, TraceDetail, TraceSummary } from '../../../types/api'
import { SectionHeader } from '../components/SectionHeader'
import { InfoPanel } from '../components/InfoPanel'

function statusColor(status?: string | null): string {
  if (status === 'success') return '#10b981'
  if (status === 'error') return '#ef4444'
  if (status === 'running') return '#f59e0b'
  return '#6b7280'
}

function formatTime(iso?: string | null): string {
  if (!iso) return '-'
  try {
    return new Date(iso).toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return iso
  }
}

export function TracesTab() {
  const [traces, setTraces] = useState<TraceSummary[]>([])
  const [selectedTrace, setSelectedTrace] = useState<TraceDetail | null>(null)
  const [logs, setLogs] = useState<ToolLog[]>([])
  const [loading, setLoading] = useState(false)
  const [workflowFilter, setWorkflowFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [intentFilter, setIntentFilter] = useState('')
  const [caseFilter, setCaseFilter] = useState('')

  async function loadTraces(filters?: { workflow_name?: string; status?: string; intent?: string; case_id?: string }) {
    const data = await api.getAgentTraces(filters)
    setTraces(data)
    if (data[0]) {
      const [detail, logData] = await Promise.all([api.getAgentTrace(data[0].id), api.getToolLogs({ trace_id: data[0].id })])
      setSelectedTrace(detail)
      setLogs(logData)
    } else {
      setSelectedTrace(null)
      setLogs([])
    }
  }

  useEffect(() => {
    setLoading(true)
    void loadTraces().finally(() => setLoading(false))
  }, [])

  async function openTrace(id: string) {
    const [detail, logData] = await Promise.all([api.getAgentTrace(id), api.getToolLogs({ trace_id: id })])
    setSelectedTrace(detail)
    setLogs(logData)
  }

  return (
    <div className="ai-section ai-tab-shell">
      <SectionHeader
        num="2"
        title="Agent Traces"
        subtitle="ตรวจสอบการทำงานของ Agent"
        caption="ดูรายละเอียดทุกขั้นตอนการตัดสินใจ, Tool Calls, ข้อมูลที่นำมาใช้ และผลลัพธ์"
      />
      {loading && <div className="notice">Loading traces...</div>}
      <div className="ai-traces-layout">
        <div>
          <div className="ai-filter-bar ai-filter-bar--panel">
            <input value={workflowFilter} onChange={(e) => setWorkflowFilter(e.target.value)} placeholder="Workflow" />
            <input value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} placeholder="Status" />
            <input value={intentFilter} onChange={(e) => setIntentFilter(e.target.value)} placeholder="Intent" />
            <input value={caseFilter} onChange={(e) => setCaseFilter(e.target.value)} placeholder="Case ID" />
            <button
              type="button"
              className="ghost-button"
              onClick={() => {
                setLoading(true)
                void loadTraces({
                  workflow_name: workflowFilter || undefined,
                  status: statusFilter || undefined,
                  intent: intentFilter || undefined,
                  case_id: caseFilter || undefined,
                }).finally(() => setLoading(false))
              }}
            >
              Apply
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={() => {
                setWorkflowFilter('')
                setStatusFilter('')
                setIntentFilter('')
                setCaseFilter('')
                setLoading(true)
                void loadTraces().finally(() => setLoading(false))
              }}
            >
              Reset
            </button>
          </div>

          <div className="ai-trace-card">
            <div className="ai-trace-card__header">
              <span>Trace ID: <strong>{selectedTrace?.id ?? '-'}</strong></span>
              <span className="status-pill" style={{ background: '#dcfce7', color: '#15803d' }}>
                {selectedTrace?.status ?? '-'}
              </span>
            </div>
            {!selectedTrace ? (
              <p className="ai-section-caption">ยังไม่มี trace — ลองส่ง chat ก่อนแล้วกด Apply</p>
            ) : (
              <div className="ai-timeline">
                {/* Header: intent + confidence */}
                {selectedTrace.intent ? (
                  <div className="ai-timeline-item">
                    <div className="ai-timeline-left">
                      <span className="ai-timeline-dot" style={{ background: '#8b5cf6' }} />
                      {(selectedTrace.tool_logs?.length ?? 0) > 0 && <span className="ai-timeline-line" />}
                    </div>
                    <div className="ai-timeline-body">
                      <div className="ai-timeline-row">
                        <span className="ai-timeline-time">{formatTime(selectedTrace.started_at)}</span>
                        <strong className="ai-timeline-label">Intent Detection</strong>
                        {selectedTrace.confidence != null && (
                          <span className="ai-timeline-meta" style={{ color: '#8b5cf6' }}>Conf: {selectedTrace.confidence.toFixed(2)}</span>
                        )}
                      </div>
                      <p className="ai-timeline-detail">{selectedTrace.intent}</p>
                    </div>
                  </div>
                ) : null}
                {/* Tool logs */}
                {(selectedTrace.tool_logs ?? logs).map((log, i) => {
                  const color = statusColor(log.status)
                  const isLast = i === (selectedTrace.tool_logs ?? logs).length - 1
                  return (
                    <div key={log.id} className="ai-timeline-item">
                      <div className="ai-timeline-left">
                        <span className="ai-timeline-dot" style={{ background: color }} />
                        {!isLast && <span className="ai-timeline-line" />}
                      </div>
                      <div className="ai-timeline-body">
                        <div className="ai-timeline-row">
                          <span className="ai-timeline-time">{formatTime(log.created_at)}</span>
                          <strong className="ai-timeline-label">
                            {log.agent_name ? `[${log.agent_name}] ` : ''}{log.tool_name ?? 'tool'}
                          </strong>
                          {log.latency_ms != null && (
                            <span className="ai-timeline-meta" style={{ color }}>
                              {log.status} {log.latency_ms}ms
                            </span>
                          )}
                        </div>
                        {log.error_message ? (
                          <p className="ai-timeline-detail" style={{ color: '#ef4444' }}>{log.error_message}</p>
                        ) : null}
                      </div>
                    </div>
                  )
                })}
                {/* Final response */}
                {selectedTrace.final_response ? (
                  <div className="ai-timeline-item">
                    <div className="ai-timeline-left">
                      <span className="ai-timeline-dot" style={{ background: '#6b7280' }} />
                    </div>
                    <div className="ai-timeline-body">
                      <div className="ai-timeline-row">
                        <span className="ai-timeline-time">{formatTime(selectedTrace.ended_at)}</span>
                        <strong className="ai-timeline-label">Response Generated</strong>
                      </div>
                      <p className="ai-timeline-detail" style={{ fontSize: '0.82rem' }}>{selectedTrace.final_response.slice(0, 120)}{selectedTrace.final_response.length > 120 ? '…' : ''}</p>
                    </div>
                  </div>
                ) : null}
              </div>
            )}
            {logs.length > 0 ? <p className="ai-section-caption">Loaded {logs.length} tool log entries for the selected trace.</p> : null}
          </div>

          {traces.length > 0 && (
            <div className="ai-trace-list">
              {traces.map((trace) => (
                <button key={trace.id} type="button" className="trace-row" onClick={() => void openTrace(trace.id)}>
                  <div>
                    <strong>{trace.workflow_name}</strong>
                    <p>{trace.id}</p>
                  </div>
                  <div className="list-card__meta">
                    <span>{trace.intent}</span>
                    <span className="status-pill">{trace.status}</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
        <InfoPanel
          main={['ดู Trace ทั้งหมด', 'ดู Tool Calls', 'ดูข้อมูลที่ Retrieve', 'ตรวจสอบ Decision', 'ตรวจสอบ Response']}
          features={['Step-by-step Timeline', 'Tool Call Details', 'Retrieved Chunks', 'Model I/O', 'Export Trace']}
        />
      </div>
    </div>
  )
}
