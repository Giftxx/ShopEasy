import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { Sidebar } from '../../components/Sidebar'
import { api } from '../../lib/api'
import { clearSession, readSession } from '../../lib/session'
import type {
  ConversationSummary,
  OrderSummary,
  ProactiveAlert,
  RefundRequest,
  RefundRequestDetail,
  ShipmentDetail,
} from '../../types/api'

type CustomerTab = 'assistant' | 'orders' | 'shipments' | 'refund' | 'alerts'

type ChatMessage = { role: 'user' | 'ai'; text: string; time: string }

type RefundUploadDraft = {
  file: File
  evidenceGroup: string
  description?: string | null
}

const navItems: { key: CustomerTab; label: string; icon: string }[] = [
  { key: 'assistant', label: 'แชทกับ AI', icon: '✦' },
  { key: 'orders', label: 'คำสั่งซื้อของฉัน', icon: '▣' },
  { key: 'shipments', label: 'การจัดส่งของฉัน', icon: '▱' },
  { key: 'refund', label: 'คืนเงิน / คืนสินค้า', icon: '↺' },
  { key: 'alerts', label: 'การแจ้งเตือน', icon: '♧' },
]

function shipmentStatusLabel(status?: string | null): string {
  switch (status) {
    case 'out_for_delivery':
      return 'กำลังนำส่ง'
    case 'in_transit':
      return 'อยู่ระหว่างขนส่ง'
    case 'delivered':
      return 'สำเร็จ'
    case 'delayed':
      return 'ล่าช้า'
    default:
      return status ?? 'ไม่ทราบสถานะ'
  }
}

function statusTone(status?: string | null): string {
  switch (status) {
    case 'delivered':
      return 'status-pill--success'
    case 'out_for_delivery':
      return 'status-pill--info'
    case 'in_transit':
      return 'status-pill--warning'
    case 'delayed':
      return 'status-pill--danger'
    default:
      return ''
  }
}

