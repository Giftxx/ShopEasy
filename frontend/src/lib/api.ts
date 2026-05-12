import type {
  Approval,
  CaseDetail,
  AttachmentConfirmRequest,
  AttachmentPresignRequest,
  AttachmentPresignResponse,
  CaseSummary,
  ChatRequest,
  ChatResponse,
  ConversationDetail,
  ConversationSummary,
  CustomerRefundCreateRequest,
  CustomerRefundCreateResponse,
  LoginRequest,
  LoginResponse,
  OrderSummary,
  Policy,
  PolicyCreate,
  PolicyDetail,
  PolicyDownloadUrl,
  PolicySearchResult,
  ProactiveAlert,
  RefundRequest,
  RefundRequestDetail,
  ShipmentDetail,
  ToolLog,
  TraceDetail,
  TraceSummary,
  User,
} from '../types/api'
import { readSession } from './session'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const session = readSession()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((init?.headers as Record<string, string>) ?? {}),
  }
  if (session?.token) {
    headers['Authorization'] = `Bearer ${session.token}`
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Request failed: ${response.status}`)
  }

  return response.json() as Promise<T>
}

async function uploadToPresignedUrl(uploadUrl: string, file: File): Promise<void> {
  const response = await fetch(uploadUrl, {
    method: 'PUT',
    headers: {
      'Content-Type': file.type || 'application/octet-stream',
    },
    body: file,
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Upload failed: ${response.status}`)
  }
}

function withQuery(path: string, query: Record<string, string | number | undefined | null>): string {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && String(value).trim() !== '') {
      params.set(key, String(value))
    }
  }
  const queryString = params.toString()
  return queryString ? `${path}?${queryString}` : path
}

