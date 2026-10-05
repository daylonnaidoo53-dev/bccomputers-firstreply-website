#!/usr/bin/env bash
# demo.sh — bash demonstration script
# Author: Daylon Naido · BCComputers

set -e

BASE_URL="${BASE_URL:-http://localhost:8000}"
ADMIN_TOKEN="${ADMIN_TOKEN:-dev-admin-token}"

echo "============================================================"
echo "  Fitness Fuzion — First Reply Demo"
echo "  Author: Daylon Naido · BCComputers"
echo "============================================================"
echo ""

# Check if server is running
if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/docs" | grep -q "200"; then
  echo ">>> Posting fake lead to $BASE_URL/webhook/form ..."
  RESPONSE=$(curl -s -X POST "$BASE_URL/webhook/form" \
    -H "Content-Type: application/json" \
    -d '{
      "name":    "Jane Demo",
      "contact": "jane@example.com",
      "message": "Hi, I saw your ad and would love to try a class. When is it available?"
    }')
  echo "Webhook response: $RESPONSE"
  echo ""
  sleep 1

  echo ">>> Fetching lead log from $BASE_URL/admin/leads ..."
  LEADS=$(curl -s "$BASE_URL/admin/leads" -H "X-Admin-Token: $ADMIN_TOKEN")

  python3 -c "
import json, sys
leads = json.loads('''$LEADS''')
if not leads:
    print('No leads found.')
    sys.exit(0)
lead = leads[0]
print()
print('============================================================')
print('  STORED LEAD ROW:')
print('============================================================')
print(f'Lead ID            : {lead[\"id\"]}')
print(f'Channel            : {lead[\"channel\"]}')
print(f'Sender             : {lead[\"sender_name\"]} <{lead[\"sender_id\"]}>')
print(f'Message            : {lead[\"text\"]}')
print(f'Replied Within SLA : {lead[\"replied_within_sla\"]}')
print(f'Reply Sent At      : {lead[\"reply_sent_at\"]}')
print()
print('----------------- AUTO-REPLY SENT -----------------')
print(lead[\"reply_text\"])
print()
print('----------- OWNER NOTIFICATION PAYLOAD ------------')
print(f'[NEW LEAD #{lead[\"id\"]}] [{lead[\"channel\"].upper()}]')
print(f'From: {lead[\"sender_name\"]} <{lead[\"sender_id\"]}>')
print(f'Message: {lead[\"text\"]}')
print(f'Auto-Reply: {lead[\"reply_text\"]}')
print('Dispatched to: WhatsApp (+27824673870) and Email (info@fitnessfuzion.co.za)')
print('============================================================')
"
else
  echo "Server not running on $BASE_URL. Running in-process demonstration..."
  python3 -c "
import json
import time
from fastapi.testclient import TestClient
from main import app
import config
import database as db

client = TestClient(app)
payload = {
    'name': 'Jane Demo',
    'contact': 'jane@example.com',
    'message': 'Hi, I saw your ad and would love to try a class. When is it available?'
}
resp = client.post('/webhook/form', json=payload)
print('Webhook Response Status:', resp.status_code)
time.sleep(0.5)

token = config.cfg.admin_token or 'dev-admin-token'
admin_resp = client.get('/admin/leads', headers={'X-Admin-Token': token})
leads = admin_resp.json()
if leads:
    lead = leads[0]
    print()
    print('============================================================')
    print('  STORED LEAD ROW:')
    print('============================================================')
    print(f'Lead ID            : {lead[\"id\"]}')
    print(f'Channel            : {lead[\"channel\"]}')
    print(f'Sender             : {lead[\"sender_name\"]} <{lead[\"sender_id\"]}>')
    print(f'Message            : {lead[\"text\"]}')
    print(f'Replied Within SLA : {lead[\"replied_within_sla\"]}')
    print(f'Reply Sent At      : {lead[\"reply_sent_at\"]}')
    print()
    print('----------------- AUTO-REPLY SENT -----------------')
    print(lead[\"reply_text\"])
    print()
    print('----------- OWNER NOTIFICATION PAYLOAD ------------')
    print(f'[NEW LEAD #{lead[\"id\"]}] [{lead[\"channel\"].upper()}]')
    print(f'From: {lead[\"sender_name\"]} <{lead[\"sender_id\"]}>')
    print(f'Message: {lead[\"text\"]}')
    print(f'Auto-Reply: {lead[\"reply_text\"]}')
    print('Dispatched to: WhatsApp (+27824673870) and Email (info@fitnessfuzion.co.za)')
    print('============================================================')
"
fi
