"""Knative Function entry point — ASGI handler for MCP over Streamable HTTP."""
import json
import logging

from .config.env_loader import load_devices_from_env
from .core.manager import FortiGateManager
from .mcp.handler import MCPHandler
from .mcp.protocol import PARSE_ERROR, make_error
from .tools import ToolRegistry
from .tools.device import register_device_tools
from .tools.firewall import register_firewall_tools
from .tools.network import register_network_tools
from .tools.routing import register_routing_tools
from .tools.virtual_ip import register_virtual_ip_tools

logger = logging.getLogger(__name__)


def new():
    return Function()


class Function:
    def __init__(self):
        self._handler = None
        self._ready = False

    async def handle(self, scope, receive, send):
        if self._handler is None:
            await self._send_plain(send, 503, b"Service Unavailable")
            return

        method = scope.get("method", "GET")

        if method == "GET":
            await self._send_plain(send, 405, b"Method Not Allowed")
            return

        if method == "DELETE":
            await self._send_plain(send, 202, b"")
            return

        # POST — read body
        body = b""
        while True:
            msg = await receive()
            body += msg.get("body", b"")
            if not msg.get("more_body", False):
                break

        # Parse JSON
        try:
            request = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            error_resp = make_error(None, PARSE_ERROR, "Parse error")
            await self._send_json(send, 200, error_resp)
            return

        # Dispatch
        response = await self._handler.dispatch(request)

        if response is None:
            # Notification — no body
            await self._send_plain(send, 202, b"")
        else:
            await self._send_json(send, 200, response)

    def start(self, cfg):
        device_configs = load_devices_from_env(cfg)
        manager = FortiGateManager(device_configs)

        registry = ToolRegistry()
        register_device_tools(registry, manager)
        register_firewall_tools(registry, manager)
        register_network_tools(registry, manager)
        register_routing_tools(registry, manager)
        register_virtual_ip_tools(registry, manager)

        self._handler = MCPHandler(registry)
        self._ready = True
        logger.info("Function started with %d devices", len(device_configs))

    def stop(self):
        logger.info("Function stopping")

    def alive(self):
        return True, "Alive"

    def ready(self):
        if not self._ready:
            return False, "Not initialized"
        return True, "Ready"

    @staticmethod
    async def _send_plain(send, status, body):
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [[b"content-type", b"text/plain"]],
        })
        await send({"type": "http.response.body", "body": body})

    @staticmethod
    async def _send_json(send, status, data):
        body = json.dumps(data).encode()
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [
                [b"content-type", b"application/json"],
            ],
        })
        await send({"type": "http.response.body", "body": body})