export const api = {
  login: (payload: LoginRequest) =>
    request<LoginResponse>('/auth/login', { method: 'POST', body: JSON.stringify(payload) }),
  googleLogin: (payload: { credential: string }) =>
    request<LoginResponse>('/auth/google', { method: 'POST', body: JSON.stringify(payload) }),
  getMe: () => request<User>('/auth/me'),
  getHealth: () => request<{ status: string }>('/health'),
  sendChat: (payload: ChatRequest) =>
    request<ChatResponse>('/chat', { method: 'POST', body: JSON.stringify(payload) }),
  getCustomerOrders: (customerId: string) =>
    request<OrderSummary[]>(`/data/customers/${customerId}/orders`),
  getCustomerShipments: (customerId: string) =>
    request<ShipmentDetail[]>(`/data/customers/${customerId}/shipments`),
  getShipment: (shipmentId: string) => request<ShipmentDetail>(`/data/shipments/${shipmentId}`),
  getCustomerConversations: (customerId: string) =>
    request<ConversationSummary[]>(`/data/customers/${customerId}/conversations`),
  getConversation: (conversationId: string) =>
    request<ConversationDetail>(`/data/conversations/${conversationId}`),
  getCustomerRefundRequests: (customerId: string) =>
    request<RefundRequest[]>(`/data/customers/${customerId}/refund-requests`),
  getCustomerRefundRequestDetail: (customerId: string, refundRequestId: string) =>
    request<RefundRequestDetail>(`/data/customers/${customerId}/refund-requests/${refundRequestId}`),
  getCustomerProactiveAlerts: (customerId: string) =>
    request<ProactiveAlert[]>(`/data/customers/${customerId}/proactive-alerts`),
  createCustomerRefundRequest: (customerId: string, payload: CustomerRefundCreateRequest) =>
    request<CustomerRefundCreateResponse>(`/data/customers/${customerId}/refund-requests`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  presignAttachmentUpload: (payload: AttachmentPresignRequest) =>
    request<AttachmentPresignResponse>('/attachments/presign-upload', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  uploadAttachmentFile: (uploadUrl: string, file: File) => uploadToPresignedUrl(uploadUrl, file),
  confirmAttachmentUpload: (payload: AttachmentConfirmRequest) =>
    request<RefundRequestDetail['attachments'][number]>('/attachments/confirm-upload', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  uploadAttachmentDirect: async (
    file: File,
    refundRequestId: string,
    evidenceGroup: string,
    description?: string,
  ): Promise<RefundRequestDetail['attachments'][number]> => {
    const session = readSession()
    const formData = new FormData()
    formData.append('file', file)
    formData.append('refund_request_id', refundRequestId)
    formData.append('evidence_group', evidenceGroup)
    if (description) formData.append('description', description)
    const response = await fetch(`${API_BASE}/attachments/upload-direct`, {
      method: 'POST',
      headers: session?.token ? { Authorization: `Bearer ${session.token}` } : {},
      body: formData,
    })
    if (!response.ok) {
      const text = await response.text()
      throw new Error(text || `Upload failed: ${response.status}`)
    }
    return response.json() as Promise<RefundRequestDetail['attachments'][number]>
  },
  getAttachmentDownloadUrl: (attachmentId: string) =>
    request<AttachmentPresignResponse>(`/attachments/${attachmentId}/presign-download`),
  getAttachmentDirectUrl: (attachmentId: string): string =>
    `${API_BASE}/attachments/${attachmentId}/download`,
  getCases: () => request<CaseSummary[]>('/admin/cases'),
  getCaseDetail: (caseId: string) => request<CaseDetail>(`/admin/cases/${caseId}`),
  getApprovals: () => request<Approval[]>('/admin/approvals'),
  getRefundRequests: () => request<RefundRequest[]>('/admin/refund-requests'),
  getProactiveAlerts: () => request<ProactiveAlert[]>('/admin/proactive-alerts'),
  approveApproval: (approvalId: string, reason: string) =>
    request<Approval>(`/admin/approvals/${approvalId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),
  rejectApproval: (approvalId: string, reason: string) =>
    request<Approval>(`/admin/approvals/${approvalId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),
  closeCase: (caseId: string, reason: string) =>
    request<CaseSummary>(`/admin/cases/${caseId}/close`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),
  resolveAlert: (alertId: string, reason: string) =>
    request<ProactiveAlert>(`/admin/proactive-alerts/${alertId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),
  getAgentTraces: (filters?: {
    workflow_name?: string
    status?: string
    intent?: string
    case_id?: string
    limit?: number
  }) =>
    request<TraceSummary[]>(
      withQuery('/ai/agent-traces', {
        workflow_name: filters?.workflow_name,
        status: filters?.status,
        intent: filters?.intent,
        case_id: filters?.case_id,
        limit: filters?.limit,
      }),
    ),
  getAgentTrace: (traceId: string) => request<TraceDetail>(`/ai/agent-traces/${traceId}`),
  getToolLogs: (filters?: {
    trace_id?: string
    agent_name?: string
    tool_name?: string
    status?: string
    limit?: number
  }) =>
    request<ToolLog[]>(
      withQuery('/ai/tool-logs', {
        trace_id: filters?.trace_id,
        agent_name: filters?.agent_name,
        tool_name: filters?.tool_name,
        status: filters?.status,
        limit: filters?.limit,
      }),
    ),
  triggerProactiveDelay: (shipmentId: string) =>
    request<{ workflow_name: string; response_text: string; state_snapshot: Record<string, unknown> }>(
      '/events/proactive-delay',
      {
        method: 'POST',
        body: JSON.stringify({ shipment_id: shipmentId, event_type: 'shipment_no_update_48h' }),
      },
    ),
  // ── Policy / RAG ──────────────────────────────────────────────────────────
  getPolicies: () => request<Policy[]>('/ai/policies'),
  getPolicyDetail: (policyId: string) => request<PolicyDetail>(`/ai/policies/${policyId}`),
  createPolicy: (payload: PolicyCreate) =>
    request<PolicyDetail>('/ai/policies', { method: 'POST', body: JSON.stringify(payload) }),
  updatePolicyContent: (policyId: string, content: string) =>
    request<PolicyDetail>(`/ai/policies/${policyId}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    }),
  deletePolicy: (policyId: string) =>
    request<void>(`/ai/policies/${policyId}`, { method: 'DELETE' }),
  searchPolicies: (query: string, limit = 5, category?: string) =>
    request<PolicySearchResult[]>(
      withQuery('/ai/policies/search', { q: query, limit, category }),
    ),
  downloadPolicyFile: (policyId: string) =>
    request<PolicyDownloadUrl>(`/ai/policies/${policyId}/download`),
  uploadPolicyDocument: async (
    file: File,
    title: string,
    category: string,
    version: string,
  ): Promise<PolicyDetail> => {
    const session = readSession()
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', title)
    formData.append('category', category)
    formData.append('version', version)
    const response = await fetch(`${API_BASE}/ai/policies/upload`, {
      method: 'POST',
      headers: session?.token ? { Authorization: `Bearer ${session.token}` } : {},
      body: formData,
    })
    if (!response.ok) {
      const text = await response.text()
      throw new Error(text || `Upload failed: ${response.status}`)
    }
    return response.json() as Promise<PolicyDetail>
  },
  // ── Analytics / Evaluation ────────────────────────────────────────────────
  getAnalyticsStats: () => request<{
    total_conversations: number
    auto_resolution_rate: number
    handoff_rate: number
    avg_response_time: string
    total_traces: number
  }>('/ai/analytics/stats'),
  getAnalyticsTrend: (days = 12) =>
    request<{ date: string; count: number }[]>(withQuery('/ai/analytics/trend', { days })),
  getAnalyticsIntents: () =>
    request<{ label: string; pct: number; count: number }[]>('/ai/analytics/intents'),
  getEvalSummary: () => request<{
    total_traces: number
    success: number
    failed: number
    partial: number
    success_pct: number
    failed_pct: number
    partial_pct: number
    last_run: string | null
  }>('/ai/analytics/eval-summary'),
  getRecentRuns: (limit = 10) =>
    request<{
      trace_id: string
      workflow_name: string
      intent: string
      confidence: number | null
      status: string
      requires_human_approval: boolean
      duration_ms: number | null
      started_at: string | null
      tools: { agent: string; tool: string; status: string; latency_ms: number | null }[]
    }[]>(withQuery('/ai/workspace/recent-runs', { limit })),
}