function formatDate(value?: string | null): string {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat('th-TH', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(date)
}

function orderStatusLabel(status?: string | null): string {
  switch (status) {
    case 'processing': return 'กำลังจัดเตรียม'
    case 'completed':  return 'สำเร็จ'
    case 'cancelled':  return 'ยกเลิกแล้ว'
    case 'pending':    return 'รอดำเนินการ'
    case 'shipped':    return 'จัดส่งแล้ว'
    case 'in_transit': return 'อยู่ระหว่างขนส่ง'
    default:           return status ?? 'ไม่ทราบสถานะ'
  }
}

const ORDER_STATUS_STYLE: Record<string, { bg: string; text: string; accent: string }> = {
  processing: { bg: '#eef4ff', text: '#3a6fd8', accent: '#89b4f7' },
  pending:    { bg: '#eef4ff', text: '#3a6fd8', accent: '#89b4f7' },
  shipped:    { bg: '#fff7f2', text: '#c05518', accent: '#f5a878' },
  in_transit: { bg: '#fff7f2', text: '#c05518', accent: '#f5a878' },
  completed:  { bg: '#f0fbf6', text: '#2a8a5a', accent: '#76c9a0' },
  delivered:  { bg: '#f0fbf6', text: '#2a8a5a', accent: '#76c9a0' },
  cancelled:  { bg: '#fff5f6', text: '#b84050', accent: '#f09090' },
}

function trackingSteps(status?: string | null): boolean[] {
  if (status === 'delivered') return [true, true, true, true, true]
  if (status === 'out_for_delivery') return [true, true, true, true, false]
  if (status === 'in_transit') return [true, true, true, false, false]
  return [true, false, false, false, false]
}

const STEP_LABELS = ['รับพัสดุ', 'คัดแยก', 'ระหว่างส่ง', 'ใกล้ถึง', 'จัดส่งสำเร็จ']

function shipmentStatusColor(status?: string | null): string {
  switch (status) {
    case 'delivered': return '#37ac56'
    case 'out_for_delivery': return '#4f7cff'
    case 'delayed': return '#ef4444'
    case 'in_transit': return '#ff8f41'
    default: return '#94a3b8'
  }
}

export function CustomerPortal() {
  const navigate = useNavigate()
  const session = readSession()
  const customerId = session?.customer_id ?? ''
  const userName = session?.user?.name ?? 'ลูกค้า'

  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = (searchParams.get('tab') as CustomerTab) ?? 'assistant'
  const setActiveTab = (tab: CustomerTab) => setSearchParams({ tab }, { replace: true })
  const [orders, setOrders] = useState<OrderSummary[]>([])
  const [shipments, setShipments] = useState<ShipmentDetail[]>([])
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [refundRequests, setRefundRequests] = useState<RefundRequest[]>([])
  const [conversationId, setConversationId] = useState<string>('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [historyOpen, setHistoryOpen] = useState(false)
  const [selectedRefundDetail, setSelectedRefundDetail] = useState<RefundRequestDetail | null>(null)
  const [showAllRefunds, setShowAllRefunds] = useState(false)
  const [refundDetailLoading, setRefundDetailLoading] = useState(false)
  const [proactiveAlerts, setProactiveAlerts] = useState<ProactiveAlert[]>([])
  const [expandedAlertId, setExpandedAlertId] = useState<string | null>(null)
  const [orderFilter, setOrderFilter] = useState<string>('all')
  const [shipmentFilter, setShipmentFilter] = useState<string>('all')
  const [chatMessage, setChatMessage] = useState('ของฉันอยู่ไหนแล้ว')
  const [refundReason, setRefundReason] = useState('สินค้าเสียหายและได้รับไม่ครบ')
  const [selectedOrderId, setSelectedOrderId] = useState<string>('')
  const [refundFiles, setRefundFiles] = useState<RefundUploadDraft[]>([])
  const [refundSubmitting, setRefundSubmitting] = useState(false)
  const [refundSuccessMessage, setRefundSuccessMessage] = useState<string | null>(null)
  const [refundUploadStatus, setRefundUploadStatus] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [chatLoading, setChatLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const refundFileInputRef = useRef<HTMLInputElement | null>(null)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError(null)

      try {
        const [ordersData, shipmentSummaries, conversationsData, refundRequestsData, alertsData] = await Promise.all([
          api.getCustomerOrders(customerId),
          api.getCustomerShipments(customerId),
          api.getCustomerConversations(customerId),
          api.getCustomerRefundRequests(customerId),
          api.getCustomerProactiveAlerts(customerId),
        ])

        const shipmentDetails = await Promise.all(shipmentSummaries.map((item) => api.getShipment(item.id)))

        setOrders(ordersData)
        setShipments(shipmentDetails)
        setConversations(conversationsData)
        setRefundRequests(refundRequestsData)
        setProactiveAlerts(alertsData)
        if (ordersData.length > 0) setSelectedOrderId(ordersData[0].id)

        if (conversationsData.length > 0) {
          const latestConv = conversationsData[0]
          setConversationId(latestConv.id)
          try {
            const detail = await api.getConversation(latestConv.id)
            const sortedMessages = [...detail.messages].sort((a, b) => {
              const ta = new Date(a.created_at ?? 0).getTime()
              const tb = new Date(b.created_at ?? 0).getTime()
              if (ta !== tb) return ta - tb
              const senderRank = (s?: string | null) => ((s ?? '').toLowerCase() === 'customer' ? 0 : 1)
              const sr = senderRank(a.sender_type) - senderRank(b.sender_type)
              if (sr !== 0) return sr
              return a.id.localeCompare(b.id)
            })
            const loaded: ChatMessage[] = sortedMessages.map((m) => ({
              role: m.sender_type === 'customer' ? 'user' : 'ai',
              text: m.content,
              time: m.created_at
                ? new Date(m.created_at).toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' })
                : '',
            }))
            setMessages(loaded)
          } catch {
            // ประวัติโหลดไม่ได้ — เริ่มใหม่
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'โหลดข้อมูลลูกค้าไม่สำเร็จ')
      } finally {
        setLoading(false)
      }
    }

    void load()
  }, [customerId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const previewOrder = useMemo(
    () => orders.find((o) => o.id === selectedOrderId) ?? orders[0] ?? null,
    [orders, selectedOrderId],
  )

  async function submitChat() {
    const text = chatMessage.trim()
    if (!text) return

    const convId = conversationId || crypto.randomUUID()
    if (!conversationId) setConversationId(convId)

    const now = new Date().toLocaleTimeString('th-TH', {
      hour: '2-digit',
      minute: '2-digit',
    })

    setMessages((prev) => [...prev, { role: 'user', text, time: now }])
    setChatMessage('')
    setChatLoading(true)
    setError(null)

    try {
      const result = await api.sendChat({
        customer_id: customerId,
        conversation_id: convId,
        message: text,
      })

      const aiNow = new Date().toLocaleTimeString('th-TH', {
        hour: '2-digit',
        minute: '2-digit',
      })

      setMessages((prev) => [...prev, { role: 'ai', text: result.response_text, time: aiNow }])

      // Refresh conversation list so new conversation appears in history
      const updatedConvs = await api.getCustomerConversations(customerId)
      setConversations(updatedConvs)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'ส่งข้อความไม่สำเร็จ')
    } finally {
      setChatLoading(false)
    }
  }

  async function switchConversation(convId: string) {
    if (convId === conversationId) return
    try {
      const detail = await api.getConversation(convId)
      const sortedMessages = [...detail.messages].sort((a, b) => {
        const ta = new Date(a.created_at ?? 0).getTime()
        const tb = new Date(b.created_at ?? 0).getTime()
        if (ta !== tb) return ta - tb
        const senderRank = (s?: string | null) => ((s ?? '').toLowerCase() === 'customer' ? 0 : 1)
        const sr = senderRank(a.sender_type) - senderRank(b.sender_type)
        if (sr !== 0) return sr
        return a.id.localeCompare(b.id)
      })
      const loaded: ChatMessage[] = sortedMessages.map((m) => ({
        role: m.sender_type === 'customer' ? 'user' : 'ai',
        text: m.content,
        time: m.created_at
          ? new Date(m.created_at).toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' })
          : '',
      }))
      setMessages(loaded)
      setConversationId(convId)
      setHistoryOpen(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'โหลดประวัติการสนทนาไม่สำเร็จ')
    }
  }

  function startNewChat() {
    setMessages([])
    setConversationId(crypto.randomUUID())
    setHistoryOpen(false)
  }

  async function loadRefundDetail(refundRequestId: string) {
    setRefundDetailLoading(true)
    setError(null)

    try {
      const detail = await api.getCustomerRefundRequestDetail(customerId, refundRequestId)
      setSelectedRefundDetail(detail)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'โหลดรายละเอียดคำขอคืนเงินไม่สำเร็จ')
    } finally {
      setRefundDetailLoading(false)
    }
  }

  async function submitRefundRequest() {
    if (!previewOrder || !refundReason.trim()) return

    setRefundSubmitting(true)
    setError(null)
    setRefundSuccessMessage(null)
    setRefundUploadStatus(null)

    try {
      const convId = conversationId || crypto.randomUUID()
      if (!conversationId) setConversationId(convId)

      const result = await api.createCustomerRefundRequest(customerId, {
        conversation_id: convId,
        order_id: previewOrder.id,
        reason: refundReason,
        requested_resolution: 'refund',
        evidence_items: [],
      })

      for (const [index, item] of refundFiles.entries()) {
        setRefundUploadStatus(`กำลังอัปโหลดไฟล์ ${index + 1}/${refundFiles.length}: ${item.file.name}`)

        await api.uploadAttachmentDirect(
          item.file,
          result.refund_request.id,
          item.evidenceGroup,
          item.description ?? item.file.name,
        )
      }

      setRefundRequests((current) => [result.refund_request, ...current])
      setRefundSuccessMessage(result.assistant_message)
      setRefundUploadStatus(refundFiles.length > 0 ? 'อัปโหลดหลักฐานเรียบร้อยแล้ว' : null)
      setShowAllRefunds(true)

      await loadRefundDetail(result.refund_request.id)

      setRefundFiles([])

      const refundCustomerRefundRequests = await api.getCustomerRefundRequests(customerId)
      setRefundRequests(refundCustomerRefundRequests)
      setActiveTab('refund')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'ส่งคำขอคืนเงินไม่สำเร็จ')
    } finally {
      setRefundSubmitting(false)
    }
  }

  function openAttachment(attachmentId: string) {
    window.open(api.getAttachmentDirectUrl(attachmentId), '_blank', 'noopener,noreferrer')
  }

  function renderAssistant() {
    const INTENT_LABEL: Record<string, string> = {
      track_shipment: 'ติดตามพัสดุ',
      refund_request: 'คืนเงิน',
      order_status: 'สถานะออเดอร์',
      general_inquiry: 'ทั่วไป',
    }

    return (
      <section className="shopeasy-chat-page">
        <header className="shopeasy-chat-header">
          <div className="shopeasy-chat-header__left">
            <div className="shopeasy-ai-label">AI</div>

            <div>
              <h2>แชทกับ ShopEasy AI Assistant</h2>
              <p>
                <span className="online-dot" />
                ออนไลน์
              </p>
            </div>
          </div>

          <div className="shopeasy-chat-header__right">
            {conversations.length > 0 && (
              <button
                type="button"
                className="chat-history-btn"
                onClick={() => setHistoryOpen((v) => !v)}
                title="ประวัติการสนทนา"
              >
                ☰ ประวัติ {conversations.length > 0 ? `(${conversations.length})` : ''}
              </button>
            )}
            <button type="button" className="chat-new-btn" onClick={startNewChat}>
              + สนทนาใหม่
            </button>
          </div>
        </header>

        {historyOpen && conversations.length > 0 && (
          <div className="chat-history-panel">
            <p className="chat-history-panel__title">ประวัติการสนทนา</p>
            <ul>
              {conversations.map((conv) => (
                <li
                  key={conv.id}
                  className={`chat-history-item${conv.id === conversationId ? ' chat-history-item--active' : ''}`}
                  onClick={() => void switchConversation(conv.id)}
                >
                  <span className="chat-history-item__intent">
                    {INTENT_LABEL[conv.latest_intent ?? ''] ?? conv.latest_intent ?? 'สนทนา'}
                  </span>
                  <span className="chat-history-item__date">
                    {conv.updated_at
                      ? new Date(conv.updated_at).toLocaleDateString('th-TH', {
                          day: 'numeric',
                          month: 'short',
                          year: '2-digit',
                        })
                      : '—'}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="shopeasy-chat-shell">
          {messages.length === 0 ? (
            <div className="shopeasy-empty-state">
              <div className="shopeasy-hero-icon">✦</div>

              <h1>
                <span>ShopEasy</span> AI Assistant
              </h1>

              <p className="shopeasy-hero-subtitle">
                สวัสดีค่ะ! ฉันช่วยตรวจสอบพัสดุ ขอคืนเงิน หรือสอบถามเกี่ยวกับออเดอร์ได้เลยค่ะ
              </p>

              <div className="shopeasy-quick-actions">
                <button type="button" onClick={() => setChatMessage('ของฉันอยู่ไหนแล้ว')}>
                  <span className="quick-action-icon">▱</span>

                  <div>
                    <strong>ของฉันอยู่ไหนแล้ว</strong>
                    <p>ตรวจสอบสถานะคำสั่งซื้อ</p>
                  </div>

                  <b>›</b>
                </button>

                <button type="button" onClick={() => setChatMessage('ขอคืนเงินได้ไหม')}>
                  <span className="quick-action-icon">▰</span>

                  <div>
                    <strong>ขอคืนเงินได้ไหม</strong>
                    <p>เช็คเงื่อนไขการคืนเงิน</p>
                  </div>

                  <b>›</b>
                </button>

                <button type="button" onClick={() => setChatMessage('ออเดอร์ของฉันสถานะอะไร')}>
                  <span className="quick-action-icon">☏</span>

                  <div>
                    <strong>สถานะออเดอร์</strong>
                    <p>สรุปคำสั่งซื้อทั้งหมด</p>
                  </div>

                  <b>›</b>
                </button>
              </div>
            </div>
          ) : (
            <div className="shopeasy-message-area">
              {messages.map((msg, index) =>
                msg.role === 'user' ? (
                  <div key={index} className="shopeasy-message shopeasy-message--user">
                    <p>{msg.text}</p>
                    <span>{msg.time}</span>
                  </div>
                ) : (
                  <div key={index} className="shopeasy-message-row">
                    <div className="shopeasy-message-avatar">S</div>

                    <div className="shopeasy-message shopeasy-message--ai">
                      <p style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</p>
                      <span>{msg.time}</span>
                    </div>
                  </div>
                ),
              )}

              {chatLoading ? (
                <div className="shopeasy-message-row">
                  <div className="shopeasy-message-avatar">S</div>

                  <div className="shopeasy-message shopeasy-message--ai">
                    <p>กำลังคิด...</p>
                  </div>
                </div>
              ) : null}
              <div ref={messagesEndRef} />
            </div>
          )}

          <div className="shopeasy-composer">
            <span className="composer-attach">⌕</span>

            <input
              value={chatMessage}
              onChange={(event) => setChatMessage(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') void submitChat()
              }}
              placeholder="พิมพ์ข้อความของคุณที่นี่..."
            />

            <button
              type="button"
              onClick={() => void submitChat()}
              disabled={chatLoading || !chatMessage.trim()}
            >
              ➤
            </button>
          </div>

          <div className="shopeasy-security-note">
            🔒 ข้อมูลของคุณปลอดภัย เรารักษาความเป็นส่วนตัวตามนโยบายบริษัท
          </div>
        </div>
      </section>
    )
  }



  function renderOrders() {
    const filterMap: Record<string, string[]> = {
      all:        [],
      processing: ['processing', 'pending'],
      in_transit: ['in_transit', 'shipped'],
      completed:  ['completed'],
      cancelled:  ['cancelled'],
    }
    const filtered = orderFilter === 'all'
      ? orders
      : orders.filter((o) => filterMap[orderFilter]?.includes(o.order_status ?? ''))

    const PILLS = [
      { key: 'all',        label: 'ทั้งหมด',        count: orders.length },
      { key: 'processing', label: 'จัดเตรียม',      count: orders.filter(o => ['processing','pending'].includes(o.order_status ?? '')).length },
      { key: 'in_transit', label: 'จัดส่งแล้ว',     count: orders.filter(o => ['in_transit','shipped'].includes(o.order_status ?? '')).length },
      { key: 'completed',  label: 'สำเร็จ',          count: orders.filter(o => o.order_status === 'completed').length },
      { key: 'cancelled',  label: 'ยกเลิก',          count: orders.filter(o => o.order_status === 'cancelled').length },
    ] as const

    return (
      <section className="customer-panel">
        <div className="ord-header">
          <h2 className="ord-title">คำสั่งซื้อของฉัน</h2>
          <span className="ord-count">{orders.length} รายการ</span>
        </div>

        <div className="ord-filters">
          {PILLS.map(({ key, label, count }) => (
            <button
              key={key}
              type="button"
              className={`ord-pill${orderFilter === key ? ' is-active' : ''}`}
              onClick={() => setOrderFilter(key)}
            >
              {label}
              {count > 0 && <span className="ord-pill__count">{count}</span>}
            </button>
          ))}
        </div>

        <div className="ord-list">
          {filtered.map((order) => {
            const st = ORDER_STATUS_STYLE[order.order_status ?? ''] ?? { bg: '#f5f7fc', text: '#7b8aa7', accent: '#c8d0e0' }
            return (
              <article key={order.id} className="ord-card">
                <div className="ord-card__accent" style={{ background: st.accent }} />
                <div className="ord-card__body">
                  <div className="ord-card__top">
                    <div className="ord-card__left">
                      <span className="ord-card__id">{order.id}</span>
                      <span className="ord-card__seller">{order.seller_name ?? '—'}</span>
                    </div>
                    <div className="ord-card__right">
                      <span className="ord-card__price">฿{order.total_amount?.toLocaleString() ?? '—'}</span>
                      <span className="ord-card__badge" style={{ background: st.bg, color: st.text }}>
                        {orderStatusLabel(order.order_status)}
                      </span>
                    </div>
                  </div>
                  <div className="ord-card__foot">
                    <span className="ord-card__date">สั่งเมื่อ {formatDate(order.created_at)}</span>
                    {order.promised_delivery_date && (
                      <span className="ord-card__eta">คาดว่าได้รับ {formatDate(order.promised_delivery_date)}</span>
                    )}
                  </div>
                </div>
              </article>
            )
          })}
          {filtered.length === 0 && (
            <div className="ord-empty">
              <p>ไม่มีคำสั่งซื้อในหมวดนี้</p>
            </div>
          )}
        </div>
      </section>
    )
  }

  function renderShipments() {
    const SHIP_PILLS = [
      { key: 'all',              label: 'ทั้งหมด',        statuses: [] as string[] },
      { key: 'in_transit',       label: 'ระหว่างขนส่ง',   statuses: ['in_transit', 'out_for_delivery'] },
      { key: 'delivered',        label: 'สำเร็จ',          statuses: ['delivered'] },
      { key: 'delayed',          label: 'ล่าช้า',          statuses: ['delayed'] },
    ] as const

    const filteredShipments = shipmentFilter === 'all'
      ? shipments
      : shipments.filter((s) => {
          const pill = SHIP_PILLS.find((p) => p.key === shipmentFilter)
          return pill ? (pill.statuses as readonly string[]).includes(s.shipment_status ?? '') : true
        })

    return (
      <section className="customer-panel">
        <header className="customer-panel__header customer-panel__header--section">
          <div className="customer-panel__title">
            <strong>การจัดส่งของฉัน</strong>
          </div>
        </header>

        <div className="ord-filters">
          {SHIP_PILLS.map(({ key, label, statuses }) => {
            const count = key === 'all'
              ? shipments.length
              : shipments.filter((s) => (statuses as readonly string[]).includes(s.shipment_status ?? '')).length
            return (
              <button
                key={key}
                type="button"
                className={`ord-pill${shipmentFilter === key ? ' is-active' : ''}`}
                onClick={() => setShipmentFilter(key)}
              >
                {label}
                {count > 0 && <span className="ord-pill__count">{count}</span>}
              </button>
            )
          })}
        </div>

        <div className="shipment-cards">
          {filteredShipments.map((shipment) => {
            const steps = trackingSteps(shipment.shipment_status)
            const activeIdx = steps.every(Boolean) ? -1 : steps.lastIndexOf(true)
            const color = shipmentStatusColor(shipment.shipment_status)
            const EVENT_PRIORITY: Record<string, number> = {
              picked_up: 1, sorted: 2, in_transit: 3,
              out_for_delivery: 4, delivered: 5, carrier_contacted: 6,
              shipment_no_update_48h: 0,
            }
            // Dedupe automated/system events to at most 1 per day per type per shipment
            const AUTOMATED_TYPES = new Set(['shipment_no_update_48h', 'carrier_contacted'])
            const seenAutomatedKeys = new Set<string>()
            const dedupedEvents = [...shipment.events]
              .sort((a, b) => {
                const ta = new Date(a.event_time ?? a.created_at ?? 0).getTime()
                const tb = new Date(b.event_time ?? b.created_at ?? 0).getTime()
                if (tb !== ta) return tb - ta
                const pa = EVENT_PRIORITY[a.event_type ?? ''] ?? 99
                const pb = EVENT_PRIORITY[b.event_type ?? ''] ?? 99
                return pb - pa
              })
              .filter((evt) => {
                const evtType = evt.event_type ?? ''
                if (!AUTOMATED_TYPES.has(evtType)) return true
                const ts = new Date(evt.event_time ?? evt.created_at ?? 0)
                const dayKey = `${evtType}|${ts.getFullYear()}-${ts.getMonth()}-${ts.getDate()}`
                if (seenAutomatedKeys.has(dayKey)) return false
                seenAutomatedKeys.add(dayKey)
                return true
              })
            const recentEvents = dedupedEvents.slice(0, 5)

            return (
              <article key={shipment.id} className="shipment-card">
                <div className="shipment-card__strip" style={{ background: color }} />
                <div className="shipment-card__body">

                  <div className="shipment-card__top">
                    <div className="shipment-card__icon" style={{ color }}>▱</div>
                    <div className="shipment-card__info">
                      <strong className="shipment-card__tracking">{shipment.tracking_no}</strong>
                      <span className="shipment-card__carrier">{shipment.carrier}</span>
                    </div>
                    <div className="shipment-card__badges">
                      <span className={`status-pill ${statusTone(shipment.shipment_status)}`}>
                        {shipmentStatusLabel(shipment.shipment_status)}
                      </span>
                      {shipment.delay_risk_score >= 50 && (
                        <span className="risk-badge">⚠ ความเสี่ยง {shipment.delay_risk_score}%</span>
                      )}
                    </div>
                  </div>

                  <div className="shipment-card__meta">
                    <div className="shipment-card__meta-item">
                      <span>คาดว่าถึง</span>
                      <strong>{formatDate(shipment.eta)}</strong>
                    </div>
                    {shipment.last_update && (
                      <div className="shipment-card__meta-item">
                        <span>อัปเดตล่าสุด</span>
                        <strong>{formatDate(shipment.last_update)}</strong>
                      </div>
                    )}
                    <div className="shipment-card__meta-item">
                      <span>ออเดอร์</span>
                      <strong>{shipment.order_id}</strong>
                    </div>
                  </div>

                  <div className="shipment-stepper">
                    {steps.map((done, index) => (
                      <div
                        key={`${shipment.id}-step-${index}`}
                        className={[
                          'shipment-stepper__step',
                          done ? 'is-done' : '',
                          index === activeIdx ? 'is-active' : '',
                        ].filter(Boolean).join(' ')}
                      >
                        {index < steps.length - 1 && (
                          <div className={`shipment-stepper__line ${done ? 'is-done' : ''}`} />
                        )}
                        <div className="shipment-stepper__dot">
                          {done && <span>✓</span>}
                        </div>
                        <span className="shipment-stepper__label">{STEP_LABELS[index]}</span>
                      </div>
                    ))}
                  </div>

                  {recentEvents.length > 0 && (
                    <div className="shipment-events">
                      {recentEvents.map((evt) => (
                        <div key={evt.id} className="shipment-event">
                          <span className="shipment-event__time">{formatDate(evt.event_time ?? evt.created_at)}</span>
                          <span className="shipment-event__msg">{evt.event_message ?? evt.event_type}</span>
                          {evt.location && <span className="shipment-event__loc">📍 {evt.location}</span>}
                        </div>
                      ))}
                    </div>
                  )}

                </div>
              </article>
            )
          })}
          {filteredShipments.length === 0 && (
            <div className="ord-empty">
              <p>{shipments.length === 0 ? 'ไม่มีข้อมูลการจัดส่ง' : 'ไม่มีพัสดุในหมวดนี้'}</p>
            </div>
          )}
        </div>
      </section>
    )
  }

  function renderRefund() {
    return (
      <section className="customer-panel customer-panel--refund">
        <header className="customer-panel__header customer-panel__header--section">
          <div className="customer-panel__title">
            <strong>คืนเงิน / คืนสินค้า</strong>
          </div>
        </header>

        <div className="refund-form-card">
          <h4>สร้างคำขอคืนเงิน / คืนสินค้า</h4>

          {orders.length > 1 ? (
            <div className="refund-reason-box" style={{ marginBottom: '0.75rem' }}>
              <strong>เลือกออเดอร์</strong>
              <select
                className="refund-reason-input"
                style={{ padding: '0.5rem', height: 'auto' }}
                value={selectedOrderId}
                onChange={(e) => setSelectedOrderId(e.target.value)}
              >
                {orders.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.id} — {o.seller_name} — ฿{o.total_amount?.toLocaleString()}
                  </option>
                ))}
              </select>
            </div>
          ) : null}

          <div className="refund-product">
            <div className="refund-product__image">{previewOrder?.seller_name?.slice(0, 1) ?? 'S'}</div>
            <div>
              <strong>{previewOrder?.id ?? '-'}</strong>
              <p>{previewOrder?.seller_name ?? '-'}</p>
              <span>฿{previewOrder?.total_amount?.toLocaleString() ?? '0'}</span>
            </div>
          </div>

          <div className="refund-reason-box">
            <strong>เหตุผล</strong>
            <textarea
              className="refund-reason-input"
              value={refundReason}
              onChange={(event) => setRefundReason(event.target.value)}
            />
          </div>

          <div className="refund-evidence-box">
            <strong>แนบหลักฐาน</strong>

            <div className="refund-evidence-grid">
              {refundFiles.map((item, index) => (
                <div key={`${item.file.name}-${index}`} className="refund-evidence-thumb" title={item.description ?? item.file.name}>
                  {index + 1}
                </div>
              ))}

              <input
                ref={refundFileInputRef}
                type="file"
                accept="image/*"
                multiple
                hidden
                onChange={(event) => {
                  const nextFiles = Array.from(event.target.files ?? []).map((file, index) => ({
                    file,
                    evidenceGroup: index === 0 ? 'damaged_item' : 'customer_upload',
                    description: file.name,
                  }))

                  if (nextFiles.length > 0) {
                    setRefundFiles((current) => [...current, ...nextFiles])
                  }

                  event.currentTarget.value = ''
                }}
              />

              <button
                type="button"
                className="refund-evidence-thumb refund-evidence-thumb--add"
                onClick={() => refundFileInputRef.current?.click()}
              >
                +
              </button>
            </div>

            <p className="refund-evidence-note">จะส่งหลักฐาน {refundFiles.length} รายการไปพร้อมคำขอนี้</p>

            {refundFiles.length > 0 ? (
              <div className="refund-file-list">
                {refundFiles.map((item, index) => (
                  <div key={`${item.file.name}-${index}-meta`} className="refund-file-row">
                    <div>
                      <strong>{item.file.name}</strong>
                      <p>{item.file.type || 'application/octet-stream'} · {(item.file.size / 1024).toFixed(1)} KB</p>
                    </div>

                    <button
                      type="button"
                      className="refund-file-remove"
                      onClick={() => setRefundFiles((current) => current.filter((_, currentIndex) => currentIndex !== index))}
                      disabled={refundSubmitting}
                    >
                      ลบ
                    </button>
                  </div>
                ))}
              </div>
            ) : null}

            {refundUploadStatus ? <p className="refund-upload-status">{refundUploadStatus}</p> : null}
          </div>

          <div className="refund-actions">
            <button
              type="button"
              className="refund-submit-button"
              onClick={() => void submitRefundRequest()}
              disabled={refundSubmitting}
            >
              {refundSubmitting ? 'กำลังส่ง...' : 'ส่งคำขอ'}
            </button>

            <button type="button" className="refund-link-button" onClick={() => setShowAllRefunds((current) => !current)}>
              {showAllRefunds ? 'แสดงย่อ' : 'ดูประวัติทั้งหมด'}
            </button>
          </div>
        </div>

        {refundSuccessMessage ? <div className="notice notice--success">{refundSuccessMessage}</div> : null}
        {error ? <div className="notice notice--error">{error}</div> : null}

        {showAllRefunds ? (
          <div style={{ marginTop: '1rem' }}>
            <strong style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>ประวัติคำขอคืนเงิน ({refundRequests.length} รายการ)</strong>
            {refundDetailLoading ? <div className="notice">กำลังโหลด...</div> : null}
            <div className="list-stack">
              {refundRequests.map((item) => {
                const linkedOrder = orders.find((o) => o.id === item.order_id)
                const productName =
                  linkedOrder?.items?.[0]?.product_name ??
                  linkedOrder?.seller_name ??
                  item.order_id
                return (
                  <article
                    key={item.id}
                    className="list-card"
                    style={{ cursor: 'pointer', outline: selectedRefundDetail?.id === item.id ? '2px solid #ee4d2d' : 'none' }}
                    onClick={() => void loadRefundDetail(item.id)}
                  >
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <strong style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {productName}
                      </strong>
                      <p style={{ fontSize: '0.78rem', color: '#94a3b8', margin: '0.15rem 0 0.25rem' }}>
                        ออเดอร์ {item.order_id} · คำขอ {item.id}
                      </p>
                      <p style={{ fontSize: '0.8rem', color: '#666', margin: 0 }}>{item.reason}</p>
                    </div>
                    <div className="list-card__meta">
                      <span>Risk {item.risk_score}</span>
                      <span className="status-pill">{item.status}</span>
                    </div>
                  </article>
                )
              })}
            </div>

            {selectedRefundDetail ? (
              (() => {
                const linkedOrder = orders.find((o) => o.id === selectedRefundDetail.order_id)
                const productName =
                  linkedOrder?.items?.[0]?.product_name ??
                  linkedOrder?.seller_name ??
                  selectedRefundDetail.order_id
                return (
                  <div className="list-card" style={{ marginTop: '0.75rem', background: '#fffaf7' }}>
                    <strong style={{ display: 'block', marginBottom: '0.25rem' }}>{productName}</strong>
                    <p style={{ fontSize: '0.78rem', color: '#94a3b8', margin: '0 0 0.5rem' }}>
                      ออเดอร์ {selectedRefundDetail.order_id} · คำขอ {selectedRefundDetail.id}
                    </p>
                    <p style={{ fontSize: '0.82rem' }}>เหตุผล: {selectedRefundDetail.reason}</p>
                    <p style={{ fontSize: '0.82rem' }}>สถานะ: {selectedRefundDetail.status} | AI แนะนำ: {selectedRefundDetail.ai_recommendation}</p>
                {selectedRefundDetail.attachments.length > 0 ? (
                  <div style={{ marginTop: '0.5rem' }}>
                    <strong style={{ fontSize: '0.82rem' }}>หลักฐาน ({selectedRefundDetail.attachments.length} ไฟล์):</strong>
                    <div className="refund-attachment-list">
                      {selectedRefundDetail.attachments.map((att) => (
                        <div key={att.id} className="refund-attachment-item">
                          <div>
                            <strong>{att.file_name ?? att.id}</strong>
                            <p className="refund-attachment-item__group">{att.evidence_group}</p>
                          </div>
                          <button
                            type="button"
                            className="ghost-button"
                            onClick={(e) => { e.stopPropagation(); openAttachment(att.id) }}
                          >
                            เปิด
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
              <p className="customer-empty">ยังไม่มีหลักฐาน</p>
                )}
              </div>
                )
              })()
            ) : refundRequests.length > 0 ? (
              <p className="customer-empty">คลิกที่รายการเพื่อดูรายละเอียด</p>
            ) : null}
          </div>
        ) : null}
      </section>
    )
  }

  function renderAlerts() {
    const ALERT_STYLE: Record<string, { bg: string; text: string; accent: string }> = {
      open:     { bg: '#fff7f2', text: '#d97706', accent: '#f5a878' },
      resolved: { bg: '#f0fbf6', text: '#059669', accent: '#76c9a0' },
      closed:   { bg: '#f0fbf6', text: '#059669', accent: '#76c9a0' },
    }

    return (
      <section className="customer-panel">
        <div className="alrt-header">
          <h2 className="alrt-title">การแจ้งเตือน</h2>
          <span className="alrt-count">{proactiveAlerts.filter(a => a.status === 'open').length} รายการที่ยังใช้งาน</span>
        </div>

        <div className="alrt-list">
          {proactiveAlerts.length === 0 && (
            <div className="alrt-empty">
              <p>ไม่มีการแจ้งเตือนในขณะนี้</p>
            </div>
          )}
          {proactiveAlerts.map((alert) => {
            const st = ALERT_STYLE[alert.status ?? ''] ?? { bg: '#f5f7fc', text: '#8090b0', accent: '#c8d0e0' }
            const isExpanded = expandedAlertId === alert.id
            return (
              <article key={alert.id} className="alrt-card">
                <div className="alrt-card__accent" style={{ background: st.accent }} />
                <button
                  type="button"
                  className="alrt-card__head"
                  onClick={() => setExpandedAlertId(isExpanded ? null : alert.id)}
                >
                  <div className="alrt-card__info">
                    <span className="alrt-card__type">{alert.alert_type ?? 'การแจ้งเตือน'}</span>
                    <span className="alrt-card__title">{alert.message_draft ?? `พัสดุ ${alert.shipment_id || alert.order_id || 'N/A'}`}</span>
                  </div>
                  <div className="alrt-card__right">
                    {alert.risk_score != null && (
                      <span className="alrt-card__risk">
                        <span className="alrt-risk-label">ความเสี่ยง</span>
                        <span className="alrt-risk-val" style={{ color: st.text }}>{alert.risk_score}%</span>
                      </span>
                    )}
                    <span className="alrt-card__badge" style={{ background: st.bg, color: st.text }}>
                      {alert.status === 'open' ? 'เปิดอยู่' : alert.status === 'resolved' ? 'แก้ไขแล้ว' : 'ปิด'}
                    </span>
                    <span className={`alrt-chevron${isExpanded ? ' is-expanded' : ''}`}>▼</span>
                  </div>
                </button>

                {isExpanded && (
                  <div className="alrt-card__detail">
                    {alert.recommended_action && (
                      <div className="alrt-section">
                        <span className="alrt-section__label">ขอแนะนำ</span>
                        <p className="alrt-section__text">{alert.recommended_action}</p>
                      </div>
                    )}
                    {alert.resolution_note && (
                      <div className="alrt-section">
                        <span className="alrt-section__label">หมายเหตุ</span>
                        <p className="alrt-section__text">{alert.resolution_note}</p>
                      </div>
                    )}
                    {alert.shipment_id && (
                      <div className="alrt-section alrt-section--inline">
                        <span className="alrt-section__label">พัสดุ</span>
                        <span className="alrt-section__value">{alert.shipment_id}</span>
                      </div>
                    )}
                    {alert.order_id && (
                      <div className="alrt-section alrt-section--inline">
                        <span className="alrt-section__label">ออเดอร์</span>
                        <span className="alrt-section__value">{alert.order_id}</span>
                      </div>
                    )}
                  </div>
                )}
              </article>
            )
          })}
        </div>
      </section>
    )
  }

  function renderContent() {
    switch (activeTab) {
      case 'assistant':
        return renderAssistant()
      case 'orders':
        return renderOrders()
      case 'shipments':
        return renderShipments()
      case 'refund':
        return renderRefund()
      case 'alerts':
        return renderAlerts()
      default:
        return renderAssistant()
    }
  }

  return (
    <div className="customer-app">
      <aside className="customer-sidebar-wrap">
        <div className="customer-brand-block">
          <div className="customer-brand-block__logo">S</div>
          <div>
            <h1>ShopEasy</h1>
            <strong>AI Assistant</strong>
          </div>
        </div>

        <Sidebar
          title=""
          subtitle=""
          accent="linear-gradient(135deg, #ee4d2d, #ff3415)"
          items={navItems}
          activeKey={activeTab}
          onSelect={(key) => setActiveTab(key as CustomerTab)}
          footer={
            <div className="sidebar-profile sidebar-profile--customer">
              <strong>{userName}</strong>
              <span>{session?.user?.email ?? ''}</span>

              <button
                type="button"
                className="ghost-button"
                style={{ marginTop: '0.5rem', width: '100%', fontSize: '0.75rem' }}
                onClick={() => {
                  clearSession()
                  navigate('/')
                }}
              >
                Logout
              </button>
            </div>
          }
        />
      </aside>

      <main className="customer-main">
        {loading ? <div className="notice">กำลังโหลดข้อมูลจาก backend...</div> : null}

        <div className="customer-content-wrapper">
          {renderContent()}
        </div>
      </main>
    </div>
  )
}