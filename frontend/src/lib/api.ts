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
  OrderSummary,
  ProactiveAlert,
  RefundRequest,
  RefundRequestDetail,
  ShipmentDetail,
  ToolLog,
  TraceDetail,
  TraceSummary,
} from '../types/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
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
  getAttachmentDownloadUrl: (attachmentId: string) =>
    request<AttachmentPresignResponse>(`/attachments/${attachmentId}/presign-download`),
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
}
