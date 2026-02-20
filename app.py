import re

from dotenv import load_dotenv

from microsoft_agents.hosting.core import MemoryStorage
from microsoft_agents.hosting.core.app import AgentApplication, ApplicationOptions
from microsoft_agents.hosting.core.app.state import TurnState
from microsoft_agents.hosting.core import TurnContext

from email_parser import parse_attendance_exception
from outlook_reader import fetch_latest_emails
from start_server import start

load_dotenv()

HELP_TEXT = (
    "**Attendance Exception Parser**\n\n"
    "Send me an attendance exception email and I'll parse it for you.\n\n"
    "**Commands:**\n"
    "- `/fetch` — Fetch and parse latest unread emails from Outlook\n"
    "- `/fetch 3` — Fetch up to 3 unread emails\n"
    "- `/help` — Show this help message\n\n"
    "**Supported exception types:**\n"
    "- Late-In / Late arrival\n"
    "- Early-Out / Leaving early\n"
    "- Half-Day\n"
    "- Work-From-Home (WFH)\n"
    "- Leave (sick, casual, day off)\n\n"
    "**Example email:**\n"
    "```\n"
    "Subject: Late-in request for 17/02/2026\n"
    "Hi, I will be coming late today due to a doctor's appointment.\n"
    "Expected arrival: 11:00 AM. Employee ID: EMP1234\n"
    "```\n"
)

storage = MemoryStorage()
app = AgentApplication[TurnState](options=ApplicationOptions(storage=storage))


@app.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, state: TurnState):
    await context.send_activity(
        "Welcome! I'm the **Attendance Exception Parser Agent**.\n\n"
        "Paste an attendance exception email and I'll extract the details.\n"
        "Type `/help` to see supported formats."
    )


@app.message("/help")
async def on_help(context: TurnContext, state: TurnState):
    await context.send_activity(HELP_TEXT)


@app.message(re.compile(r"^/fetch(?:\s+(\d+))?$"))
async def on_fetch(context: TurnContext, state: TurnState):
    text = (context.activity.text or "").strip()
    # Parse optional count from "/fetch N"
    match = re.match(r"^/fetch(?:\s+(\d+))?$", text)
    max_count = int(match.group(1)) if match and match.group(1) else 5

    try:
        emails = await fetch_latest_emails(max_count=max_count)
    except KeyError as e:
        await context.send_activity(
            f"Missing environment variable: {e}. "
            "Please configure `.env` with AZURE_TENANT_ID, AZURE_CLIENT_ID, "
            "AZURE_CLIENT_SECRET, and OUTLOOK_USER_EMAIL."
        )
        return
    except Exception as e:
        await context.send_activity(f"Error fetching emails: {e}")
        return

    if not emails:
        await context.send_activity("No emails found in the inbox.")
        return

    for i, email in enumerate(emails, 1):
        combined_text = f"Subject: {email['subject']}\n{email['body_text']}"
        result = parse_attendance_exception(combined_text)

        header = (
            f"**Email {i}/{len(emails)}**\n"
            f"- **From:** {email['from_address']}\n"
            f"- **Subject:** {email['subject']}\n"
            f"- **Received:** {email['received_at']}\n\n"
        )

        if result.exception_type or result.date or result.reason:
            await context.send_activity(header + result.to_summary())
        else:
            await context.send_activity(
                header + "No attendance exception detected in this email."
            )


@app.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    text = context.activity.text or ""
    if not text.strip():
        await context.send_activity("Please send some email text for me to parse.")
        return

    result = parse_attendance_exception(text)

    if not result.exception_type and not result.date and not result.reason:
        await context.send_activity(
            "I couldn't identify an attendance exception in your message.\n"
            "Type `/help` to see supported formats."
        )
        return

    await context.send_activity(result.to_summary())


if __name__ == "__main__":
    start(app)
