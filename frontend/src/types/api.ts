export type Role = 'customer' | 'admin' | 'ai-engineer'

export type User = {
  id: string
  name: string
  email: string
  role: string
  status: string
  created_at?: string | null
  updated_at?: string | null
}

export type LoginRequest = {
  email: string
  password: string
}

export type LoginResponse = {
  user: User
  access_token: string
  token_type: string
  customer_id?: string | null
}

export type ChatRequest = {
  customer_id: string
  conversation_id: string
  message: string
}

export type ShipmentSummary = {
  order_id: string
  seller_name: string
  item_names: string[]
  shipment_status: string
  note: string
}

export type ChatResponse = {
  workflow_name: string
  intent: string
  response_text: string
  active_shipments: ShipmentSummary[]
  state_snapshot: Record<string, unknown>
}

export type OrderSummary = {
  id: string
  customer_id: string
  seller_id: string
  seller_name?: string | null
  order_status: string
  payment_status?: string | null
  total_amount?: number | null
  currency: string
  promised_delivery_date?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export type OrderItem = {
  id: string
  product_name?: string | null
  sku?: string | null
  quantity?: number | null
  unit_price?: number | null
  created_at?: string | null
}

export type ShipmentEvent = {
  id: string
  event_type?: string | null
  event_message?: string | null
  location?: string | null
  event_time?: string | null
  raw_payload?: Record<string, unknown> | null
  created_at?: string | null
}

export type ShipmentDetail = {
  id: string
  order_id: string
  carrier?: string | null
  tracking_no?: string | null
  shipment_status?: string | null
  eta?: string | null
  last_update?: string | null
  delay_risk_score: number
  created_at?: string | null
  updated_at?: string | null
  events: ShipmentEvent[]
}

export type ConversationSummary = {
  id: string
  customer_id: string
  channel: string
  status: string
  latest_intent?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export type Message = {
  id: string
  conversation_id: string
  sender_type: string
  sender_id?: string | null
  content: string
  metadata_json?: Record<string, unknown> | null
  created_at?: string | null
}

export type ConversationDetail = ConversationSummary & {
  messages: Message[]
}

export type CaseSummary = {
  id: string
  customer_id: string
  order_id?: string | null
  case_type?: string | null
  priority?: string | null
  status?: string | null
  ai_summary?: string | null
  resolution_note?: string | null
  assigned_role?: string | null
  created_by?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export type Approval = {
  id: string
  case_id: string
  approval_type: string
  requested_action?: string | null
  amount?: number | null
  currency?: string | null
  risk_level?: string | null
  status?: string | null
  ai_reason?: string | null
  review_note?: string | null
  policy_citation?: Record<string, unknown> | null
  created_at?: string | null
}

export type RefundRequest = {
  id: string
  order_id: string
  customer_id: string
  case_id?: string | null
  reason?: string | null
  requested_resolution?: string | null
  eligibility_status?: string | null
  risk_score: number
  ai_recommendation?: string | null
  status?: string | null
  evidence_count?: number | null
  created_at?: string | null
  updated_at?: string | null
}

export type EvidenceItem = {
  evidence_group: string
  description?: string | null
  file_name: string
  mime_type: string
}

export type AttachmentPresignRequest = {
  file_name: string
  content_type: string
  refund_request_id: string
  evidence_group: string
}

export type AttachmentPresignResponse = {
  upload_url: string
  object_name: string
}

export type AttachmentConfirmRequest = {
  object_name: string
  file_name: string
  content_type: string
  refund_request_id: string
  evidence_group: string
  description?: string | null
  file_size_bytes?: number | null
}

export type CustomerRefundCreateRequest = {
  conversation_id: string
  order_id: string
  reason: string
  requested_resolution: string
  evidence_items: EvidenceItem[]
}

export type CustomerRefundCreateResponse = {
  workflow_name: string
  assistant_message: string
  trace_id?: string | null
  case_id?: string | null
  refund_request: RefundRequest
}

export type RefundAttachment = {
  id: string
  evidence_group?: string | null
  description?: string | null
  file_name?: string | null
  mime_type?: string | null
  object_key: string
  upload_status?: string | null
  created_at?: string | null
}

export type RefundRequestDetail = RefundRequest & {
  attachments: RefundAttachment[]
}

export type AdminRefundRequestDetail = RefundRequest & {
  attachments: RefundAttachment[]
}

export type ProactiveAlert = {
  id: string
  order_id?: string | null
  shipment_id?: string | null
  alert_type?: string | null
  risk_score?: number | null
  status?: string | null
  recommended_action?: string | null
  resolution_note?: string | null
  message_draft?: string | null
  case_id?: string | null
  created_at?: string | null
  resolved_at?: string | null
}

export type TraceSummary = {
  id: string
  conversation_id?: string | null
  case_id?: string | null
  workflow_name?: string | null
  intent?: string | null
  confidence?: number | null
  status?: string | null
  requires_human_approval: boolean
  started_at?: string | null
  ended_at?: string | null
}

export type TraceConversationContext = {
  id: string
  customer_id: string
  customer_name?: string | null
  channel: string
  status: string
  latest_intent?: string | null
}

export type TraceRefundContext = {
  id: string
  order_id: string
  customer_id: string
  case_id?: string | null
  reason?: string | null
  requested_resolution?: string | null
  eligibility_status?: string | null
  risk_score: number
  ai_recommendation?: string | null
  status?: string | null
  attachments: RefundAttachment[]
}

export type TraceCaseContext = {
  id: string
  customer_id: string
  order_id?: string | null
  case_type?: string | null
  priority?: string | null
  status?: string | null
  ai_summary?: string | null
  resolution_note?: string | null
  refund_requests: TraceRefundContext[]
  attachments: RefundAttachment[]
}

export type TraceBusinessContext = {
  conversation?: TraceConversationContext | null
  case?: TraceCaseContext | null
  active_order_ids: string[]
  active_shipment_ids: string[]
  refund_request_id?: string | null
  alert_id?: string | null
}

export type ToolLog = {
  id: string
  trace_id: string
  agent_name?: string | null
  tool_name?: string | null
  input_payload?: Record<string, unknown> | null
  output_payload?: Record<string, unknown> | null
  status?: string | null
  latency_ms?: number | null
  error_message?: string | null
  created_at?: string | null
}

export type TraceDetail = TraceSummary & {
  final_response?: string | null
  state_snapshot?: Record<string, unknown> | null
  tool_logs: ToolLog[]
  business_context?: TraceBusinessContext | null
}

export type CaseDetail = CaseSummary & {
  approvals: Approval[]
  refund_requests: AdminRefundRequestDetail[]
  attachments: RefundAttachment[]
}

export type PolicyChunk = {
  id: string
  chunk_index: number | null
  chunk_text: string | null
  heading: string | null
  tags: string[] | null
  page_number: number | null
}

export type Policy = {
  id: string
  title: string | null
  category: string | null
  version: string | null
  content: string | null
  status: string | null
  source_filename: string | null
  file_size_bytes: number | null
  chunk_count: number
  created_at: string | null
  updated_at: string | null
}

export type PolicyDetail = Policy & {
  chunks: PolicyChunk[]
}

export type PolicyCreate = {
  title: string
  category: string
  version: string
  content: string
}

export type PolicySearchResult = {
  policy_id: string
  policy_title: string
  category: string
  chunk_index: number | null
  chunk_text: string
  heading: string
  tags: string[]
  page_number: number | null
}

export type PolicyDownloadUrl = {
  url: string
  filename: string
}
