"""Tests for MCP JSON-RPC handler."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from function.mcp.handler import MCPHandler


def _make_handler(tools=None):
    registry = MagicMock()
    registry.list_all.return_value = tools or []
    registry.get.return_value = None
    return MCPHandler(registry)


class TestInitialize:
    @pytest.mark.asyncio
    async def test_initialize_returns_capabilities(self):
        handler = _make_handler()
        resp = await handler.dispatch({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        assert resp["id"] == 1
        assert "protocolVersion" in resp["result"]
        assert "capabilities" in resp["result"]
        assert "serverInfo" in resp["result"]


class TestPing:
    @pytest.mark.asyncio
    async def test_ping_returns_empty_result(self):
        handler = _make_handler()
        resp = await handler.dispatch({"jsonrpc": "2.0", "id": 2, "method": "ping"})
        assert resp == {"jsonrpc": "2.0", "id": 2, "result": {}}


class TestNotification:
    @pytest.mark.asyncio
    async def test_initialized_notification_returns_none(self):
        handler = _make_handler()
        resp = await handler.dispatch({"jsonrpc": "2.0", "method": "notifications/initialized"})
        assert resp is None


class TestToolsList:
    @pytest.mark.asyncio
    async def test_tools_list_returns_tools(self):
        tools = [{"name": "test_tool", "description": "A test", "inputSchema": {"type": "object", "properties": {}}}]
        handler = _make_handler(tools)
        resp = await handler.dispatch({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
        assert resp["result"]["tools"] == tools


class TestToolsCall:
    @pytest.mark.asyncio
    async def test_call_existing_tool(self):
        mock_tool = AsyncMock(return_value=[{"type": "text", "text": "ok"}])
        registry = MagicMock()
        registry.get.return_value = mock_tool
        handler = MCPHandler(registry)
        resp = await handler.dispatch({
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "test_tool", "arguments": {"a": 1}}
        })
        assert resp["result"]["content"] == [{"type": "text", "text": "ok"}]
        mock_tool.assert_awaited_once_with({"a": 1})

    @pytest.mark.asyncio
    async def test_call_unknown_tool(self):
        handler = _make_handler()
        resp = await handler.dispatch({
            "jsonrpc": "2.0", "id": 5, "method": "tools/call",
            "params": {"name": "nonexistent", "arguments": {}}
        })
        assert resp["result"]["isError"] is True

    @pytest.mark.asyncio
    async def test_call_tool_exception_returns_error(self):
        async def failing_tool(args):
            raise RuntimeError("boom")
        registry = MagicMock()
        registry.get.return_value = failing_tool
        handler = MCPHandler(registry)
        resp = await handler.dispatch({
            "jsonrpc": "2.0", "id": 6, "method": "tools/call",
            "params": {"name": "bad_tool", "arguments": {}}
        })
        assert resp["result"]["isError"] is True
        assert "boom" in resp["result"]["content"][0]["text"]


class TestProtocolErrors:
    @pytest.mark.asyncio
    async def test_unknown_method(self):
        handler = _make_handler()
        resp = await handler.dispatch({"jsonrpc": "2.0", "id": 7, "method": "unknown/method"})
        assert resp["error"]["code"] == -32601

    @pytest.mark.asyncio
    async def test_missing_method(self):
        handler = _make_handler()
        resp = await handler.dispatch({"jsonrpc": "2.0", "id": 8})
        assert resp["error"]["code"] == -32600

    @pytest.mark.asyncio
    async def test_invalid_jsonrpc_version(self):
        handler = _make_handler()
        resp = await handler.dispatch({"jsonrpc": "1.0", "id": 9, "method": "ping"})
        assert resp["error"]["code"] == -32600
