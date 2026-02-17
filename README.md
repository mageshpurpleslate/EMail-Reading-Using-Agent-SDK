# Email Parser Agent — Attendance Exception Requests

A POC agent built with the Microsoft 365 Agents SDK (Python) that parses attendance exception emails and extracts structured data for an approval workflow.

## Prerequisites

- Python 3.10+
- Node.js (for the Teams App Test Tool / playground)
- Azure AD App Registration with **Mail.Read** application permission

## Azure AD Setup

1. Go to [Azure Portal](https://portal.azure.com) → **App Registrations** → **New Registration**
2. Note the **Application (client) ID** and **Directory (tenant) ID**
3. Under **Certificates & secrets** → **New client secret** — copy the secret value
4. Under **API Permissions** → **Add a permission** → **Microsoft Graph** → **Application permissions** → add **Mail.Read**
5. Click **Grant admin consent** for the tenant

## Setup

```bash
cd /Users/magesh/Workspace/EMail_Reading_Using_Agent_SDK
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure `.env`

Create a `.env` file in the project root with your Azure AD credentials:

```
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-client-id>
AZURE_CLIENT_SECRET=<your-client-secret>
OUTLOOK_USER_EMAIL=<user@yourdomain.com>
```

| Variable | Where to find it |
|---|---|
| `AZURE_TENANT_ID` | Azure Portal → App Registrations → your app → Overview → **Directory (tenant) ID** |
| `AZURE_CLIENT_ID` | Azure Portal → App Registrations → your app → Overview → **Application (client) ID** |
| `AZURE_CLIENT_SECRET` | Azure Portal → App Registrations → your app → Certificates & secrets → **Client secret Value** (copy immediately after creating — it's only shown once) |
| `OUTLOOK_USER_EMAIL` | The email address of the mailbox to read from (e.g. `user@yourdomain.com`). Required for the app-only client credentials flow. |

## Running

```bash
python app.py
```

The server starts on `http://localhost:3978`.

## Testing with the Playground

```bash
npm install -g @microsoft/teams-app-test-tool
teamsapptester
```

This opens a browser UI. You can:
- **Paste** sample attendance exception emails and the agent responds with parsed structured data
- Send `/fetch` to fetch and parse the latest 5 unread emails from Outlook
- Send `/fetch 3` to fetch up to 3 unread emails
- Send `/help` to see supported formats

## Testing with curl (expectReplies mode)

```bash
curl -X POST http://localhost:3978/api/messages \
  -H "Content-Type: application/json" \
  -d '{
    "type": "message",
    "text": "/fetch",
    "deliveryMode": "expectReplies"
  }'
```

## Supported Exception Types

| Type | Keywords |
|---|---|
| Late-In | late-in, late arrival, coming late |
| Early-Out | early-out, leaving early |
| Half-Day | half-day, half day |
| Work-From-Home | work from home, WFH |
| Leave | leave request, sick leave, casual leave, day off |

## Sample Emails

**Example 1:**
```
Subject: Late-in request for 17/02/2026
Hi, I will be coming late today due to a doctor's appointment.
Expected arrival: 11:00 AM. Employee ID: EMP1234
```

**Example 2:**
```
Request for attendance exception - Late arrival on 18th Feb
Due to car breakdown, I will be approximately 2 hours late tomorrow.
- John Smith (EMP5678)
```

## Project Structure

```
app.py              — Main entry point, agent definition
start_server.py     — aiohttp server setup
email_parser.py     — Attendance exception email parsing logic
outlook_reader.py   — Microsoft Graph API email fetcher
models.py           — Data models (AttendanceException)
requirements.txt    — Python dependencies
.env                — Azure AD credentials (not committed)
```
