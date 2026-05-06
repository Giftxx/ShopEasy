import { useEffect, useMemo, useRef, useState } from 'react'

import { Sidebar } from '../../components/Sidebar'
import { api } from '../../lib/api'
import type {
  ChatResponse,
  ConversationSummary,
  OrderSummary,
  RefundRequest,
  RefundRequestDetail,
  ShipmentDetail,
} from '../../types/api'

type CustomerTab = 'home' | 'assistant' | 'orders' | 'shipments' | 'refund' | 'alerts' | 'help'

type RefundUploadDraft = {
  file: File
  evidenceGroup: string
  description?: string | null
}

const navItems: { key: CustomerTab; label: string; icon: string }[] = [
  { key: 'home', label: 'หน้าหลัก', icon: '⌂' },
  { key: 'assistant', label: 'แชตกับ AI', icon: '✦' },
  { key: 'orders', label: 'คำสั่งซื้อของฉัน', icon: '▣' },
  { key: 'shipments', label: 'การจัดส่งของฉัน', icon: '◎' },
  { key: 'refund', label: 'คืนเงิน / คืนสินค้า', icon: '◌' },
  { key: 'alerts', label: 'การแจ้งเตือน', icon: '◔' },
  { key: 'help', label: 'ศูนย์ช่วยเหลือ', icon: '?' },
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
    case 'processing':
      return 'กำลังจัดเตรียม'
    case 'completed':
      return 'สำเร็จ'
    case 'cancelled':
      return 'ยกเลิกแล้ว'
    case 'pending':
      return 'รอดำเนินการ'
    default:
      return status ?? 'ไม่ทราบสถานะ'
  }
}

function trackingSteps(status?: string | null): boolean[] {
  if (status === 'delivered') return [true, true, true, true, true]
  if (status === 'out_for_delivery') return [true, true, true, true, false]
  if (status === 'in_transit') return [true, true, true, false, false]
  return [true, false, false, false, false]
}

