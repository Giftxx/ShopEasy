import io
import requests

BASE = 'http://localhost:8000/api/v1'

# Login
r = requests.post(BASE + '/auth/login', json={'email':'customer_demo@shopeasy.local','password':'demo1234'})
token = r.json()['access_token']
h = {'Authorization': 'Bearer ' + token}

# First create a refund request to get a valid refund_request_id
r2 = requests.post(BASE + '/chat', json={
    'customer_id': 'CUST-001',
    'conversation_id': 'test-upload-001',
    'message': 'ขอคืนเงิน สินค้าเสียหาย ออเดอร์ SP-1024'
}, headers=h)
snap = r2.json().get('state_snapshot', {})
refund_id = snap.get('refund_request_id')
print('Refund ID:', refund_id)

if not refund_id:
    print('ERROR: No refund request created')
    exit(1)

# Upload a test file via /attachments/upload-direct
fake_image = io.BytesIO(b'\xff\xd8\xff\xe0' + b'\x00' * 100)  # minimal JPEG header bytes
files = {'file': ('test_evidence.jpg', fake_image, 'image/jpeg')}
data = {
    'refund_request_id': refund_id,
    'evidence_group': 'damaged_item',
    'description': 'Test evidence photo',
}

r3 = requests.post(BASE + '/attachments/upload-direct', files=files, data=data, headers=h)
print('Upload status:', r3.status_code)
if r3.status_code == 201:
    att = r3.json()
    print('Attachment ID:', att['id'])
    print('File name:', att['file_name'])
    print('Object key:', att['object_key'])
    print('Upload status:', att['upload_status'])

    # Test download proxy
    att_id = att['id']
    r4 = requests.get(BASE + '/attachments/' + att_id + '/download', headers=h)
    print('Download proxy status:', r4.status_code)
    print('Content-Type:', r4.headers.get('content-type'))
    print('Content-Length:', len(r4.content), 'bytes')
    print('ALL UPLOAD/DOWNLOAD OK')
else:
    print('Upload FAILED:', r3.text[:300])
