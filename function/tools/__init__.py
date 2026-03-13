"""Tool registry for MCP tools."""
from typing import Any, Callable, Dict, List, Optional


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._handlers: Dict[str, Callable] = {}

    def register(self, name: str, description: str, input_schema: Dict[str, Any], handler: Callable) -> None:
        if name in self._tools:
            raise ValueError(f"Tool '{name}' already registered")
        self._tools[name] = {"name": name, "description": description, "inputSchema": input_schema}
        self._handlers[name] = handler

    def list_all(self) -> List[Dict[str, Any]]:
        return list(self._tools.values())

    def get(self, name: str) -> Optional[Callable]:
        return self._handlers.get(name)
