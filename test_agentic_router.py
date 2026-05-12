import requests
import time

BASE = "http://localhost:8000/api/v1"
ts = int(time.time())

login = requests.post(f"{BASE}/auth/login", json={"email": "customer_demo@shopeasy.local", "password": "demo1234"})
token = login.json()["access_token"]
h = {"Authorization": "Bearer " + token}

r1 = requests.post(f"{BASE}/chat", json={"conversation_id": f"conv-agent-t1-{ts}", "customer_id": "CUST-001", "message": "พัสดุของฉันอยู่ไหนครับ"}, headers=h)
j1 = r1.json()
print("[WF01] intent:", j1.get("intent"), "| workflow:", j1.get("workflow_name"))
tc = j1.get("state_snapshot", {}).get("state", {}).get("tool_calls", [])
print("[Router tool]:", tc[0] if tc else "no tool_calls")

r2 = requests.post(f"{BASE}/chat", json={"conversation_id": f"conv-agent-t2-{ts}", "customer_id": "CUST-001", "message": "ขอคืนเงิน สินค้าเสียหาย", "target_order_id": "SP-1024"}, headers=h)
j2 = r2.json()
print("[WF02] intent:", j2.get("intent"), "| workflow:", j2.get("workflow_name"))
print("ALL OK" if j1.get("intent") and j2.get("intent") else "CHECK FAILED")