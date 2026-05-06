import { useEffect, useState } from 'react'
import { api } from '../../../lib/api'
import type { ToolLog, TraceDetail, TraceSummary } from '../../../types/api'
import { SectionHeader } from '../components/SectionHeader'
import { InfoPanel } from '../components/InfoPanel'

const TRACE_STEPS = [
  { time: '10:21:43', label: 'Intent Detection', detail: 'refund_request + delayed_shipment', meta: 'Conf: 0.92', color: '#8b5cf6' },
  { time: '10:21:44', label: 'Tool Call: get_order(SP-1024)', detail: null, meta: 'Success 330ms', color: '#10b981' },
  { time: '10:21:45', label: 'Tool Call: get_shipment_status(TH0123456789)', detail: null, meta: 'Success 418ms', color: '#10b981' },
  { time: '10:21:46', label: 'RAG Search: Refund Policy Section 3.2', detail: null, meta: 'Top-3 Similarity: 0.89', color: '#3b82f6' },
  { time: '10:21:47', label: 'Decision: requires_human_approval', detail: 'Reason: amount > threshold', meta: null, color: '#f59e0b' },
  { time: '10:21:48', label: 'Response Generated', detail: null, meta: 'Tokens: 256', color: '#ef4444' },
]

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
              <span>Trace ID: <strong>{selectedTrace?.id ?? 'TRC-2024-05-16-000124'}</strong></span>
              <span className="status-pill" style={{ background: '#dcfce7', color: '#15803d' }}>
                {selectedTrace?.status ?? 'completed'}
              </span>
            </div>
            <div className="ai-timeline">
              {TRACE_STEPS.map((step, i) => (
                <div key={i} className="ai-timeline-item">
                  <div className="ai-timeline-left">
                    <span className="ai-timeline-dot" style={{ background: step.color }} />
                    {i < TRACE_STEPS.length - 1 && <span className="ai-timeline-line" />}
                  </div>
                  <div className="ai-timeline-body">
                    <div className="ai-timeline-row">
                      <span className="ai-timeline-time">{step.time}</span>
                      <strong className="ai-timeline-label">{step.label}</strong>
                      {step.meta && <span className="ai-timeline-meta" style={{ color: step.color }}>{step.meta}</span>}
                    </div>
                    {step.detail && <p className="ai-timeline-detail">{step.detail}</p>}
                  </div>
                </div>
              ))}
            </div>
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
