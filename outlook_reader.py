import os

from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.users.item.messages.messages_request_builder import (
    MessagesRequestBuilder,
)


def _get_graph_client() -> tuple[GraphServiceClient, str]:
    """Create a Graph client using Azure AD client credentials."""
    tenant_id = os.environ["AZURE_TENANT_ID"]
    client_id = os.environ["AZURE_CLIENT_ID"]
    client_secret = os.environ["AZURE_CLIENT_SECRET"]
    user_email = os.environ["OUTLOOK_USER_EMAIL"]

    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
    scopes = ["https://graph.microsoft.com/.default"]
    client = GraphServiceClient(credentials=credential, scopes=scopes)
    return client, user_email


async def fetch_unread_emails(max_count: int = 5) -> list[dict]:
    """Fetch the latest unread emails from the configured Outlook mailbox.

    Returns a list of dicts with keys: subject, body_text, from_address, received_at, message_id.
    """
    client, user_email = _get_graph_client()

    query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
        filter="isRead eq false",
        top=max_count,
        orderby=["receivedDateTime desc"],
        select=["id", "subject", "body", "from", "receivedDateTime"],
    )
    config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
        query_parameters=query_params,
    )

    messages = await client.users.by_user_id(user_email).messages.get(
        request_configuration=config,
    )

    results = []
    if messages and messages.value:
        for msg in messages.value:
            from_addr = ""
            if msg.from_ and msg.from_.email_address:
                from_addr = msg.from_.email_address.address or ""

            body_text = ""
            if msg.body:
                body_text = msg.body.content or ""

            results.append(
                {
                    "subject": msg.subject or "",
                    "body_text": body_text,
                    "from_address": from_addr,
                    "received_at": str(msg.received_date_time or ""),
                    "message_id": msg.id or "",
                }
            )

    return results


async def mark_as_read(message_id: str) -> None:
    """Mark a message as read in the configured Outlook mailbox."""
    from msgraph.generated.models.message import Message

    client, user_email = _get_graph_client()

    request_body = Message()
    request_body.is_read = True

    await client.users.by_user_id(user_email).messages.by_message_id(
        message_id
    ).patch(request_body)
