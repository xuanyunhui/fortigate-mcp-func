"""MCP JSON-RPC 2.0 handler."""
import logging
from typing import Any, Dict, List, Optional

from .protocol import (
    INTERNAL_ERROR,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    make_error,
    make_initialize_result,
    make_response,
)

logger = logging.getLogger(__name__)


class MCPHandler:
    def __init__(self, tool_registry):
        self._registry = tool_registry

    async def dispatch(self, msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if msg.get("jsonrpc") != "2.0":
            return make_error(msg.get("id"), INVALID_REQUEST, "Invalid JSON-RPC version")

        method = msg.get("method")
        if method is None:
            return make_error(msg.get("id"), INVALID_REQUEST, "Missing method")

        req_id = msg.get("id")
        params = msg.get("params", {})

        if method.startswith("notifications/"):
            return None

        if method == "initialize":
            return make_response(req_id, make_initialize_result())

        if method == "ping":
            return make_response(req_id, {})

        if method == "tools/list":
            tools = self._registry.list_all()
            return make_response(req_id, {"tools": tools})

        if method == "tools/call":
            return await self._handle_tools_call(req_id, params)

        return make_error(req_id, METHOD_NOT_FOUND, f"Method not found: {method}")

    async def _handle_tools_call(self, req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        tool_fn = self._registry.get(tool_name)
        if tool_fn is None:
            return make_response(req_id, {
                "content": [{"type": "text", "text": f"Error: Unknown tool '{tool_name}'"}],
                "isError": True,
            })

        try:
            content = await tool_fn(arguments)
            return make_response(req_id, {"content": content})
        except Exception as e:
            logger.exception("Tool %s failed", tool_name)
            return make_response(req_id, {
                "content": [{"type": "text", "text": f"Error: {e}"}],
                "isError": True,
            })
