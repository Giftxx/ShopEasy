from datetime import datetime, timedelta


def get_workflow_03_seed_data() -> dict[str, list[dict]]:
    now = datetime.utcnow()
    stale_time = now - timedelta(hours=72)
    return {
        "shipment_events": [
            {
                "id": "EVT-7001",
                "shipment_id": "SHP-9002",
                "event_type": "shipment_no_update_48h",
                "event_message": "No shipment update for more than 48 hours.",
                "location": "Bangkok Sorting Center",
                "event_time": stale_time,
                "raw_payload": {"source": "scheduler", "threshold_hours": 48},
                "created_at": now,
            }
        ],
        "proactive_alerts": [
            {
                "id": "ALT-1001",
                "order_id": "SP-1024",
                "shipment_id": "SHP-9002",
                "alert_type": "shipment_delay",
                "risk_score": 87,
                "status": "open",
                "recommended_action": "Notify customer and monitor shipment",
                "message_draft": "Initial proactive delay draft",
                "case_id": "CS-7001",
                "created_at": now,
                "resolved_at": None,
            }
        ],
        "cases": [
            {
                "id": "CS-7001",
                "customer_id": "CUST-001",
                "order_id": "SP-1024",
                "case_type": "shipping_delay",
                "priority": "high",
                "status": "open",
                "ai_summary": "Shipment delay case opened proactively.",
                "assigned_role": "admin",
                "assigned_user_id": None,
                "created_by": "ai",
                "created_at": now,
                "updated_at": now,
            }
        ],
        "approvals": [
            {
                "id": "APR-7001",
                "case_id": "CS-7001",
                "approval_type": "compensation",
                "requested_action": "Review compensation for delayed shipment",
                "amount": 100.00,
                "currency": "THB",
                "risk_level": "high",
                "status": "pending",
                "ai_reason": "Shipment delay risk score is above threshold.",
                "policy_citation": {"policy_ids": ["POL-003", "POL-004"]},
                "reviewer_id": None,
                "reviewed_at": None,
                "created_at": now,
            }
        ],
        "policies": [
            {
                "id": "POL-004",
                "title": "Shipping Policy",
                "category": "shipping",
                "version": "v1.0",
                "content": "Delayed shipments with no update beyond 48 hours should trigger proactive review.",
                "status": "active",
                "effective_from": None,
                "effective_to": None,
                "created_at": now,
                "updated_at": now,
            }
        ],
        "policy_chunks": [
            {
                "id": "PCH-004",
                "policy_id": "POL-004",
                "chunk_index": 0,
                "chunk_text": "48-hour stale shipments should trigger proactive alerting.",
                "metadata_json": {"section": "4.1"},
                "embedding_id": "emb-pol-004-0",
                "created_at": now,
            }
        ],
    }
