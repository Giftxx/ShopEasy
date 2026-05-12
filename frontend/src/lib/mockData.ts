/**
 * Mock Data — จำลองข้อมูลที่ดึงมาจาก Shopee API
 *
 * ไฟล์นี้ใช้สำหรับ development/testing เมื่อ backend ยังไม่พร้อม
 * โครงสร้างข้อมูลอ้างอิงจาก Shopee Open Platform API
 * https://open.shopee.com/documents
 *
 * ใช้งาน:
 *   import { mockOrders, mockShipments, ... } from '@/lib/mockData'
 */

import type {
  Approval,
  CaseDetail,
  CaseSummary,
  ConversationSummary,
  OrderSummary,
  ProactiveAlert,
  RefundRequest,
  ShipmentDetail,
} from '../types/api'

// ─── Customers ──────────────────────────────────────────────────────────────

export const mockCustomers = [
  {
    id: 'CUST-001',
    name: 'นริศรา สมบัติวงศ์',
    email: 'customer_demo@shopeasy.local',
    phone: '089-123-4567',
    tier: 'gold',
    registered_at: '2024-03-15T10:00:00Z',
  },
  {
    id: 'CUST-002',
    name: 'สมชาย ศรีสุข',
    email: 'somchai@shopeasy.local',
    phone: '081-234-5678',
    tier: 'silver',
    registered_at: '2024-06-20T14:30:00Z',
  },
] as const

// ─── Sellers ────────────────────────────────────────────────────────────────

export const mockSellers = [
  { id: 'SELLER-001', name: 'FashionHub', rating: 4.8, products_count: 342 },
  { id: 'SELLER-002', name: 'GadgetMall', rating: 4.6, products_count: 128 },
  { id: 'SELLER-003', name: 'HomeDecor Plus', rating: 4.9, products_count: 87 },
] as const

// ─── Orders ─────────────────────────────────────────────────────────────────

export const mockOrders: OrderSummary[] = [
  {
    id: 'SP-1024',
    customer_id: 'CUST-001',
    seller_id: 'SELLER-001',
    seller_name: 'FashionHub',
    order_status: 'shipped',
    payment_status: 'paid',
    total_amount: 2490,
    currency: 'THB',
    promised_delivery_date: '2025-01-25T00:00:00Z',
    created_at: '2025-01-18T09:15:00Z',
    updated_at: '2025-01-18T09:15:00Z',
  },
  {
    id: 'SP-2044',
    customer_id: 'CUST-001',
    seller_id: 'SELLER-002',
    seller_name: 'GadgetMall',
    order_status: 'shipped',
    payment_status: 'paid',
    total_amount: 1790,
    currency: 'THB',
    promised_delivery_date: '2025-01-20T00:00:00Z',
    created_at: '2025-01-12T14:30:00Z',
    updated_at: '2025-01-20T11:00:00Z',
  },
  {
    id: 'SP-3091',
    customer_id: 'CUST-001',
    seller_id: 'SELLER-003',
    seller_name: 'HomeDecor Plus',
    order_status: 'processing',
    payment_status: 'paid',
    total_amount: 3200,
    currency: 'THB',
    promised_delivery_date: '2025-02-01T00:00:00Z',
    created_at: '2025-01-22T16:45:00Z',
    updated_at: '2025-01-22T16:45:00Z',
  },
  {
    id: 'SP-4010',
    customer_id: 'CUST-001',
    seller_id: 'SELLER-001',
    seller_name: 'FashionHub',
    order_status: 'completed',
    payment_status: 'paid',
    total_amount: 890,
    currency: 'THB',
    promised_delivery_date: '2025-01-15T00:00:00Z',
    created_at: '2025-01-05T10:00:00Z',
    updated_at: '2025-01-12T11:00:00Z',
  },
]

// ─── Order Items ────────────────────────────────────────────────────────────

export const mockOrderItems = [
  { id: 'ITEM-001', order_id: 'SP-1024', product_name: 'กางเกงขายาว ผ้าฝ้าย', sku: 'FH-PANT-001', quantity: 1, unit_price: 1290 },
  { id: 'ITEM-002', order_id: 'SP-1024', product_name: 'เสื้อยืด Oversize', sku: 'FH-SHIRT-042', quantity: 2, unit_price: 600 },
  { id: 'ITEM-003', order_id: 'SP-2044', product_name: 'หูฟังบลูทูธ Pro Max', sku: 'GM-AUDIO-019', quantity: 1, unit_price: 1790 },
  { id: 'ITEM-004', order_id: 'SP-3091', product_name: 'โคมไฟตั้งโต๊ะ LED', sku: 'HD-LAMP-005', quantity: 1, unit_price: 1450 },
  { id: 'ITEM-005', order_id: 'SP-3091', product_name: 'หมอนอิง ลายมินิมอล', sku: 'HD-PILLOW-012', quantity: 2, unit_price: 875 },
]