export function CustomerPortal() {
  const [activeTab, setActiveTab] = useState<CustomerTab>('assistant')
  const [orders, setOrders] = useState<OrderSummary[]>([])
  const [shipments, setShipments] = useState<ShipmentDetail[]>([])
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [refundRequests, setRefundRequests] = useState<RefundRequest[]>([])
  const [selectedRefundDetail, setSelectedRefundDetail] = useState<RefundRequestDetail | null>(null)
  const [showAllRefunds, setShowAllRefunds] = useState(false)
  const [refundDetailLoading, setRefundDetailLoading] = useState(false)
  const [chatResult, setChatResult] = useState<ChatResponse | null>(null)
  const [chatMessage, setChatMessage] = useState('ของฉันอยู่ไหนแล้ว')
  const [refundReason, setRefundReason] = useState('สินค้าเสียหายและได้รับไม่ครบ')
  const [refundFiles, setRefundFiles] = useState<RefundUploadDraft[]>([])
  const [refundSubmitting, setRefundSubmitting] = useState(false)
  const [refundSuccessMessage, setRefundSuccessMessage] = useState<string | null>(null)
  const [refundUploadStatus, setRefundUploadStatus] = useState<string | null>(null)
  const [openingAttachmentId, setOpeningAttachmentId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [chatLoading, setChatLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const refundFileInputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const [ordersData, shipmentSummaries, conversationsData, refundRequestsData] = await Promise.all([
          api.getCustomerOrders('CUST-001'),
          api.getCustomerShipments('CUST-001'),
          api.getCustomerConversations('CUST-001'),
          api.getCustomerRefundRequests('CUST-001'),
        ])
        const shipmentDetails = await Promise.all(shipmentSummaries.map((item) => api.getShipment(item.id)))
        setOrders(ordersData)
        setShipments(shipmentDetails)
        setConversations(conversationsData)
        setRefundRequests(refundRequestsData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'โหลดข้อมูลลูกค้าไม่สำเร็จ')
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [])

  const activeShipments = useMemo(
    () => shipments.filter((shipment) => shipment.shipment_status !== 'delivered'),
    [shipments],
  )

  const topShipment = activeShipments[0] ?? shipments[0] ?? null
  const previewOrder = orders[0] ?? null

  async function submitChat() {
    if (!chatMessage.trim()) return
    setChatLoading(true)
    setError(null)
    try {
      const result = await api.sendChat({
        customer_id: 'CUST-001',
        conversation_id: 'CONV-001',
        message: chatMessage,
      })
      setChatResult(result)
      setActiveTab('assistant')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'ส่งข้อความไม่สำเร็จ')
    } finally {
      setChatLoading(false)
    }
  }

  async function loadRefundDetail(refundRequestId: string) {
    setRefundDetailLoading(true)
    setError(null)
    try {
      const detail = await api.getCustomerRefundRequestDetail('CUST-001', refundRequestId)
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
      const result = await api.createCustomerRefundRequest('CUST-001', {
        conversation_id: 'CONV-002',
        order_id: previewOrder.id,
        reason: refundReason,
        requested_resolution: 'refund',
        evidence_items: [],
      })
      for (const [index, item] of refundFiles.entries()) {
        setRefundUploadStatus(`กำลังอัปโหลดไฟล์ ${index + 1}/${refundFiles.length}: ${item.file.name}`)
        const presign = await api.presignAttachmentUpload({
          file_name: item.file.name,
          content_type: item.file.type || 'application/octet-stream',
          refund_request_id: result.refund_request.id,
          evidence_group: item.evidenceGroup,
        })
        await api.uploadAttachmentFile(presign.upload_url, item.file)
        await api.confirmAttachmentUpload({
          object_name: presign.object_name,
          file_name: item.file.name,
          content_type: item.file.type || 'application/octet-stream',
          refund_request_id: result.refund_request.id,
          evidence_group: item.evidenceGroup,
          description: item.description ?? item.file.name,
          file_size_bytes: item.file.size,
        })
      }
      setRefundRequests((current) => [result.refund_request, ...current])
      setRefundSuccessMessage(result.assistant_message)
      setRefundUploadStatus(refundFiles.length > 0 ? 'อัปโหลดหลักฐานเรียบร้อยแล้ว' : null)
      setShowAllRefunds(true)
      await loadRefundDetail(result.refund_request.id)
      setRefundFiles([])
      setActiveTab('refund')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'ส่งคำขอคืนเงินไม่สำเร็จ')
    } finally {
      setRefundSubmitting(false)
    }
  }

  async function openAttachment(attachmentId: string) {
    setOpeningAttachmentId(attachmentId)
    setError(null)
    try {
      const presign = await api.getAttachmentDownloadUrl(attachmentId)
      window.open(presign.upload_url, '_blank', 'noopener,noreferrer')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'เปิดไฟล์หลักฐานไม่สำเร็จ')
    } finally {
      setOpeningAttachmentId(null)
    }
  }

  function renderHome() {
    return (
      <div className="customer-home-grid">
        <section className="customer-home-card">
          <h3>สรุปภาพรวม</h3>
          <div className="customer-home-stats">
            <div>
              <strong>{orders.length}</strong>
              <span>คำสั่งซื้อ</span>
            </div>
            <div>
              <strong>{shipments.length}</strong>
              <span>พัสดุ</span>
            </div>
            <div>
              <strong>{conversations.length}</strong>
              <span>บทสนทนา</span>
            </div>
          </div>
        </section>
        <section className="customer-home-card">
          <h3>สิ่งที่ควรติดตาม</h3>
          <p>{topShipment ? `${topShipment.tracking_no} · ${shipmentStatusLabel(topShipment.shipment_status)}` : 'ยังไม่มีข้อมูลพัสดุ'}</p>
        </section>
      </div>
    )
  }

  function renderAssistant() {
    return (
      <section className="customer-panel customer-panel--chat">
        <header className="customer-panel__header">
          <div className="customer-panel__title">
            <span className="customer-panel__index">AI</span>
            <div>
              <strong>แชตกับ ShopEasy AI Assistant</strong>
              <p>
                <span className="online-dot" />
                ออนไลน์
              </p>
            </div>
          </div>
          <button type="button" className="customer-dots-button">
            ...
          </button>
        </header>

        <div className="assistant-panel">
          <div className="assistant-bubble assistant-bubble--user">
            ของฉันโดนดีเลย์อีกแล้วค่ะ อัปเดตครั้งที่ 1 พ.ค.
            <br />
            ถ้าไม่ได้วันนี้ จะขอคืนเงินได้ไหมคะ
            <span>10:21</span>
          </div>

          <div className="assistant-response">
            <div className="assistant-avatar">S</div>
            <div className="assistant-response__body">
              <div className="assistant-card">
                <strong>ขอดูในความล่าช้านี้ค่ะ</strong>
                <p>เดี๋ยวตรวจสอบออเดอร์ให้แบบละเอียดค่ะ</p>
                <span>10:21</span>
              </div>

              <div className="tracking-detail-card">
                <strong>ออเดอร์ {previewOrder?.id ?? 'SP-1024'}</strong>
                <dl>
                  <div>
                    <dt>ร้านค้า</dt>
                    <dd>{previewOrder?.seller_name ?? 'BeautMall'}</dd>
                  </div>
                  <div>
                    <dt>ขนส่ง</dt>
                    <dd>{topShipment?.carrier ?? 'Flash Express'}</dd>
                  </div>
                  <div>
                    <dt>Tracking Number</dt>
                    <dd>{topShipment?.tracking_no ?? 'TH0123456789'}</dd>
                  </div>
                  <div>
                    <dt>สถานะ</dt>
                    <dd>{shipmentStatusLabel(topShipment?.shipment_status)}</dd>
                  </div>
                  <div>
                    <dt>คาดว่าจะได้รับ</dt>
                    <dd>{formatDate(topShipment?.eta)}</dd>
                  </div>
                </dl>
              </div>

              <div className="assistant-summary-card">
                <p>หากพัสดุไม่อัปเดตภายในวันนี้ ฉันสามารถช่วยเปิดเคสติดตามให้ หรือประสานเรื่องคืนเงินต่อได้ค่ะ</p>
                <div className="assistant-actions">
                  <button type="button">ขอเปิดเคสติดตาม</button>
                  <button type="button">ขออัปเดตตอนนี้</button>
                  <button type="button">คุยกับเจ้าหน้าที่</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {chatResult ? <div className="assistant-chat-result">{chatResult.response_text}</div> : null}

        <div className="assistant-composer">
          <input value={chatMessage} onChange={(event) => setChatMessage(event.target.value)} placeholder="พิมพ์ข้อความ..." />
          <button type="button" className="assistant-send-button" onClick={() => void submitChat()} disabled={chatLoading}>
            {chatLoading ? '...' : '+'}
          </button>
        </div>
      </section>
    )
  }

  function renderOrders() {
    return (
      <section className="customer-panel">
        <header className="customer-panel__header customer-panel__header--section">
          <div className="customer-panel__title">
            <span className="customer-panel__number">2</span>
            <strong>คำสั่งซื้อของฉัน</strong>
          </div>
        </header>

        <div className="customer-tabs">
          <button type="button" className="is-active">
            ทั้งหมด
          </button>
          <button type="button">จัดส่งปกติ</button>
          <button type="button">กำลังจัดส่ง</button>
          <button type="button">สำเร็จ</button>
          <button type="button">ยกเลิก</button>
        </div>

        <div className="order-rows">
          {orders.map((order) => (
            <article key={order.id} className="order-row">
              <div className="order-row__image">{order.seller_name?.slice(0, 1) ?? 'S'}</div>
              <div className="order-row__main">
                <strong>{order.id}</strong>
                <p>{order.seller_name}</p>
              </div>
              <div className="order-row__price">฿{order.total_amount?.toLocaleString()}</div>
              <div className={`order-row__status ${statusTone(order.order_status === 'completed' ? 'delivered' : 'in_transit')}`}>
                {orderStatusLabel(order.order_status)}
              </div>
              <div className="order-row__date">คาดว่าจะได้รับ {formatDate(order.promised_delivery_date)}</div>
            </article>
          ))}
        </div>
      </section>
    )
  }

  function renderShipments() {
    return (
      <section className="customer-panel">
        <header className="customer-panel__header customer-panel__header--section">
          <div className="customer-panel__title">
            <span className="customer-panel__number">3</span>
            <strong>การจัดส่งของฉัน</strong>
          </div>
        </header>

        <div className="tracking-search">
          <input placeholder="ค้นหา Tracking No." />
          <button type="button">ค้นหา</button>
        </div>

        <div className="tracking-list">
          {shipments.map((shipment) => {
            const steps = trackingSteps(shipment.shipment_status)
            return (
              <article key={shipment.id} className="tracking-list__item">
                <div className="tracking-list__top">
                  <div>
                    <strong>{shipment.tracking_no}</strong>
                    <p>{shipment.carrier}</p>
                  </div>
                  <div className="tracking-list__eta">
                    <strong>
                      {shipment.shipment_status === 'out_for_delivery'
                        ? 'กำลังจัดส่ง'
                        : shipment.shipment_status === 'in_transit'
                          ? 'ในอีก 2 วัน'
                          : 'สำเร็จแล้ว'}
                    </strong>
                    <span>คาดว่าจะถึง {formatDate(shipment.eta)}</span>
                  </div>
                </div>

                <div className="tracking-steps">
                  {steps.map((done, index) => (
                    <div key={`${shipment.id}-${index}`} className="tracking-step">
                      <span className={done ? 'is-done' : ''} />
                    </div>
                  ))}
                </div>
                <div className="tracking-labels">
                  <span>รับพัสดุแล้ว</span>
                  <span>คัดแยกแล้ว</span>
                  <span>ระหว่างส่ง</span>
                  <span>ใกล้ถึงปลายทาง</span>
                  <span>จัดส่งสำเร็จ</span>
                </div>
              </article>
            )
          })}
        </div>
      </section>
    )
  }

  function renderRefund() {
    return (
      <section className="customer-panel customer-panel--refund">
        <header className="customer-panel__header customer-panel__header--section">
          <div className="customer-panel__title">
            <span className="customer-panel__number">4</span>
            <strong>คืนเงิน / คืนสินค้า</strong>
          </div>
        </header>

        <div className="refund-form-card">
          <h4>สร้างคำขอคืนเงิน / คืนสินค้า</h4>
          <div className="refund-product">
            <div className="refund-product__image">{previewOrder?.seller_name?.slice(0, 1) ?? 'S'}</div>
            <div>
              <strong>{previewOrder?.id ?? 'SP-1024'}</strong>
              <p>{previewOrder?.seller_name ?? 'BeautMall'}</p>
              <span>฿{previewOrder?.total_amount?.toLocaleString() ?? '879.00'}</span>
            </div>
          </div>

          <div className="refund-reason-box">
            <strong>เหตุผล</strong>
            <textarea className="refund-reason-input" value={refundReason} onChange={(event) => setRefundReason(event.target.value)} />
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
                      onClick={() =>
                        setRefundFiles((current) => current.filter((_, currentIndex) => currentIndex !== index))
                      }
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
            <button type="button" className="refund-submit-button" onClick={() => void submitRefundRequest()} disabled={refundSubmitting}>
              {refundSubmitting ? 'กำลังส่ง...' : 'ส่งคำขอ'}
            </button>
            <button type="button" className="refund-link-button" onClick={() => setShowAllRefunds((current) => !current)}>
              {showAllRefunds ? 'แสดงย่อ' : 'ดูประวัติทั้งหมด'}
            </button>
          </div>
        </div>

        {refundSuccessMessage ? <div className="notice notice--success">{refundSuccessMessage}</div> : null}
        {error ? <div className="notice notice--error">{error}</div> : null}

        <div className="refund-history">
          <div className="refund-history__header">
            <strong>{showAllRefunds ? 'ประวัติคำขอทั้งหมด' : 'คำขอล่าสุด'}</strong>
          </div>

          <div className={`refund-history__content ${showAllRefunds ? 'is-expanded' : ''}`}>
            <div className="refund-history__list">
              {(showAllRefunds ? refundRequests : refundRequests.slice(0, 3)).map((request) => (
                <article
                  key={request.id}
                  className={`refund-history__item ${selectedRefundDetail?.id === request.id ? 'is-selected' : ''}`}
                  onClick={() => void loadRefundDetail(request.id)}
                >
                  <div>
                    <strong>{request.id}</strong>
                    <p>{request.reason}</p>
                  </div>
                  <div className="refund-history__meta">
                    <span className="status-pill">{request.status ?? 'pending'}</span>
                    <small>Evidence {request.evidence_count ?? 0}</small>
                    <small>Case {request.case_id ?? '-'}</small>
                  </div>
                </article>
              ))}
            </div>

            {showAllRefunds ? (
              <div className="refund-detail-panel">
                {refundDetailLoading ? <p>กำลังโหลดรายละเอียด...</p> : null}
                {!refundDetailLoading && selectedRefundDetail ? (
                  <>
                    <strong>{selectedRefundDetail.id}</strong>
                    <p>{selectedRefundDetail.reason}</p>
                    <div className="refund-detail-panel__meta">
                      <span className="status-pill">{selectedRefundDetail.status ?? 'pending'}</span>
                      <small>Case {selectedRefundDetail.case_id ?? '-'}</small>
                      <small>Risk {selectedRefundDetail.risk_score}</small>
                    </div>
                    <div className="refund-detail-panel__attachments">
                      {selectedRefundDetail.attachments.map((attachment) => (
                        <article key={attachment.id} className="refund-detail-attachment">
                          <div className="refund-detail-attachment__content">
                            <strong>{attachment.file_name ?? attachment.id}</strong>
                            <p>{attachment.description ?? attachment.evidence_group ?? 'evidence'}</p>
                          </div>
                          <button
                            type="button"
                            className="refund-detail-attachment__action"
                            onClick={() => void openAttachment(attachment.id)}
                            disabled={openingAttachmentId === attachment.id}
                          >
                            {openingAttachmentId === attachment.id ? 'กำลังเปิด...' : 'เปิดหลักฐาน'}
                          </button>
                        </article>
                      ))}
                    </div>
                  </>
                ) : null}
                {!refundDetailLoading && !selectedRefundDetail ? <p>เลือกคำขอทางซ้ายเพื่อดูรายละเอียด</p> : null}
              </div>
            ) : null}
          </div>
        </div>
      </section>
    )
  }

  function renderAlerts() {
    return (
      <section className="customer-panel">
        <header className="customer-panel__header customer-panel__header--section">
          <div className="customer-panel__title">
            <span className="customer-panel__number">5</span>
            <strong>การแจ้งเตือน</strong>
          </div>
          <button type="button" className="section-link-button">
            ดูทั้งหมด
          </button>
        </header>

        <div className="alert-list">
          {activeShipments.map((shipment, index) => (
            <article key={shipment.id} className="alert-item">
              <div className={`alert-item__icon alert-item__icon--${index % 3}`}>{index + 1}</div>
              <div className="alert-item__body">
                <strong>{shipment.shipment_status === 'in_transit' ? 'อัปเดตการขนส่งช้า' : 'อัปเดตการจัดส่ง'}</strong>
                <p>
                  ออเดอร์ {shipment.order_id} {shipmentStatusLabel(shipment.shipment_status)}
                </p>
              </div>
              <span>{index === 0 ? '10:20' : '09:12'}</span>
            </article>
          ))}
          <article className="alert-item">
            <div className="alert-item__icon alert-item__icon--2">i</div>
            <div className="alert-item__body">
              <strong>สำรองคืนเงินไม่ได้รับการอัปเดต</strong>
              <p>เรากำลังตรวจสอบภายใน 1-3 วัน</p>
            </div>
            <span>28/04</span>
          </article>
        </div>
      </section>
    )
  }

  function renderHelp() {
    return (
      <section className="customer-panel customer-panel--help">
        <header className="customer-panel__header customer-panel__header--section">
          <div className="customer-panel__title">
            <span className="customer-panel__number">6</span>
            <strong>ศูนย์ช่วยเหลือ</strong>
          </div>
        </header>

        <div className="help-search-box">
          <input placeholder="ค้นหาคำถามที่พบบ่อย" />
        </div>

        <div className="help-list">
          <p>คำถามที่พบบ่อย</p>
          <button type="button">วิธีติดตามพัสดุ</button>
          <button type="button">นโยบายการคืนเงิน / คืนสินค้า</button>
          <button type="button">ระยะเวลาสำหรับการคืนเงิน</button>
          <button type="button">การขอคืนสินค้าอยู่ที่ไหน</button>
          <button type="button">ปัญหาเรื่องค่าขนส่งชำระเงิน</button>
          <button type="button">การขนส่งล่าช้าทำอย่างไร</button>
        </div>

        <button type="button" className="help-contact-button">
          ติดต่อเจ้าหน้าที่
        </button>
      </section>
    )
  }

  function renderContent() {
    switch (activeTab) {
      case 'home':
        return renderHome()
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
      case 'help':
        return renderHelp()
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
            <strong>Agentic Support Platform</strong>
            <p>Shopee-inspired Marketplace AI Ops</p>
          </div>
        </div>

        <Sidebar
          title=""
          subtitle=""
          accent="linear-gradient(135deg, #ff5a2b, #ff8a39)"
          items={navItems}
          activeKey={activeTab}
          onSelect={(key) => setActiveTab(key as CustomerTab)}
          footer={
            <div className="sidebar-profile sidebar-profile--customer">
              <strong>Nicha</strong>
              <span>Silver Member</span>
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
