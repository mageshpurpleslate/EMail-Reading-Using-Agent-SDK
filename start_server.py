from aiohttp import web

from microsoft_agents.hosting.aiohttp import CloudAdapter, jwt_authorization_middleware
from microsoft_agents.hosting.core.authorization import AgentAuthConfiguration


def start(agent):
    """Start the aiohttp web server with the given agent."""
    adapter = CloudAdapter()

    async def messages(req: web.Request) -> web.Response:
        return await adapter.process(req, agent)

    # Anonymous auth config (no CLIENT_ID) for local testing
    auth_config = AgentAuthConfiguration()

    app = web.Application(middlewares=[jwt_authorization_middleware])
    app["agent_configuration"] = auth_config
    app.router.add_post("/api/messages", messages)

    print("Agent server starting on http://localhost:3978/api/messages")
    web.run_app(app, host="localhost", port=3978)
