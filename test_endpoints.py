import requests

BASE = 'http://localhost:8000/api/v1'

roles = {}
for role_email, role_pass, label in [
    ('customer_demo@shopeasy.local', 'demo1234', 'customer'),
    ('admin_demo@shopeasy.local', 'demo1234', 'admin'),
    ('ai_system_admin@shopeasy.local', 'demo1234', 'ai'),
]:
    r = requests.post(BASE + '/auth/login', json={'email': role_email, 'password': role_pass})
    if r.status_code == 200:
        data = r.json()
        roles[label] = {'token': data['access_token'], 'customer_id': data.get('customer_id'), 'user': data['user']}
        print('[' + label + '] Login OK | role=' + str(data['user']['role']) + ' | customer_id=' + str(data.get('customer_id')))
    else:
        print('[' + label + '] Login FAIL ' + str(r.status_code) + ': ' + r.text[:100])

ch = {'Authorization': 'Bearer ' + roles['customer']['token']}
ah = {'Authorization': 'Bearer ' + roles['admin']['token']}
aih = {'Authorization': 'Bearer ' + roles['ai']['token']}
cid = roles['customer']['customer_id']

# Test GET endpoints
tests_get = [
    (BASE + '/data/customers/' + cid + '/orders', ch, 'GET customer orders'),
    (BASE + '/data/customers/' + cid + '/shipments', ch, 'GET customer shipments'),
    (BASE + '/data/customers/' + cid + '/conversations', ch, 'GET customer conversations'),
    (BASE + '/data/customers/' + cid + '/refund-requests', ch, 'GET customer refunds'),
    (BASE + '/admin/cases', ah, 'GET admin cases'),
    (BASE + '/admin/approvals', ah, 'GET admin approvals'),
    (BASE + '/admin/refund-requests', ah, 'GET admin refunds'),
    (BASE + '/admin/proactive-alerts', ah, 'GET admin alerts'),
    (BASE + '/ai/agent-traces', aih, 'GET ai traces'),
    (BASE + '/ai/tool-logs', aih, 'GET ai tool-logs'),
]

for url, headers, label in tests_get:
    r = requests.get(url, headers=headers)
    count = len(r.json()) if r.status_code == 200 and isinstance(r.json(), list) else r.json()
    status = 'OK' if r.status_code == 200 else 'FAIL'
    print('[' + status + '] ' + label + ': ' + str(r.status_code) + ' | ' + str(count)[:80])

# Test chat
r = requests.post(BASE + '/chat', json={
    'customer_id': cid,
    'conversation_id': 'test-conv-001',
    'message': 'ของฉันอยู่ไหนแล้ว'
}, headers=ch)
status = 'OK' if r.status_code == 200 else 'FAIL'
print('[' + status + '] POST chat: ' + str(r.status_code) + ' | ' + (str(r.json().get('response_text', ''))[:80] if r.status_code == 200 else r.text[:80]))

# Test proactive
r = requests.post(BASE + '/events/proactive-delay', json={
    'shipment_id': 'SHP-9002',
    'event_type': 'shipment_no_update_48h'
}, headers=ah)
status = 'OK' if r.status_code == 200 else 'FAIL'
print('[' + status + '] POST proactive-delay: ' + str(r.status_code))
