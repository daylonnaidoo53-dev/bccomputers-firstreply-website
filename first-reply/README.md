# First Reply Service — Fitness Fuzion

**Author:** Daylon Naido · BCComputers  
Answers every incoming lead within 2 minutes and hands the thread to the owner.  
*It answers the door. It does not run the company.*

---

## Run locally in 3 commands

```bash
# 1. Install dependencies (Python 3.12+)
pip install -r requirements.txt

# 2. Copy the example env and fill in your secrets
cp .env.example .env

# 3. Start the server
uvicorn main:app --reload
```

Then open a second terminal and run the demo:

- **Windows PowerShell:** `.\demo.ps1`
- **Linux / macOS:** `bash demo.sh`

A fake lead is submitted, an auto-reply is built strictly from `config.yaml`, and the owner notification payload is printed.

---

## Run the tests

```bash
pytest -v
```

All 24 tests run against an isolated SQLite test database and mock external dispatchers — zero network calls.

---

## Layout & Architecture

| File / Folder | Purpose |
|---|---|
| `main.py` | FastAPI application, lifespan handler, route registration |
| `config.py` | Typed configuration loader (`config.yaml` + `.env`) |
| `database.py` | SQLite schema and operations (`leads` and `senders` tables) |
| `reply.py` | Deterministic reply template builder & LLM safety validator |
| `handoff.py` | Owner notification & subsequent message forwarding |
| `app/adapters/base.py` | Abstract `BaseAdapter` interface & `InboundMessage` dataclass |
| `app/adapters/form.py` | Website contact form adapter |
| `app/adapters/whatsapp.py` | WhatsApp Cloud API adapter with fail-closed HMAC verification |
| `app/adapters/instagram.py` | Instagram DM adapter stub with step-by-step implementation guide |
| `app/adapters/email.py` | Inbound email adapter stub with step-by-step implementation guide |
| `app/adapters/email_util.py` | Shared asynchronous SMTP dispatch helper |
| `app/routes/webhooks.py` | Inbound webhook endpoints (`/webhook/{channel}`) |
| `app/routes/admin.py` | Admin inspection endpoints (`/admin/leads`, `/admin/leads.csv`) |
| `tests/` | 24 pytest verification tests |
| `demo.ps1` / `demo.sh` | End-to-end local test scripts |

---

## Admin API

Both admin endpoints require the `X-Admin-Token` header matching `ADMIN_TOKEN` in `.env`:

| Endpoint | Method | Description |
|---|---|---|
| `/admin/leads` | GET | JSON list of all leads (newest first) |
| `/admin/leads.csv` | GET | Download CSV log file for weekly reporting |

---

## Connecting Meta Cloud API (WhatsApp Business)

### Step 1 — Create Meta App
1. Go to [developers.facebook.com](https://developers.facebook.com) → **My Apps → Create App**.
2. Select **Business** as the application type.
3. Name your app (e.g. `Fitness Fuzion First Reply`).
4. Add the **WhatsApp** product.

### Step 2 — Retrieve Credentials
In **WhatsApp → API Setup**:
- **Phone Number ID**: Copy into `WHATSAPP_PHONE_NUMBER_ID` in `.env`.
- **Access Token**: Generate a permanent System User token in Business Settings and paste into `WHATSAPP_ACCESS_TOKEN`.
- **App Secret**: Navigate to **App Settings → Basic** → retrieve App Secret and paste into `WHATSAPP_APP_SECRET`.

### Step 3 — Configure Webhook
1. Under **WhatsApp → Configuration → Webhook**, click **Edit**.
2. **Callback URL**: `https://<your-domain>/webhook/whatsapp`
3. **Verify Token**: Generate a random secure string and set it in both Meta and `WHATSAPP_VERIFY_TOKEN` in `.env`.
4. Subscribe to the `messages` event.
5. Click **Verify and Save**. Meta will call `GET /webhook/whatsapp` to verify the handshake.

---

## Deployment Notes

### Render
1. Connect repository to [render.com](https://render.com).
2. Create a new **Web Service**.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Configure all variables from `.env.example` in the Render Environment tab.

### Railway
1. Import repo into [railway.app](https://railway.app).
2. Set start command to `uvicorn main:app --host 0.0.0.0 --port $PORT`.
3. Add environment variables in Railway dashboard.

### $5 VPS (Ubuntu / Debian)
```bash
git clone <repo> /opt/first-reply
cd /opt/first-reply
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env
pip install gunicorn
gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```
Use Nginx or Caddy reverse proxy for SSL termination.