// ─── Shipments ──────────────────────────────────────────────────────────────

export const mockShipments: ShipmentDetail[] = [
  {
    id: 'SHIP-1024-A',
    order_id: 'SP-1024',
    carrier: 'Kerry Express',
    tracking_no: 'KRY2025011801234',
    shipment_status: 'in_transit',
    eta: '2025-01-25T12:00:00Z',
    last_update: '2025-01-22T08:30:00Z',
    delay_risk_score: 15,
    created_at: '2025-01-19T10:00:00Z',
    updated_at: '2025-01-22T08:30:00Z',
    events: [
      { id: 'EVT-001', event_type: 'picked_up', event_message: 'พัสดุถูกรับจากผู้ส่ง', location: 'กรุงเทพฯ — คลังสินค้า FashionHub', event_time: '2025-01-19T10:00:00Z', created_at: '2025-01-19T10:00:00Z' },
      { id: 'EVT-002', event_type: 'sorted', event_message: 'คัดแยกพัสดุที่ศูนย์กระจายสินค้า', location: 'กรุงเทพฯ — ศูนย์บางนา', event_time: '2025-01-20T06:15:00Z', created_at: '2025-01-20T06:15:00Z' },
      { id: 'EVT-003', event_type: 'in_transit', event_message: 'อยู่ระหว่างขนส่ง', location: 'นนทบุรี — ศูนย์แจ้งวัฒนะ', event_time: '2025-01-22T08:30:00Z', created_at: '2025-01-22T08:30:00Z' },
    ],
  },
  {
    id: 'SHIP-2044-A',
    order_id: 'SP-2044',
    carrier: 'Flash Express',
    tracking_no: 'FLE2025011205678',
    shipment_status: 'delivered',
    eta: '2025-01-20T12:00:00Z',
    last_update: '2025-01-20T11:00:00Z',
    delay_risk_score: 0,
    created_at: '2025-01-13T09:00:00Z',
    updated_at: '2025-01-20T11:00:00Z',
    events: [
      { id: 'EVT-010', event_type: 'picked_up', event_message: 'พัสดุถูกรับจากผู้ส่ง', location: 'กรุงเทพฯ — คลังสินค้า GadgetMall', event_time: '2025-01-13T09:00:00Z', created_at: '2025-01-13T09:00:00Z' },
      { id: 'EVT-011', event_type: 'sorted', event_message: 'คัดแยกพัสดุ', location: 'กรุงเทพฯ — ศูนย์ลาดกระบัง', event_time: '2025-01-14T07:00:00Z', created_at: '2025-01-14T07:00:00Z' },
      { id: 'EVT-012', event_type: 'out_for_delivery', event_message: 'กำลังนำส่ง', location: 'ปทุมธานี — สาขาคลองหลวง', event_time: '2025-01-20T09:30:00Z', created_at: '2025-01-20T09:30:00Z' },
      { id: 'EVT-013', event_type: 'delivered', event_message: 'จัดส่งสำเร็จ — ผู้รับเซ็นรับพัสดุแล้ว', location: 'ปทุมธานี', event_time: '2025-01-20T11:00:00Z', created_at: '2025-01-20T11:00:00Z' },
    ],
  },
]

// ─── Conversations ──────────────────────────────────────────────────────────

export const mockConversations: ConversationSummary[] = [
  {
    id: 'CONV-001',
    customer_id: 'CUST-001',
    channel: 'web',
    status: 'open',
    latest_intent: 'tracking',
    created_at: '2025-01-22T10:00:00Z',
    updated_at: '2025-01-22T10:05:00Z',
  },
]

// ─── Refund Requests ────────────────────────────────────────────────────────

export const mockRefundRequests: RefundRequest[] = [
  {
    id: 'RF-5521',
    order_id: 'SP-2044',
    customer_id: 'CUST-001',
    case_id: 'CS-5521',
    reason: 'สินค้าเสียหายจากการขนส่ง — หูฟังมีรอยร้าว',
    requested_resolution: 'refund',
    eligibility_status: 'eligible',
    risk_score: 45,
    ai_recommendation: 'อนุมัติคืนเงินเต็มจำนวน — สินค้าเสียหายจากขนส่ง',
    status: 'pending',
    evidence_count: 2,
    created_at: '2025-01-21T14:00:00Z',
    updated_at: '2025-01-21T14:00:00Z',
  },
  {
    id: 'RF-8002',
    order_id: 'SP-5002',
    customer_id: 'CUST-002',
    case_id: 'CS-8002',
    reason: 'สินค้าส่งผิดรุ่น ได้เสื้อสีดำแทนสีขาว',
    requested_resolution: 'refund',
    eligibility_status: 'under_review',
    risk_score: 30,
    ai_recommendation: 'แนะนำอนุมัติ — สินค้าส่งผิดรุ่น',
    status: 'pending',
    evidence_count: 0,
    created_at: '2025-01-24T08:00:00Z',
    updated_at: '2025-01-24T08:00:00Z',
  },
]

