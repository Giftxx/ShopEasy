import { useEffect, useState } from 'react'
import { api } from '../../../lib/api'

// ── Types ─────────────────────────────────────────────────────────────────────

type NodeType = 'llm_router' | 'router' | 'lookup' | 'policy' | 'validate' | 'risk' | 'generate' | 'alert' | 'ingest'

type WFNode = {
  id: string
  label: string
  type: NodeType
}

type Workflow = {
  id: string
  name: string
  description: string
  color: string
  nodes: WFNode[]
}

// ── Live Run Types ────────────────────────────────────────────────────────────

type ToolCall = { agent: string; tool: string; status: string; latency_ms: number | null }
type RecentRun = {
  trace_id: string
  workflow_name: string
  intent: string
  confidence: number | null
  status: string
  requires_human_approval: boolean
  duration_ms: number | null
  started_at: string | null
  tools: ToolCall[]
}

// ── Constants ─────────────────────────────────────────────────────────────────

const NODE_STYLE: Record<NodeType, { color: string; bg: string }> = {
  llm_router: { color: '#f5a878', bg: '#fff7f2' },
  router:     { color: '#89b4f7', bg: '#eef4ff' },
  lookup:     { color: '#76c9a0', bg: '#f0fbf6' },
  policy:     { color: '#b8a0e8', bg: '#f5f2ff' },
  validate:   { color: '#f0c870', bg: '#fffdf0' },
  risk:       { color: '#f09090', bg: '#fff5f5' },
  generate:   { color: '#f5a878', bg: '#fff7f2' },
  alert:      { color: '#f0d878', bg: '#fdfef0' },
  ingest:     { color: '#a8b8cc', bg: '#f7f9fc' },
}

const NODE_PALETTE: { label: string; type: NodeType; note?: string }[] = [
  { label: 'LLM Router',        type: 'llm_router', note: 'LLM classifies intent' },
  { label: 'Lookup Shipment',   type: 'lookup'   },
  { label: 'Lookup Order',      type: 'lookup'   },
  { label: 'Check Policy',      type: 'policy'   },
  { label: 'RAG Search',        type: 'policy'   },
  { label: 'Validate Refund',   type: 'validate' },
  { label: 'Risk Assessment',   type: 'risk'     },
  { label: 'Generate Response', type: 'generate' },
  { label: 'Send Alert',        type: 'alert'    },
  { label: 'Event Ingestion',   type: 'ingest'   },
]

const WF_COLORS = ['#89b4f7', '#f5a878', '#f08898', '#76c9a0', '#b8a0e8', '#f0c870', '#a8b8cc', '#f5b8d8']

const INITIAL_WORKFLOWS: Workflow[] = [
  {
    id: 'wf01',
    name: 'WF01 · Tracking',
    description: 'LLM routes → shipment lookup → Ollama response',
    color: '#89b4f7',
    nodes: [
      { id: 'wf01-n1', label: 'LLM Router',        type: 'llm_router' },
      { id: 'wf01-n2', label: 'Resolve Context',   type: 'lookup'     },
      { id: 'wf01-n3', label: 'Memory Retrieval',  type: 'lookup'     },
      { id: 'wf01-n4', label: 'Plan Response',     type: 'router'     },
      { id: 'wf01-n5', label: 'Fetch Shipments',   type: 'lookup'     },
      { id: 'wf01-n6', label: 'Generate Response', type: 'generate'   },
    ],
  },
  {
    id: 'wf02',
    name: 'WF02 · Refund',
    description: 'LLM routes → evidence eval → RAG policy → Ollama response',
    color: '#f5a878',
    nodes: [
      { id: 'wf02-n1', label: 'LLM Router',        type: 'llm_router' },
      { id: 'wf02-n2', label: 'Resolve Context',   type: 'lookup'     },
      { id: 'wf02-n3', label: 'Memory Retrieval',  type: 'lookup'     },
      { id: 'wf02-n4', label: 'Validate Refund',   type: 'validate'   },
      { id: 'wf02-n5', label: 'RAG Policy Search', type: 'policy'     },
      { id: 'wf02-n6', label: 'Risk Assessment',   type: 'risk'       },
      { id: 'wf02-n7', label: 'Generate Response', type: 'generate'   },
    ],
  },
  {
    id: 'wf03',
    name: 'WF03 · Proactive',
    description: 'Event-driven shipment delay alerts (no LLM routing — event-triggered)',
    color: '#f08898',
    nodes: [
      { id: 'wf03-n1', label: 'Event Ingestion',   type: 'ingest'   },
      { id: 'wf03-n2', label: 'Risk Assessment',   type: 'risk'     },
      { id: 'wf03-n3', label: 'Send Alert',        type: 'alert'    },
    ],
  },
]

