import json
import logging
from contextvars import ContextVar
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ── Security header capture via ASGI middleware ─────────────────────────────
HEADER_PREFIX = "x-amzn-bedrock-agentcore-runtime-custom-"
SECURITY_KEYS = ["end-user-id", "end-user-dept", "end-user-role"]
_security_ctx: ContextVar[dict] = ContextVar("security_ctx", default={})


class SecurityHeaderMiddleware:
    """Raw ASGI middleware that captures security headers and body _meta into a ContextVar."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Try headers first
            headers = dict((k.decode(), v.decode()) for k, v in scope.get("headers", []))
            ctx = {}
            for key in SECURITY_KEYS:
                value = headers.get(f"{HEADER_PREFIX}{key}", "")
                if value:
                    ctx[key] = value
            # If no headers found, try reading _meta from JSON body
            if not ctx:
                # Read first message to get body
                first_msg = await receive()
                body_data = first_msg.get("body", b"")
                try:
                    parsed = json.loads(body_data)
                    meta = None
                    if isinstance(parsed, dict):
                        meta = parsed.get("params", {}).get("_meta", {}).get("security_context", {})
                    if meta:
                        ctx = meta
                        logger.info(f"Security context from body _meta: {json.dumps(ctx)}")
                except Exception:
                    pass
                # Replay the buffered message
                replayed = False
                orig_receive = receive
                async def replay_receive():
                    nonlocal replayed
                    if not replayed:
                        replayed = True
                        return first_msg
                    return await orig_receive()
                receive = replay_receive
            _security_ctx.set(ctx)
            if ctx:
                logger.info(f"Security context set: {json.dumps(ctx)}")
        await self.app(scope, receive, send)


mcp = FastMCP(host="0.0.0.0", stateless_http=True)


def get_security_context() -> dict:
    return _security_ctx.get()


@mcp.tool()
def get_property_details(property_id: str) -> str:
    """Get details for a real estate property by ID"""
    security_ctx = get_security_context()
    logger.info(f"get_property_details | caller={json.dumps(security_ctx)}")
    properties = {
        "PROP001": {"id": "PROP001", "address": "123 Main St, Austin TX", "type": "Commercial",
                    "status": "Under Construction", "completion_pct": 65, "contractor": "BuildCo Inc"},
        "PROP002": {"id": "PROP002", "address": "456 Oak Ave, Dallas TX", "type": "Residential",
                    "status": "Planning", "completion_pct": 0, "contractor": "TexasBuild LLC"},
    }
    result = properties.get(property_id, {"error": f"Property {property_id} not found"})
    return json.dumps({"_security_context": security_ctx, **result}, indent=2)


@mcp.tool()
def list_active_projects(status: str = "all") -> str:
    """List active real estate projects, optionally filtered by status"""
    security_ctx = get_security_context()
    logger.info(f"list_active_projects | caller={json.dumps(security_ctx)}")
    projects = [
        {"id": "PROJ001", "name": "Downtown Office Tower", "status": "Under Construction", "budget_usd": 5000000},
        {"id": "PROJ002", "name": "Riverside Condos", "status": "Planning", "budget_usd": 12000000},
        {"id": "PROJ003", "name": "Industrial Park Phase 2", "status": "Completed", "budget_usd": 3500000},
    ]
    filtered = projects if status == "all" else [p for p in projects if p["status"].lower() == status.lower()]
    return json.dumps({"_security_context": security_ctx, "projects": filtered}, indent=2)


@mcp.tool()
def get_project_budget_summary(project_id: str) -> str:
    """Get budget summary for a real estate project"""
    security_ctx = get_security_context()
    logger.info(f"get_project_budget_summary | caller={json.dumps(security_ctx)}")
    budgets = {
        "PROJ001": {"allocated": 5000000, "spent": 3250000, "remaining": 1750000, "variance_pct": -2.1},
        "PROJ002": {"allocated": 12000000, "spent": 450000, "remaining": 11550000, "variance_pct": 0.0},
        "PROJ003": {"allocated": 3500000, "spent": 3480000, "remaining": 20000, "variance_pct": -0.6},
    }
    result = budgets.get(project_id, {"error": f"Project {project_id} not found"})
    return json.dumps({"_security_context": security_ctx, **result}, indent=2)


if __name__ == "__main__":
    # Wrap the MCP ASGI app with security header middleware
    import uvicorn
    app = mcp.streamable_http_app()
    app = SecurityHeaderMiddleware(app)
    uvicorn.run(app, host="0.0.0.0", port=8000)