// ─── Proactive Alerts ───────────────────────────────────────────────────────

export const mockProactiveAlerts: ProactiveAlert[] = [
  {
    id: 'ALT-1001',
    order_id: 'SP-1024',
    shipment_id: 'SHP-9002',
    alert_type: 'shipment_delay',
    risk_score: 87,
    status: 'open',
    recommended_action: 'แจ้งลูกค้าเรื่องความล่าช้า พร้อมชดเชยค่าส่ง',
    message_draft: 'สวัสดีค่ะ คุณนริศรา พัสดุ TRACK-9002 อาจจัดส่งล่าช้ากว่ากำหนด 1-2 วัน เนื่องจากสภาพอากาศ',
    case_id: 'CS-7001',
    created_at: '2025-01-22T09:00:00Z',
    resolved_at: null,
  },
  {
    id: 'ALT-2001',
    order_id: 'SP-5001',
    shipment_id: 'SHP-5001',
    alert_type: 'shipment_delay',
    risk_score: 42,
    status: 'open',
    recommended_action: 'ติดตามสถานะกับ Kerry Express',
    message_draft: 'สวัสดีค่ะ คุณ Somchai พัสดุ TH5001 อาจจัดส่งล่าช้า 1-2 วัน',
    case_id: null,
    created_at: '2025-01-23T06:00:00Z',
    resolved_at: null,
  },
]

// ─── Cases (Admin) ──────────────────────────────────────────────────────────

export const mockCases: CaseSummary[] = [
  {
    id: 'CS-5521',
    customer_id: 'CUST-001',
    order_id: 'SP-2044',
    case_type: 'refund',
    priority: 'medium',
    status: 'approved',
    ai_summary: 'ลูกค้าร้องเรียนสินค้าเสียหายจากการขนส่ง (หูฟังบลูทูธ) — AI แนะนำอนุมัติคืนเงิน',
    resolution_note: null,
    assigned_role: 'admin',
    created_by: 'system',
    created_at: '2025-01-21T14:00:00Z',
    updated_at: '2025-01-21T14:00:00Z',
  },
  {
    id: 'CS-7001',
    customer_id: 'CUST-001',
    order_id: 'SP-1024',
    case_type: 'shipping_delay',
    priority: 'high',
    status: 'approved',
    ai_summary: 'พัสดุล่าช้าเกิน 48 ชม. — AI แนะนำชดเชยค่าจัดส่ง',
    resolution_note: null,
    assigned_role: 'admin',
    created_by: 'ai',
    created_at: '2025-01-22T09:00:00Z',
    updated_at: '2025-01-22T09:00:00Z',
  },
  {
    id: 'CS-8001',
    customer_id: 'CUST-002',
    order_id: 'SP-5001',
    case_type: 'shipping_inquiry',
    priority: 'low',
    status: 'resolved',
    ai_summary: 'ลูกค้าสอบถามสถานะจัดส่ง — AI ตอบเรียบร้อย',
    resolution_note: null,
    assigned_role: 'admin',
    created_by: 'ai',
    created_at: '2025-01-23T10:00:00Z',
    updated_at: '2025-01-23T10:05:00Z',
  },
  {
    id: 'CS-8002',
    customer_id: 'CUST-002',
    order_id: 'SP-5002',
    case_type: 'refund',
    priority: 'medium',
    status: 'open',
    ai_summary: 'ลูกค้าร้องเรียนสินค้าไม่ตรงรุ่น — รอตรวจสอบ',
    resolution_note: null,
    assigned_role: 'admin',
    created_by: 'ai',
    created_at: '2025-01-24T08:00:00Z',
    updated_at: '2025-01-24T08:00:00Z',
  },
]

// ─── Approvals (Admin) ──────────────────────────────────────────────────────

