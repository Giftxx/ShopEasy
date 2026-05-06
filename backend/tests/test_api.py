def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_tracking_chat(client):
    response = client.post(
        "/api/v1/chat",
        json={
            "customer_id": "CUST-001",
            "conversation_id": "CONV-001",
            "message": "ของฉันอยู่ไหนแล้ว",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "workflow_01_track_shipment"
    assert len(payload["active_shipments"]) == 2


def test_refund_chat(client):
    response = client.post(
        "/api/v1/chat",
        json={
            "customer_id": "CUST-001",
            "conversation_id": "CONV-002",
            "message": "สินค้าเสียหาย ขอคืนเงิน",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "workflow_02_refund_return"
    assert payload["state_snapshot"]["case_id"].startswith("CS-")
    assert payload["state_snapshot"]["refund_request_id"].startswith("RF-")


def test_proactive_event(client):
    response = client.post(
        "/api/v1/events/proactive-delay",
        json={"shipment_id": "SHP-9002", "event_type": "shipment_no_update_48h"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "workflow_03_proactive_delay_alert"
    assert payload["state_snapshot"]["alert_id"] == "ALT-1001"


def test_admin_lists(client):
    response = client.get("/api/v1/admin/cases")
    assert response.status_code == 200
    assert len(response.json()) >= 2

    detail_response = client.get("/api/v1/admin/cases/CS-5521")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert len(detail_payload["refund_requests"]) >= 1
    assert len(detail_payload["refund_requests"][0]["attachments"]) >= 1


def test_create_customer_refund_request(client):
    response = client.post(
        "/api/v1/data/customers/CUST-001/refund-requests",
        json={
            "conversation_id": "CONV-002",
            "order_id": "SP-1024",
            "reason": "สินค้าเสียหายและได้รับไม่ครบ",
            "requested_resolution": "refund",
            "evidence_items": [
                {
                    "evidence_group": "damaged_item",
                    "description": "ภาพสินค้ามีรอยแตก",
                    "file_name": "damaged-item-01.jpg",
                    "mime_type": "image/jpeg",
                },
                {
                    "evidence_group": "parcel_package",
                    "description": "ภาพกล่องพัสดุ",
                    "file_name": "parcel-box-01.jpg",
                    "mime_type": "image/jpeg",
                },
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "workflow_02_refund_return"
    assert payload["refund_request"]["order_id"] == "SP-1024"
    assert payload["refund_request"]["customer_id"] == "CUST-001"
    assert payload["refund_request"]["id"].startswith("RF-")
    assert payload["case_id"].startswith("CS-")
    assert payload["refund_request"]["evidence_count"] == 2


def test_attachment_presign_and_confirm(client):
    refund_response = client.post(
        "/api/v1/data/customers/CUST-001/refund-requests",
        json={
            "conversation_id": "CONV-002",
            "order_id": "SP-1024",
            "reason": "Need to upload evidence after request creation",
            "requested_resolution": "refund",
            "evidence_items": [],
        },
    )
    assert refund_response.status_code == 200
    refund_request_id = refund_response.json()["refund_request"]["id"]

    presign_response = client.post(
        "/api/v1/attachments/presign-upload",
        json={
            "file_name": "damage.jpg",
            "content_type": "image/jpeg",
            "refund_request_id": refund_request_id,
            "evidence_group": "damaged_item",
        },
    )
    assert presign_response.status_code == 200
    presign_payload = presign_response.json()
    assert "upload_url" in presign_payload
    assert f"refund_request/{refund_request_id}/damaged_item/" in presign_payload["object_name"]

    confirm_response = client.post(
        "/api/v1/attachments/confirm-upload",
        json={
            "object_name": presign_payload["object_name"],
            "file_name": "damage.jpg",
            "content_type": "image/jpeg",
            "refund_request_id": refund_request_id,
            "evidence_group": "damaged_item",
            "description": "Front zipper broken",
            "file_size_bytes": 2048,
        },
    )
    assert confirm_response.status_code == 201
    attachment_payload = confirm_response.json()
    assert attachment_payload["file_name"] == "damage.jpg"
    assert attachment_payload["object_key"] == presign_payload["object_name"]
    assert attachment_payload["upload_status"] == "uploaded"

    download_response = client.get(f"/api/v1/attachments/{attachment_payload['id']}/presign-download")
    assert download_response.status_code == 200
    download_payload = download_response.json()
    assert "upload_url" in download_payload
    assert download_payload["object_name"] == presign_payload["object_name"]


def test_trace_detail_business_context(client):
    refund_response = client.post(
        "/api/v1/chat",
        json={
            "customer_id": "CUST-001",
            "conversation_id": "CONV-002",
            "message": "สินค้าเสียหาย ขอคืนเงิน",
            "target_order_id": "SP-1024",
        },
    )
    assert refund_response.status_code == 200
    trace_id = refund_response.json()["state_snapshot"]["trace_id"]

    trace_response = client.get(f"/api/v1/ai/agent-traces/{trace_id}")
    assert trace_response.status_code == 200
    payload = trace_response.json()
    assert payload["business_context"]["refund_request_id"].startswith("RF-")
    assert payload["business_context"]["case"]["id"].startswith("CS-")
    assert len(payload["business_context"]["case"]["refund_requests"]) >= 1

    filtered_response = client.get("/api/v1/ai/agent-traces", params={"workflow_name": "workflow_02_refund_return"})
    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.json()
    assert len(filtered_payload) >= 1
    assert all(item["workflow_name"] == "workflow_02_refund_return" for item in filtered_payload)

    tool_log_response = client.get(
        "/api/v1/ai/tool-logs",
        params={"trace_id": trace_id, "agent_name": "router_node", "status": "success"},
    )
    assert tool_log_response.status_code == 200
    tool_log_payload = tool_log_response.json()
    assert len(tool_log_payload) >= 1
    assert all(item["agent_name"] == "router_node" for item in tool_log_payload)
    assert all(item["status"] == "success" for item in tool_log_payload)