// ── Helpers ───────────────────────────────────────────────────────────────────

function uid() {
  return `n-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`
}

function wfUid() {
  return `wf-${Date.now().toString(36)}`
}

// ── Sub-components ────────────────────────────────────────────────────────────

const WF_LABEL: Record<string, string> = {
  workflow_01_track_shipment: 'WF01 · Tracking',
  workflow_02_refund:         'WF02 · Refund',
  workflow_03_proactive:      'WF03 · Proactive',
}

const WF_COLOR: Record<string, string> = {
  workflow_01_track_shipment: '#89b4f7',
  workflow_02_refund:         '#f5a878',
  workflow_03_proactive:      '#f08898',
}

const STATUS_COLOR: Record<string, string> = {
  success:   '#76c9a0',
  failed:    '#f09090',
  completed: '#89b4f7',
  fallback:  '#f0c870',
  partial:   '#f0c870',
}

const TOOL_COLOR: Record<string, string> = {
  detect_intent:       '#b8a0e8',
  get_shipments:       '#76c9a0',
  validate_refund:     '#f0c870',
  search_policy:       '#b8a0e8',
  assess_risk:         '#f09090',
  generate_response:   '#f5a878',
  send_alert:          '#f0d878',
  ingest_event:        '#a8b8cc',
  process_cancellation:'#89b4f7',
}

