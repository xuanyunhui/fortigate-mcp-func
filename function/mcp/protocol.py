"""MCP JSON-RPC 2.0 protocol helpers."""
from typing import Any, Dict

# JSON-RPC 2.0 error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def make_response(req_id: Any, result: Any) -> Dict[str, Any]:
    """Build a JSON-RPC 2.0 success response."""
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def make_error(req_id: Any, code: int, message: str) -> Dict[str, Any]:
    """Build a JSON-RPC 2.0 error response."""
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def make_initialize_result() -> Dict[str, Any]:
    """Build the MCP initialize result payload."""
    return {
        "protocolVersion": "2025-03-26",
        "capabilities": {
            "tools": {},
        },
        "serverInfo": {
            "name": "fortigate-mcp-func",
            "version": "0.1.0",
        },
    }
