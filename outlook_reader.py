import json
import os
import sys
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _build_server_params() -> StdioServerParameters:
    """Map AZURE_* env vars to what mcp-outlook expects and return server params."""
    env = os.environ.copy()
    env["CLIENT_ID"] = os.environ["AZURE_CLIENT_ID"]
    env["CLIENT_SECRET"] = os.environ["AZURE_CLIENT_SECRET"]
    env["TENANT_ID"] = os.environ["AZURE_TENANT_ID"]

    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_outlook_server.server"],
        env=env,
    )


@asynccontextmanager
async def _mcp_session():
    """Async context manager that yields an initialized MCP ClientSession."""
    server_params = _build_server_params()
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


async def fetch_latest_emails(max_count: int = 5) -> list[dict]:
    """Fetch the latest emails from the configured Outlook mailbox.

    Returns a list of dicts with keys: subject, body_text, from_address,
    received_at, message_id.
    """
    user_email = os.environ["OUTLOOK_USER_EMAIL"]

    async with _mcp_session() as session:
        result = await session.call_tool(
            "Search_Outlook_Emails",
            {
                "user_email": user_email,
                "top": max_count,
                "folders": ["Inbox"],
            },
        )

    emails: list[dict] = []
    for block in result.content:
        text = getattr(block, "text", None)
        if not text:
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue

        # data may be a list of emails or a single email dict
        items = data if isinstance(data, list) else [data]
        for item in items:
            # mcp-outlook structured output uses Spanish field names
            from_addr = item.get("remitente", "")
            body_text = item.get("cuerpo", "")
            subject = item.get("asunto", "")
            received_at = item.get("fecha", "")
            message_id = item.get("id", "")

            # Fall back to English keys if present (e.g. from KQL search)
            if not subject:
                subject = item.get("subject", "")
            if not from_addr:
                from_field = item.get("from", {})
                if isinstance(from_field, dict):
                    email_address = from_field.get("emailAddress", {})
                    from_addr = email_address.get("address", "")
                elif isinstance(from_field, str):
                    from_addr = from_field
            if not body_text:
                body_field = item.get("body", {})
                if isinstance(body_field, dict):
                    body_text = body_field.get("content", "")
                elif isinstance(body_field, str):
                    body_text = body_field
            if not received_at:
                received_at = item.get("receivedDateTime", "")
            if not message_id:
                message_id = item.get("id", "")

            emails.append(
                {
                    "subject": subject,
                    "body_text": body_text,
                    "from_address": from_addr,
                    "received_at": received_at,
                    "message_id": message_id,
                }
            )

    return emails[:max_count]


async def mark_as_read(message_id: str) -> None:
    """Mark a message as read (no-op — mcp-outlook doesn't expose this tool)."""
    pass
