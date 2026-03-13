"""MCP protocol constants and message builders."""
from typing import Any, Dict, Optional, Union

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

PROTOCOL_VERSION = "2025-03-26"

SERVER_INFO = {
    "name": "fortigate-mcp-func",
    "version": "0.1.0",
}


def make_response(req_id: Union[str, int, None], result: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def make_error(req_id: Union[str, int, None], code: int, message: str) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def make_initialize_result() -> Dict[str, Any]:
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": SERVER_INFO,
    }