function RunCard({ run, expanded, onToggle }: { run: RecentRun; expanded: boolean; onToggle: () => void }) {
  const wfLabel = WF_LABEL[run.workflow_name] ?? run.workflow_name
  const wfColor = WF_COLOR[run.workflow_name] ?? '#94a3b8'
  const stColor = STATUS_COLOR[run.status] ?? '#94a3b8'
  const ts = run.started_at ? new Date(run.started_at).toLocaleString('th-TH', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: 'short' }) : '—'

  return (
    <div className="ws-run-card" style={{ borderLeftColor: wfColor }}>
      <button type="button" className="ws-run-card__head" onClick={onToggle}>
        <div className="ws-run-card__meta">
          <span className="ws-run-badge" style={{ background: `${wfColor}22`, color: wfColor }}>{wfLabel}</span>
          <span className="ws-run-intent">{run.intent}</span>
          {run.confidence != null && (
            <span className="ws-run-conf">{Math.round(run.confidence * 100)}%</span>
          )}
        </div>
        <div className="ws-run-card__right">
          {run.requires_human_approval && (
            <span className="ws-run-human" title="Requires human approval">Human Review</span>
          )}
          <span className="ws-run-status" style={{ color: stColor }}>● {run.status}</span>
          {run.duration_ms != null && (
            <span className="ws-run-dur">{run.duration_ms < 1000 ? `${run.duration_ms}ms` : `${(run.duration_ms / 1000).toFixed(1)}s`}</span>
          )}
          <span className="ws-run-ts">{ts}</span>
          <span className="ws-run-chevron">{expanded ? '▲' : '▼'}</span>
        </div>
      </button>

      {expanded && (
        <div className="ws-run-tools">
          <div className="ws-run-tools__label">Tools called automatically by agent:</div>
          <div className="ws-run-flow">
            {run.tools.length === 0 && <span className="ws-run-tools__empty">No tool logs recorded</span>}
            {run.tools.map((t, i) => {
              const tc = TOOL_COLOR[t.tool] ?? '#94a3b8'
              return (
                <div key={i} className="ws-run-flow__item">
                  {i > 0 && <span className="ws-run-flow__arrow">→</span>}
                  <div className="ws-run-tool" style={{ borderTopColor: tc }}>
                    <span className="ws-run-tool__name" style={{ color: tc }}>{t.tool}</span>
                    <span className="ws-run-tool__agent">{t.agent}</span>
                    <span className="ws-run-tool__lat" style={{ color: t.status === 'failed' ? '#ef4444' : '#94a3b8' }}>
                      {t.status === 'failed' ? 'failed' : t.latency_ms != null ? `${t.latency_ms}ms` : '—'}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
          <div className="ws-run-tid">trace: {run.trace_id}</div>
        </div>
      )}
    </div>
  )
}

// ── Component ─────────────────────────────────────────────────────────────────

export function WorkspaceTab() {
  const [workflows, setWorkflows] = useState<Workflow[]>(INITIAL_WORKFLOWS)
  const [selectedId, setSelectedId] = useState<string>('wf01')
  const [showPalette, setShowPalette] = useState(false)
  const [showAddWf, setShowAddWf] = useState(false)
  const [newWfName, setNewWfName] = useState('')
  const [newWfDesc, setNewWfDesc] = useState('')

  const [testShipmentId, setTestShipmentId] = useState('')
  const [testResult, setTestResult] = useState<string | null>(null)
  const [testLoading, setTestLoading] = useState(false)
  const [testError, setTestError] = useState<string | null>(null)

  // ── Live runs ──────────────────────────────────────────────────────────────
  const [runs, setRuns] = useState<RecentRun[]>([])
  const [runsLoading, setRunsLoading] = useState(true)
  const [expandedRun, setExpandedRun] = useState<string | null>(null)
  const [filterWf, setFilterWf] = useState<string>('all')

  useEffect(() => {
    setRunsLoading(true)
    api.getRecentRuns(20)
      .then(data => { setRuns(data); if (data.length > 0) setExpandedRun(data[0].trace_id) })
      .catch(() => {})
      .finally(() => setRunsLoading(false))
  }, [])

  const filteredRuns = filterWf === 'all' ? runs : runs.filter(r => r.workflow_name === filterWf)

  const selectedWf = workflows.find(w => w.id === selectedId) ?? workflows[0]

  // ── Workflow CRUD ──────────────────────────────────────────────────────────

  function handleAddWorkflow() {
    const name = newWfName.trim()
    if (!name) return
    const colorIdx = workflows.length % WF_COLORS.length
    const wf: Workflow = {
      id: wfUid(),
      name,
      description: newWfDesc.trim() || 'Custom workflow',
      color: WF_COLORS[colorIdx],
      nodes: [],
    }
    setWorkflows(ws => [...ws, wf])
    setSelectedId(wf.id)
    setNewWfName('')
    setNewWfDesc('')
    setShowAddWf(false)
    setShowPalette(false)
  }

  function handleRemoveWorkflow(id: string) {
    if (!confirm('Remove this workflow from the workspace? This does not affect the running backend.')) return
    const remaining = workflows.filter(w => w.id !== id)
    setWorkflows(remaining)
    if (selectedId === id) setSelectedId(remaining[0]?.id ?? '')
    setShowPalette(false)
  }

  // ── Node CRUD ──────────────────────────────────────────────────────────────

  function handleAddNode(template: { label: string; type: NodeType }) {
    setWorkflows(ws =>
      ws.map(w =>
        w.id !== selectedId ? w : { ...w, nodes: [...w.nodes, { id: uid(), label: template.label, type: template.type }] }
      )
    )
    setShowPalette(false)
  }

  function handleRemoveNode(nodeId: string) {
    setWorkflows(ws =>
      ws.map(w =>
        w.id !== selectedId ? w : { ...w, nodes: w.nodes.filter(n => n.id !== nodeId) }
      )
    )
  }

  // ── Test flow ──────────────────────────────────────────────────────────────

  async function handleTestFlow() {
    setTestLoading(true)
    setTestResult(null)
    setTestError(null)
    try {
      const res = await api.triggerProactiveDelay(testShipmentId)
      setTestResult(
        JSON.stringify({ workflow: res.workflow_name, alert_id: res.state_snapshot?.alert_id, response: res.response_text }, null, 2)
      )
      // Refresh runs after test
      const data = await api.getRecentRuns(20)
      setRuns(data)
      if (data.length > 0) setExpandedRun(data[0].trace_id)
    } catch (err) {
      setTestError(err instanceof Error ? err.message : 'Trigger failed')
    } finally {
      setTestLoading(false)
    }
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="ws-shell">

      {/* Workflow list sidebar */}
      <div className="ws-sidebar">
        <div className="ws-sidebar__head">Workflows</div>

        {workflows.map(wf => (
          <button
            key={wf.id}
            type="button"
            className={`ws-wf-item${selectedId === wf.id ? ' is-active' : ''}`}
            onClick={() => { setSelectedId(wf.id); setShowPalette(false) }}
          >
            <span className="ws-wf-dot" style={{ background: wf.color }} />
            <span className="ws-wf-name">{wf.name}</span>
            <span className="ws-wf-badge">{wf.nodes.length}</span>
          </button>
        ))}

        {showAddWf ? (
          <div className="ws-add-wf-form">
            <input
              className="ws-add-wf-input"
              value={newWfName}
              onChange={e => setNewWfName(e.target.value)}
              placeholder="WF04 · Escalation"
              onKeyDown={e => e.key === 'Enter' && handleAddWorkflow()}
              autoFocus
            />
            <input
              className="ws-add-wf-input"
              value={newWfDesc}
              onChange={e => setNewWfDesc(e.target.value)}
              placeholder="Description (optional)"
              onKeyDown={e => e.key === 'Enter' && handleAddWorkflow()}
            />
            <div className="ws-add-wf-btns">
              <button type="button" className="ws-add-wf-confirm" onClick={handleAddWorkflow}>Add</button>
              <button type="button" className="ws-add-wf-cancel" onClick={() => { setShowAddWf(false); setNewWfName(''); setNewWfDesc('') }}>Cancel</button>
            </div>
          </div>
        ) : (
          <button type="button" className="ws-add-wf-btn" onClick={() => setShowAddWf(true)}>
            + Add Workflow
          </button>
        )}

        <p className="ws-sidebar__note">
          Agent เลือก tool เองอัตโนมัติผ่าน LangGraph — Workspace นี้แสดง tool calls จริงจากทุก run
        </p>
      </div>

      {/* Main area — split: diagram top, live runs bottom */}
      <div className="ws-main">

        {/* ── Flow canvas ───────────────────────────────────────────── */}
        <div className="ws-canvas">

          {/* Header */}
          <div className="ws-canvas__head">
            <div className="ws-canvas__head-left">
              <span className="ws-canvas__name" style={{ borderLeftColor: selectedWf.color }}>
                {selectedWf.name}
              </span>
              <span className="ws-canvas__desc">{selectedWf.description}</span>
            </div>
            {workflows.length > 1 && (
              <button type="button" className="ws-del-wf-btn" onClick={() => handleRemoveWorkflow(selectedId)}>
                Remove Workflow
              </button>
            )}
          </div>

          {/* Flow nodes */}
          <div className="ws-flow-wrap">
            {selectedWf.nodes.length === 0 && (
              <p className="ws-flow-empty">No nodes yet. Click "+ Add Node" to build this workflow.</p>
            )}
            {selectedWf.nodes.length > 0 && (
              <div className="ws-flow">
                {selectedWf.nodes.map((node, i) => (
                  <div key={node.id} className="ws-flow__item">
                    {i > 0 && <span className="ws-arrow" aria-hidden>&#8594;</span>}
                    <div
                      className="ws-node"
                      style={{ borderTopColor: NODE_STYLE[node.type].color, background: NODE_STYLE[node.type].bg }}
                    >
                      <button
                        type="button"
                        className="ws-node__del"
                        onClick={() => handleRemoveNode(node.id)}
                        title="Remove node"
                      >
                        &times;
                      </button>
                      <span className="ws-node__label">{node.label}</span>
                      <span className="ws-node__type" style={{ color: NODE_STYLE[node.type].color }}>
                        {node.type}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <button
              type="button"
              className={`ws-add-node-btn${showPalette ? ' is-active' : ''}`}
              onClick={() => setShowPalette(v => !v)}
            >
              {showPalette ? '− Close' : '+ Add Node'}
            </button>
          </div>

          {/* Node palette */}
          {showPalette && (
            <div className="ws-palette">
              <div className="ws-palette__head">Select a node type to append to the workflow</div>
              <div className="ws-palette__grid">
                {NODE_PALETTE.map(n => (
                  <button
                    key={n.label}
                    type="button"
                    className="ws-palette-node"
                    style={{ borderColor: `${NODE_STYLE[n.type].color}55` }}
                    onClick={() => handleAddNode(n)}
                  >
                    <span className="ws-palette-node__dot" style={{ background: NODE_STYLE[n.type].color }} />
                    <span style={{ color: NODE_STYLE[n.type].color, fontWeight: 700 }}>{n.label}</span>
                    <span className="ws-palette-node__type">{n.note ?? n.type}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Test panel */}
          <div className="ws-test">
            <div className="ws-test__head">
              <span className="ws-test__title">Manual Test · WF03 Proactive</span>
              <span className="ws-test__sub">ยิง event จริงผ่าน LangGraph pipeline — agent เลือก tool เอง</span>
            </div>
            <div className="ws-test__bar">
              <input
                className="ws-test__input"
                value={testShipmentId}
                onChange={e => setTestShipmentId(e.target.value)}
                placeholder="Shipment ID เช่น SHP-9002"
              />
              <button
                type="button"
                className="ws-test__run"
                onClick={() => void handleTestFlow()}
                disabled={testLoading || !testShipmentId.trim()}
              >
                {testLoading ? 'Running...' : '▶ Run'}
              </button>
            </div>
            {testError && <p className="ws-test__error">{testError}</p>}
            {testResult && <pre className="ws-test__result">{testResult}</pre>}
          </div>
        </div>

        {/* ── Live Agent Runs ──────────────────────────────────────── */}
        <div className="ws-runs">
          <div className="ws-runs__head">
            <div className="ws-runs__title">
              Live Agent Runs
              <span className="ws-runs__sub">— tool calls ที่ agent เลือกเองอัตโนมัติ</span>
            </div>
            <div className="ws-runs__filters">
              {(['all', 'workflow_01_track_shipment', 'workflow_02_refund', 'workflow_03_proactive'] as const).map(wf => (
                <button
                  key={wf}
                  type="button"
                  className={`ws-runs__filter${filterWf === wf ? ' is-active' : ''}`}
                  onClick={() => setFilterWf(wf)}
                >
                  {wf === 'all' ? 'All' : WF_LABEL[wf]}
                </button>
              ))}
            </div>
          </div>

          <div className="ws-runs__list">
            {runsLoading && <p className="ws-runs__loading">Loading runs...</p>}
            {!runsLoading && filteredRuns.length === 0 && (
              <p className="ws-runs__empty">No runs found.</p>
            )}
            {filteredRuns.map(run => (
              <RunCard
                key={run.trace_id}
                run={run}
                expanded={expandedRun === run.trace_id}
                onToggle={() => setExpandedRun(v => v === run.trace_id ? null : run.trace_id)}
              />
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}