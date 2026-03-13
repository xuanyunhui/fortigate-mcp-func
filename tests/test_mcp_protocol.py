"""Tests for MCP protocol helpers."""
import pytest
from function.mcp.protocol import (
    make_response,
    make_error,
    make_initialize_result,
    PARSE_ERROR,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)


class TestMakeResponse:
    def test_basic_response(self):
        resp = make_response(1, {"key": "value"})
        assert resp == {"jsonrpc": "2.0", "id": 1, "result": {"key": "value"}}

    def test_string_id(self):
        resp = make_response("abc", {})
        assert resp["id"] == "abc"


class TestMakeError:
    def test_method_not_found(self):
        resp = make_error(1, METHOD_NOT_FOUND, "Method not found")
        assert resp == {"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "Method not found"}}

    def test_parse_error_null_id(self):
        resp = make_error(None, PARSE_ERROR, "Parse error")
        assert resp["id"] is None
        assert resp["error"]["code"] == -32700

    def test_all_error_codes(self):
        assert PARSE_ERROR == -32700
        assert INVALID_REQUEST == -32600
        assert METHOD_NOT_FOUND == -32601
        assert INVALID_PARAMS == -32602
        assert INTERNAL_ERROR == -32603


class TestMakeInitializeResult:
    def test_returns_capabilities(self):
        result = make_initialize_result()
        assert result["protocolVersion"] == "2025-03-26"
        assert "tools" in result["capabilities"]
        assert result["serverInfo"]["name"] == "fortigate-mcp-func"
