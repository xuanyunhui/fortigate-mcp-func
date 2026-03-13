"""Tests for ToolRegistry."""
import pytest
from function.tools import ToolRegistry


class TestToolRegistry:
    def test_register_and_list(self):
        reg = ToolRegistry()
        async def my_tool(args): pass
        reg.register("my_tool", "Does stuff", {"type": "object", "properties": {}}, my_tool)
        tools = reg.list_all()
        assert len(tools) == 1
        assert tools[0]["name"] == "my_tool"
        assert tools[0]["description"] == "Does stuff"
        assert "inputSchema" in tools[0]

    def test_get_existing(self):
        reg = ToolRegistry()
        async def my_tool(args): pass
        reg.register("my_tool", "Does stuff", {}, my_tool)
        assert reg.get("my_tool") is my_tool

    def test_get_nonexistent_returns_none(self):
        reg = ToolRegistry()
        assert reg.get("nope") is None

    def test_register_duplicate_raises(self):
        reg = ToolRegistry()
        async def t(args): pass
        reg.register("t", "", {}, t)
        with pytest.raises(ValueError, match="already registered"):
            reg.register("t", "", {}, t)
