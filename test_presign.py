import requests

r = requests.post('http://localhost:8000/api/v1/auth/login', json={'email':'customer_demo@shopeasy.local','password':'demo1234'})
token = r.json()['access_token']
h = {'Authorization': 'Bearer ' + token}

r2 = requests.post('http://localhost:8000/api/v1/attachments/presign-upload',
    json={'file_name':'test.jpg','content_type':'image/jpeg','refund_request_id':'RF-TEST','evidence_group':'damaged_item'},
    headers=h)
print('STATUS:', r2.status_code)
print('RESPONSE:', r2.text[:800])
