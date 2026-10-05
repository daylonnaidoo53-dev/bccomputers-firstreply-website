# demo.ps1 — Windows PowerShell demonstration
# Author: Daylon Naido · BCComputers

param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$AdminToken = "dev-admin-token"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Fitness Fuzion — First Reply System Demo" -ForegroundColor Cyan
Write-Host "  Author: Daylon Naido · BCComputers" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$serverRunning = $false
try {
    $check = Invoke-WebRequest -Uri "$BaseUrl/docs" -Method Get -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
    if ($null -ne $check -and $check.StatusCode -eq 200) {
        $serverRunning = $true
    }
} catch {
    $serverRunning = $false
}

if ($serverRunning) {
    Write-Host "[INFO] Posting fake lead to $BaseUrl/webhook/form via HTTP..." -ForegroundColor Green
    $payloadObj = @{
        name    = "Jane Demo"
        contact = "jane@example.com"
        message = "Hi, I saw your ad and would love to try a class. When is it available?"
    }
    $bodyJson = $payloadObj | ConvertTo-Json

    $resp = Invoke-RestMethod -Uri "$BaseUrl/webhook/form" -Method Post -Body $bodyJson -ContentType "application/json"
    $respStr = $resp | ConvertTo-Json -Compress
    Write-Host "Webhook Response: $respStr"
    Start-Sleep -Seconds 1

    Write-Host "[INFO] Fetching lead from $BaseUrl/admin/leads..." -ForegroundColor Green
    $headers = @{ "X-Admin-Token" = $AdminToken }
    $leads = Invoke-RestMethod -Uri "$BaseUrl/admin/leads" -Method Get -Headers $headers

    if ($leads.Count -gt 0) {
        $lead = $leads[0]
        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Yellow
        Write-Host "  STORED LEAD ROW:" -ForegroundColor Yellow
        Write-Host "============================================================" -ForegroundColor Yellow
        Write-Host "Lead ID            : $($lead.id)"
        Write-Host "Channel            : $($lead.channel)"
        Write-Host "Sender             : $($lead.sender_name) [$($lead.sender_id)]"
        Write-Host "Message            : $($lead.text)"
        Write-Host "Replied Within SLA : $($lead.replied_within_sla)"
        Write-Host "Reply Sent At      : $($lead.reply_sent_at)"
        Write-Host ""
        Write-Host "----------------- AUTO-REPLY SENT -----------------" -ForegroundColor Green
        Write-Host $lead.reply_text
        Write-Host ""
        Write-Host "----------- OWNER NOTIFICATION PAYLOAD ------------" -ForegroundColor Cyan
        Write-Host "[NEW LEAD #$($lead.id)] [$($lead.channel.ToUpper())]"
        Write-Host "From: $($lead.sender_name) [$($lead.sender_id)]"
        Write-Host "Message: $($lead.text)"
        Write-Host "Auto-Reply: $($lead.reply_text)"
        Write-Host "Dispatched to: WhatsApp (+27824673870) and Email (info@fitnessfuzion.co.za)"
        Write-Host "============================================================" -ForegroundColor Cyan
    }
}
else {
    Write-Host "Server not running on $BaseUrl. Running in-process demonstration..." -ForegroundColor Yellow
    $py = ".\.venv\Scripts\python.exe"
    if (-not (Test-Path $py)) {
        $py = "python"
    }

    $script = @'
import json
import time
from fastapi.testclient import TestClient
from main import app
import config
import database as db

client = TestClient(app)
payload = {
    "name": "Jane Demo",
    "contact": "jane@example.com",
    "message": "Hi, I saw your ad and would love to try a class. When is it available?"
}
resp = client.post("/webhook/form", json=payload)
print("Webhook Response Status:", resp.status_code)
time.sleep(0.5)

token = config.cfg.admin_token or "dev-admin-token"
admin_resp = client.get("/admin/leads", headers={"X-Admin-Token": token})
leads = admin_resp.json()
if leads:
    lead = leads[0]
    print("\n============================================================")
    print("  STORED LEAD ROW:")
    print("============================================================\n")
    print(f"Lead ID            : {lead['id']}")
    print(f"Channel            : {lead['channel']}")
    print(f"Sender             : {lead['sender_name']} <{lead['sender_id']}>")
    print(f"Message            : {lead['text']}")
    print(f"Replied Within SLA : {lead['replied_within_sla']}")
    print(f"Reply Sent At      : {lead['reply_sent_at']}")
    print("\n----------------- AUTO-REPLY SENT -----------------\n")
    print(lead['reply_text'])
    print("\n----------- OWNER NOTIFICATION PAYLOAD ------------\n")
    print(f"[NEW LEAD #{lead['id']}] [{lead['channel'].upper()}]")
    print(f"From: {lead['sender_name']} <{lead['sender_id']}>")
    print(f"Message: {lead['text']}")
    print(f"Auto-Reply: {lead['reply_text']}")
    print("Dispatched to: WhatsApp (+27824673870) and Email (info@fitnessfuzion.co.za)")
    print("============================================================\n")
'@
    $script | & $py
}