export const mockApprovals: Approval[] = [
  {
    id: 'APR-1001',
    case_id: 'CS-5521',
    approval_type: 'refund',
    requested_action: 'คืนเงิน ฿2,490 สำหรับออเดอร์ SP-1024 — สินค้าเสียหาย',
    amount: 2490,
    currency: 'THB',
    risk_level: 'low',
    status: 'approved',
    ai_reason: 'Risk score 45 — มีหลักฐานภาพสินค้าเสียหาย ตรงตามนโยบายคืนเงิน',
    review_note: null,
    policy_citation: null,
    created_at: '2025-01-21T14:01:00Z',
  },
  {
    id: 'APR-7001',
    case_id: 'CS-7001',
    approval_type: 'compensation',
    requested_action: 'ชดเชยค่าจัดส่ง ฿100 — พัสดุล่าช้าเกิน 48 ชม.',
    amount: 100,
    currency: 'THB',
    risk_level: 'low',
    status: 'approved',
    ai_reason: 'Delay risk 87 — ตรงตามนโยบายชดเชยค่าส่ง',
    review_note: null,
    policy_citation: null,
    created_at: '2025-01-22T09:01:00Z',
  },
  {
    id: 'APR-8002',
    case_id: 'CS-8002',
    approval_type: 'refund',
    requested_action: 'คืนเงิน ฿1,290 — ออเดอร์ SP-5002 ส่งผิดรุ่น',
    amount: 1290,
    currency: 'THB',
    risk_level: 'low',
    status: 'pending',
    ai_reason: 'Risk score 30 — สินค้าส่งผิดรุ่น ตรงตามนโยบายคืนเงิน',
    review_note: null,
    policy_citation: null,
    created_at: '2025-01-24T08:01:00Z',
  },
]

// ─── Case Detail (Admin) ────────────────────────────────────────────────────

export const mockCaseDetail: CaseDetail = {
  ...mockCases[0],
  approvals: mockApprovals,
  refund_requests: [
    {
      ...mockRefundRequests[0],
      attachments: [
        {
          id: 'ATT-001',
          evidence_group: 'damaged_item',
          description: 'รูปสินค้าเสียหาย — รอยร้าวด้านข้างหูฟัง',
          file_name: 'damaged_headphone_01.jpg',
          mime_type: 'image/jpeg',
          object_key: 'attachments/RF-5521/damaged_headphone_01.jpg',
          upload_status: 'uploaded',
          created_at: '2025-01-21T14:02:00Z',
        },
        {
          id: 'ATT-002',
          evidence_group: 'packaging',
          description: 'กล่องพัสดุสภาพเสียหาย',
          file_name: 'damaged_box_01.jpg',
          mime_type: 'image/jpeg',
          object_key: 'attachments/RF-5521/damaged_box_01.jpg',
          upload_status: 'uploaded',
          created_at: '2025-01-21T14:03:00Z',
        },
      ],
    },
  ],
  attachments: [],
}

// ─── Analytics (AI Control) ─────────────────────────────────────────────────

export const mockAnalyticsStats = [
  { label: 'Total Conversations', value: '23', delta: '+12.3%', up: true },
  { label: 'Auto-resolution Rate', value: '72.2%', delta: '+4.3%', up: true },
  { label: 'Hand-off Rate', value: '27.8%', delta: '-4.3%', up: false },
  { label: 'Avg. Response Time', value: '0.7s', delta: '-0.2s', up: false },
]

export const mockAnalyticsTrend = [25, 45, 30, 55, 40, 60, 45, 70, 50, 65, 55, 75]
export const mockAnalyticsTrendDates = ['12 May', '13 May', '14 May', '15 May', '16 May']

export const mockAnalyticsIntents = [
  { label: 'track_shipment', pct: 38.9, color: '#3b82f6' },
  { label: 'refund_request', pct: 19.4, color: '#10b981' },
  { label: 'proactive_delay_alert', pct: 19.4, color: '#f59e0b' },
  { label: 'general_inquiry', pct: 11.1, color: '#8b5cf6' },
  { label: 'approve_approval', pct: 5.6, color: '#6366f1' },
  { label: 'close_case', pct: 5.6, color: '#d1d5db' },
]

// ─── Evaluation (AI Control) ────────────────────────────────────────────────

export const mockEvalStats = [
  { label: 'Total Traces', value: '36' },
  { label: 'Success', value: '6' },
  { label: 'Pass Rate', value: '16.7%', green: false },
  { label: 'Last Run', value: '12/05/2026' },
]

export const mockEvalSegments = [
  { pct: 16.7, color: '#10b981' },
  { pct: 2.8, color: '#ef4444' },
  { pct: 80.6, color: '#f59e0b' },
]

export const mockEvalLegend = [
  { label: 'Success', value: '6 (16.7%)', color: '#10b981' },
  { label: 'Failed', value: '1 (2.8%)', color: '#ef4444' },
  { label: 'Partial/Other', value: '29 (80.6%)', color: '#f59e0b' },
]
