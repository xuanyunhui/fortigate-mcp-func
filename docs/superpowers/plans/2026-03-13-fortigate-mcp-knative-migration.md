# FortiGate MCP Knative Function Migration — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate all 30 FortiGate MCP tools into a Knative Function with custom MCP protocol implementation (no FastMCP), using TDD.

**Architecture:** Knative Function ASGI handler delegates to MCPHandler which parses JSON-RPC 2.0 and dispatches to ToolRegistry. Tools call FortiGateManager → FortiGateAPI → httpx → FortiGate devices. Device config comes from environment variables.

**Tech Stack:** Python 3.9+, httpx, pytest, pytest-asyncio

**Spec:** `docs/superpowers/specs/2026-03-13-fortigate-mcp-knative-migration-design.md`

**Source project:** `/var/home/core/Downloads/fortigate-mcp-server`

---

## Chunk 1: Project Setup + Config + MCP Protocol

### Task 1: Project scaffolding and pyproject.toml

**Files:**
- Modify: `pyproject.toml`
- Create: `function/mcp/__init__.py`
- Create: `function/config/__init__.py`
- Create: `function/core/__init__.py`
- Create: `function/tools/__init__.py`
- Create: `function/formatting/__init__.py`

- [ ] **Step 1: Update pyproject.toml**

```toml
[project]
name = "fortigate-mcp-func"
description = "FortiGate MCP Knative Function"
version = "0.1.0"
requires-python = ">=3.9"
readme = "README.md"
license = "MIT"
dependencies = [
  "httpx",
  "pytest",
  "pytest-asyncio"
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "strict"
asyncio_default_fixture_loop_scope = "function"
```

- [ ] **Step 2: Create empty __init__.py files for all subpackages**

Create these files with empty content:
- `function/mcp/__init__.py`
- `function/config/__init__.py`
- `function/core/__init__.py`
- `function/tools/__init__.py`
- `function/formatting/__init__.py`

- [ ] **Step 3: Verify directory structure**

Run: `find function/ -type f -name '*.py' | sort`

Expected: all __init__.py files present in function/, function/mcp/, function/config/, function/core/, function/tools/, function/formatting/

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml function/
git commit -m "chore: scaffold project directories and update pyproject.toml"
```

---

### Task 2: Environment variable config loader (TDD)

**Files:**
- Test: `tests/test_env_loader.py`
- Create: `function/config/env_loader.py`

- [ ] **Step 1: Write failing tests for env_loader**

```python
"""Tests for environment variable config loader."""
import os
import pytest
from unittest.mock import patch


class TestLoadDevicesFromEnv:
    """Tests for load_devices_from_env function."""

    def test_single_device_with_token(self):
        """Parse a single device with API token auth."""
        env = {
            "FORTIGATE_DEVICE_FW01_HOST": "192.168.1.1",
            "FORTIGATE_DEVICE_FW01_API_TOKEN": "test-token",
        }
        with patch.dict(os.environ, env, clear=True):
            from function.config.env_loader import load_devices_from_env
            devices = load_devices_from_env()

        assert "fw01" in devices
        assert devices["fw01"]["host"] == "192.168.1.1"
        assert devices["fw01"]["api_token"] == "test-token"
        assert devices["fw01"]["port"] == 443
        assert devices["fw01"]["vdom"] == "root"
        assert devices["fw01"]["verify_ssl"] is False
        assert devices["fw01"]["timeout"] == 30

    def test_single_device_with_username_password(self):
        """Parse a single device with username/password auth."""
        env = {
            "FORTIGATE_DEVICE_FW01_HOST": "10.0.0.1",
            "FORTIGATE_DEVICE_FW01_USERNAME": "admin",
            "FORTIGATE_DEVICE_FW01_PASSWORD": "secret",
        }
        with patch.dict(os.environ, env, clear=True):
            from function.config.env_loader import load_devices_from_env
            devices = load_devices_from_env()

        assert devices["fw01"]["username"] == "admin"
        assert devices["fw01"]["password"] == "secret"
        assert devices["fw01"]["api_token"] is None

    def test_multiple_devices(self):
        """Parse multiple devices from env vars."""
        env = {
            "FORTIGATE_DEVICE_FW01_HOST": "192.168.1.1",
            "FORTIGATE_DEVICE_FW01_API_TOKEN": "token1",
            "FORTIGATE_DEVICE_FW02_HOST": "10.0.0.1",
            "FORTIGATE_DEVICE_FW02_API_TOKEN": "token2",
        }
        with patch.dict(os.environ, env, clear=True):
            from function.config.env_loader import load_devices_from_env
            devices = load_devices_from_env()

        assert len(devices) == 2
        assert "fw01" in devices
        assert "fw02" in devices

    def test_custom_optional_fields(self):
        """Parse optional fields with non-default values."""
        env = {
            "FORTIGATE_DEVICE_FW01_HOST": "192.168.1.1",
            "FORTIGATE_DEVICE_FW01_API_TOKEN": "token",
            "FORTIGATE_DEVICE_FW01_PORT": "8443",
            "FORTIGATE_DEVICE_FW01_VDOM": "custom-vdom",
            "FORTIGATE_DEVICE_FW01_VERIFY_SSL": "true",
            "FORTIGATE_DEVICE_FW01_TIMEOUT": "60",
        }
        with patch.dict(os.environ, env, clear=True):
            from function.config.env_loader import load_devices_from_env
            devices = load_devices_from_env()

        d = devices["fw01"]
        assert d["port"] == 8443
        assert d["vdom"] == "custom-vdom"
        assert d["verify_ssl"] is True
        assert d["timeout"] == 60

    def test_device_id_lowercased(self):
        """Device IDs are lowercased."""
        env = {
            "FORTIGATE_DEVICE_MyFirewall_HOST": "1.2.3.4",
            "FORTIGATE_DEVICE_MyFirewall_API_TOKEN": "tok",
        }
        with patch.dict(os.environ, env, clear=True):
            from function.config.env_loader import load_devices_from_env
            devices = load_devices_from_env()

        assert "myfirewall" in devices

    def test_missing_host_raises(self):
        """Missing HOST raises ValueError."""
        env = {
            "FORTIGATE_DEVICE_FW01_API_TOKEN": "token",
        }
        with patch.dict(os.environ, env, clear=True):
            from function.config.env_loader import load_devices_from_env
            with pytest.raises(ValueError, match="HOST"):
                load_devices_from_env()

    def test_missing_auth_raises(self):
        """Missing both API_TOKEN and USERNAME+PASSWORD raises ValueError."""
        env = {
            "FORTIGATE_DEVICE_FW01_HOST": "1.2.3.4",
        }
        with patch.dict(os.environ, env, clear=True):
            from function.config.env_loader import load_devices_from_env
            with pytest.raises(ValueError, match="auth"):
                load_devices_from_env()

    def test_no_devices_returns_empty(self):
        """No FORTIGATE_DEVICE_ vars returns empty dict."""
        with patch.dict(os.environ, {}, clear=True):
            from function.config.env_loader import load_devices_from_env
            devices = load_devices_from_env()

        assert devices == {}

    def test_unrelated_env_vars_ignored(self):
        """Non-FORTIGATE_DEVICE_ vars are ignored."""
        env = {
            "HOME": "/home/user",
            "PATH": "/usr/bin",
            "FORTIGATE_DEVICE_FW01_HOST": "1.2.3.4",
            "FORTIGATE_DEVICE_FW01_API_TOKEN": "tok",
        }
        with patch.dict(os.environ, env, clear=True):
            from function.config.env_loader import load_devices_from_env
            devices = load_devices_from_env()

        assert len(devices) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_env_loader.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement env_loader.py**

```python
"""Load FortiGate device configuration from environment variables."""
import os
import re
from typing import Dict, Any

_PREFIX = "FORTIGATE_DEVICE_"
_FIELD_RE = re.compile(rf"^{_PREFIX}([^_]+)_(.+)$")

_DEFAULTS: Dict[str, Any] = {
    "port": 443,
    "vdom": "root",
    "verify_ssl": False,
    "timeout": 30,
    "api_token": None,
    "username": None,
    "password": None,
}


def load_devices_from_env() -> Dict[str, Dict[str, Any]]:
    """Parse FORTIGATE_DEVICE_* environment variables into device configs.

    Returns:
        Dict mapping lowercased device IDs to their config dicts.

    Raises:
        ValueError: If a device is missing HOST or authentication credentials.
    """
    raw: Dict[str, Dict[str, str]] = {}

    for key, value in os.environ.items():
        m = _FIELD_RE.match(key)
        if not m:
            continue
        device_id = m.group(1).lower()
        field = m.group(2).upper()
        raw.setdefault(device_id, {})[field] = value

    devices: Dict[str, Dict[str, Any]] = {}
    for device_id, fields in raw.items():
        if "HOST" not in fields:
            raise ValueError(
                f"Device '{device_id}': HOST is required "
                f"(set FORTIGATE_DEVICE_{device_id.upper()}_HOST)"
            )

        has_token = "API_TOKEN" in fields
        has_userpass = "USERNAME" in fields and "PASSWORD" in fields
        if not has_token and not has_userpass:
            raise ValueError(
                f"Device '{device_id}': auth credentials required — "
                "set API_TOKEN or USERNAME+PASSWORD"
            )

        cfg = dict(_DEFAULTS)
        cfg["host"] = fields["HOST"]
        if has_token:
            cfg["api_token"] = fields["API_TOKEN"]
        if "USERNAME" in fields:
            cfg["username"] = fields["USERNAME"]
        if "PASSWORD" in fields:
            cfg["password"] = fields["PASSWORD"]
        if "PORT" in fields:
            cfg["port"] = int(fields["PORT"])
        if "VDOM" in fields:
            cfg["vdom"] = fields["VDOM"]
        if "VERIFY_SSL" in fields:
            cfg["verify_ssl"] = fields["VERIFY_SSL"].lower() in ("true", "1", "yes")
        if "TIMEOUT" in fields:
            cfg["timeout"] = int(fields["TIMEOUT"])

        devices[device_id] = cfg

    return devices
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_env_loader.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_env_loader.py function/config/env_loader.py
git commit -m "feat: add environment variable config loader with TDD"
```

---

### Task 3: MCP protocol helpers (TDD)

**Files:**
- Test: `tests/test_mcp_protocol.py`
- Create: `function/mcp/protocol.py`

- [ ] **Step 1: Write failing tests for protocol.py**

```python
"""Tests for MCP protocol helpers."""
import json
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
        assert resp == {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"key": "value"},
        }

    def test_string_id(self):
        resp = make_response("abc", {})
        assert resp["id"] == "abc"


class TestMakeError:
    def test_method_not_found(self):
        resp = make_error(1, METHOD_NOT_FOUND, "Method not found")
        assert resp == {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32601, "message": "Method not found"},
        }

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_mcp_protocol.py -v`
Expected: FAIL

- [ ] **Step 3: Implement protocol.py**

```python
"""MCP protocol constants and message builders."""
from typing import Any, Dict, Optional, Union

# JSON-RPC 2.0 error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# MCP protocol version
PROTOCOL_VERSION = "2025-03-26"

SERVER_INFO = {
    "name": "fortigate-mcp-func",
    "version": "0.1.0",
}


def make_response(
    req_id: Union[str, int, None], result: Any
) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def make_error(
    req_id: Union[str, int, None], code: int, message: str
) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": code, "message": message},
    }


def make_initialize_result() -> Dict[str, Any]:
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": SERVER_INFO,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_mcp_protocol.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_mcp_protocol.py function/mcp/protocol.py
git commit -m "feat: add MCP protocol constants and message builders"
```

---

### Task 4: MCP Handler (TDD)

**Files:**
- Test: `tests/test_mcp_handler.py`
- Create: `function/mcp/handler.py`

- [ ] **Step 1: Write failing tests for MCPHandler**

```python
"""Tests for MCP JSON-RPC handler."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from function.mcp.handler import MCPHandler


def _make_handler(tools=None):
    """Create MCPHandler with optional mock tool registry."""
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
        tools = [
            {"name": "test_tool", "description": "A test", "inputSchema": {"type": "object", "properties": {}}}
        ]
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_mcp_handler.py -v`
Expected: FAIL

- [ ] **Step 3: Implement handler.py**

```python
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
    """Dispatches JSON-RPC requests to the appropriate MCP method."""

    def __init__(self, tool_registry):
        self._registry = tool_registry

    async def dispatch(self, msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single JSON-RPC message and return a response (or None for notifications)."""
        if msg.get("jsonrpc") != "2.0":
            return make_error(msg.get("id"), INVALID_REQUEST, "Invalid JSON-RPC version")

        method = msg.get("method")
        if method is None:
            return make_error(msg.get("id"), INVALID_REQUEST, "Missing method")

        req_id = msg.get("id")  # None for notifications
        params = msg.get("params", {})

        # Notifications (no id) — no response
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

    async def _handle_tools_call(
        self, req_id: Any, params: Dict[str, Any]
    ) -> Dict[str, Any]:
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_mcp_handler.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_mcp_handler.py function/mcp/handler.py
git commit -m "feat: add MCP JSON-RPC handler with full protocol support"
```

---

## Chunk 2: Core Layer (FortiGateAPI + Manager)

### Task 5: FortiGateAPI client (TDD)

**Files:**
- Test: `tests/test_fortigate_api.py`
- Create: `function/core/fortigate_api.py`

Reference source: `/var/home/core/Downloads/fortigate-mcp-server/src/fortigate_mcp/core/fortigate.py` — the `FortiGateAPI` class. Migrate the class with these changes:
- Remove import of `FortiGateDeviceConfig` (Pydantic model) — accept a plain dict instead
- Remove import of `AuthConfig`
- Remove `logging` calls that use `get_logger` / `log_api_call` from source — use standard `logging.getLogger(__name__)`
- Keep `FortiGateAPIError` exception class
- Keep all API endpoint methods exactly as source
- Keep `_make_request` logic exactly as source

- [ ] **Step 1: Write failing tests**

```python
"""Tests for FortiGateAPI client."""
import pytest
import httpx
from unittest.mock import patch, MagicMock
from function.core.fortigate_api import FortiGateAPI, FortiGateAPIError


def _make_config(**overrides):
    cfg = {
        "host": "192.168.1.1",
        "port": 443,
        "api_token": "test-token",
        "username": None,
        "password": None,
        "vdom": "root",
        "verify_ssl": False,
        "timeout": 30,
    }
    cfg.update(overrides)
    return cfg


class TestFortiGateAPIInit:
    def test_token_auth_sets_header(self):
        api = FortiGateAPI("fw01", _make_config())
        assert api.base_url == "https://192.168.1.1:443/api/v2"
        assert "Bearer test-token" in api.headers["Authorization"]

    def test_basic_auth(self):
        api = FortiGateAPI("fw01", _make_config(api_token=None, username="admin", password="pass"))
        assert api.auth_method == "basic"

    def test_no_auth_raises(self):
        with pytest.raises(ValueError, match="api_token or username/password"):
            FortiGateAPI("fw01", _make_config(api_token=None))


class TestMakeRequest:
    @patch("function.core.fortigate_api.httpx.Client")
    def test_get_request(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": []}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.request.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        api = FortiGateAPI("fw01", _make_config())
        result = api._make_request("GET", "cmdb/firewall/policy")
        assert result == {"results": []}
        mock_client.request.assert_called_once()
        call_kwargs = mock_client.request.call_args
        assert call_kwargs.kwargs["method"] == "GET"
        assert "cmdb/firewall/policy" in call_kwargs.kwargs["url"]

    @patch("function.core.fortigate_api.httpx.Client")
    def test_error_response_raises(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.json.return_value = {"error": "not found"}
        mock_resp.text = "not found"
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.request.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        api = FortiGateAPI("fw01", _make_config())
        with pytest.raises(FortiGateAPIError) as exc_info:
            api._make_request("GET", "cmdb/firewall/policy/999")
        assert exc_info.value.status_code == 404

    @patch("function.core.fortigate_api.httpx.Client")
    def test_network_error_raises(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.request.side_effect = httpx.ConnectError("refused")
        mock_client_cls.return_value = mock_client

        api = FortiGateAPI("fw01", _make_config())
        with pytest.raises(FortiGateAPIError, match="Network error"):
            api._make_request("GET", "monitor/system/status")

    @patch("function.core.fortigate_api.httpx.Client")
    def test_vdom_param_passed(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.request.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        api = FortiGateAPI("fw01", _make_config())
        api._make_request("GET", "cmdb/firewall/policy", vdom="custom")
        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["params"]["vdom"] == "custom"


class TestAPIEndpoints:
    @patch("function.core.fortigate_api.httpx.Client")
    def test_get_system_status(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": {"hostname": "fw01"}}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.request.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        api = FortiGateAPI("fw01", _make_config())
        result = api.get_system_status()
        assert result["results"]["hostname"] == "fw01"

    @patch("function.core.fortigate_api.httpx.Client")
    def test_test_connection_success(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": {}}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.request.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        api = FortiGateAPI("fw01", _make_config())
        assert api.test_connection() is True

    @patch("function.core.fortigate_api.httpx.Client")
    def test_test_connection_failure(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.request.side_effect = httpx.ConnectError("refused")
        mock_client_cls.return_value = mock_client

        api = FortiGateAPI("fw01", _make_config())
        assert api.test_connection() is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_fortigate_api.py -v`
Expected: FAIL

- [ ] **Step 3: Implement fortigate_api.py**

Migrate `FortiGateAPIError` and `FortiGateAPI` from source `/var/home/core/Downloads/fortigate-mcp-server/src/fortigate_mcp/core/fortigate.py`. Changes:
- Accept plain dict `config` instead of `FortiGateDeviceConfig` (access with `config["host"]`, `config.get("api_token")`, etc.)
- Use `logging.getLogger(__name__)` instead of source's custom logging
- Remove `log_api_call` calls (just log with standard logger)
- Keep all API endpoint methods exactly as source (get_system_status, get_firewall_policies, create_firewall_policy, etc.)
- Do NOT include `validate_device_host` or SSRF protection (per design decision)

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_fortigate_api.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_fortigate_api.py function/core/fortigate_api.py
git commit -m "feat: add FortiGateAPI client with all endpoint methods"
```

---

### Task 6: FortiGateManager (TDD)

**Files:**
- Test: `tests/test_manager.py`
- Create: `function/core/manager.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for FortiGateManager."""
import pytest
from unittest.mock import patch, MagicMock
from function.core.manager import FortiGateManager


def _make_device_configs():
    return {
        "fw01": {
            "host": "192.168.1.1", "port": 443, "api_token": "tok1",
            "username": None, "password": None,
            "vdom": "root", "verify_ssl": False, "timeout": 30,
        },
        "fw02": {
            "host": "10.0.0.1", "port": 443, "api_token": "tok2",
            "username": None, "password": None,
            "vdom": "root", "verify_ssl": False, "timeout": 30,
        },
    }


class TestFortiGateManager:
    @patch("function.core.manager.FortiGateAPI")
    def test_init_creates_devices(self, mock_api_cls):
        mgr = FortiGateManager(_make_device_configs())
        assert len(mgr.devices) == 2
        assert mock_api_cls.call_count == 2

    @patch("function.core.manager.FortiGateAPI")
    def test_get_device(self, mock_api_cls):
        mgr = FortiGateManager(_make_device_configs())
        device = mgr.get_device("fw01")
        assert device is not None

    @patch("function.core.manager.FortiGateAPI")
    def test_get_device_not_found(self, mock_api_cls):
        mgr = FortiGateManager(_make_device_configs())
        with pytest.raises(ValueError, match="not found"):
            mgr.get_device("nonexistent")

    @patch("function.core.manager.FortiGateAPI")
    def test_list_devices(self, mock_api_cls):
        mgr = FortiGateManager(_make_device_configs())
        devices = mgr.list_devices()
        assert set(devices) == {"fw01", "fw02"}

    @patch("function.core.manager.FortiGateAPI")
    def test_add_device(self, mock_api_cls):
        mgr = FortiGateManager({})
        mgr.add_device("fw03", host="1.2.3.4", api_token="tok")
        assert "fw03" in mgr.devices

    @patch("function.core.manager.FortiGateAPI")
    def test_add_duplicate_raises(self, mock_api_cls):
        mgr = FortiGateManager(_make_device_configs())
        with pytest.raises(ValueError, match="already exists"):
            mgr.add_device("fw01", host="1.2.3.4", api_token="tok")

    @patch("function.core.manager.FortiGateAPI")
    def test_remove_device(self, mock_api_cls):
        mgr = FortiGateManager(_make_device_configs())
        mgr.remove_device("fw01")
        assert "fw01" not in mgr.devices

    @patch("function.core.manager.FortiGateAPI")
    def test_remove_nonexistent_raises(self, mock_api_cls):
        mgr = FortiGateManager({})
        with pytest.raises(ValueError, match="not found"):
            mgr.remove_device("nope")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_manager.py -v`
Expected: FAIL

- [ ] **Step 3: Implement manager.py**

Migrate `FortiGateManager` from source. Changes:
- Accept plain dicts instead of `FortiGateDeviceConfig`/`AuthConfig`
- Remove `auth_config` / `_allowed_host_cidrs` (no SSRF)
- Remove `validate_device_host` call in `add_device`
- Keep `add_device` with keyword args matching env_loader output
- Use standard logging

```python
"""Multi-device FortiGate manager."""
import logging
from typing import Dict, List, Optional

from .fortigate_api import FortiGateAPI

logger = logging.getLogger(__name__)


class FortiGateManager:
    """Manages multiple FortiGate API clients."""

    def __init__(self, device_configs: Dict[str, dict]):
        self.devices: Dict[str, FortiGateAPI] = {}
        for device_id, cfg in device_configs.items():
            try:
                self.devices[device_id] = FortiGateAPI(device_id, cfg)
                logger.info("Initialized device: %s", device_id)
            except Exception as e:
                logger.error("Failed to initialize device %s: %s", device_id, e)

    def get_device(self, device_id: str) -> FortiGateAPI:
        if device_id not in self.devices:
            raise ValueError(f"Device '{device_id}' not found")
        return self.devices[device_id]

    def list_devices(self) -> List[str]:
        return list(self.devices.keys())

    def add_device(self, device_id: str, host: str, port: int = 443,
                   username: Optional[str] = None, password: Optional[str] = None,
                   api_token: Optional[str] = None, vdom: str = "root",
                   verify_ssl: bool = False, timeout: int = 30) -> None:
        if device_id in self.devices:
            raise ValueError(f"Device '{device_id}' already exists")
        cfg = {
            "host": host, "port": port,
            "username": username, "password": password,
            "api_token": api_token, "vdom": vdom,
            "verify_ssl": verify_ssl, "timeout": timeout,
        }
        self.devices[device_id] = FortiGateAPI(device_id, cfg)
        logger.info("Added device: %s", device_id)

    def remove_device(self, device_id: str) -> None:
        if device_id not in self.devices:
            raise ValueError(f"Device '{device_id}' not found")
        del self.devices[device_id]
        logger.info("Removed device: %s", device_id)

    def test_all_connections(self) -> Dict[str, bool]:
        results = {}
        for device_id, api in self.devices.items():
            try:
                results[device_id] = api.test_connection()
            except Exception:
                results[device_id] = False
        return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_manager.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_manager.py function/core/manager.py
git commit -m "feat: add FortiGateManager for multi-device management"
```

---

## Chunk 3: Formatting + ToolRegistry + Device Tools

### Task 7: Formatting module

**Files:**
- Create: `function/formatting/formatters.py`

This is a direct migration of source formatting — templates.py and formatters.py merged into one file. No TDD for this task because it's a straight copy with minor adaptation (replace `mcp.types.TextContent` with plain dicts).

- [ ] **Step 1: Create formatters.py**

Migrate from source files:
- `/var/home/core/Downloads/fortigate-mcp-server/src/fortigate_mcp/formatting/templates.py` (all static methods)
- `/var/home/core/Downloads/fortigate-mcp-server/src/fortigate_mcp/formatting/formatters.py` (all static methods)

Key changes:
- Replace `from mcp.types import TextContent as Content` — use plain dicts `{"type": "text", "text": "..."}` instead of `Content(type="text", text="...")`
- Merge `FortiGateTemplates` methods directly into `FortiGateFormatters` (formatters call templates → inline them)
- Or simpler: keep both classes in one file, keeping the delegation pattern

The implementation should return `List[Dict[str, str]]` (list of `{"type": "text", "text": "..."}`) instead of `List[Content]`.

- [ ] **Step 2: Verify import works**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -c "from function.formatting.formatters import FortiGateFormatters; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add function/formatting/formatters.py
git commit -m "feat: add response formatters (migrated from source)"
```

---

### Task 8: ToolRegistry (TDD)

**Files:**
- Test: `tests/test_tool_registry.py`
- Modify: `function/tools/__init__.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for ToolRegistry."""
import pytest
from unittest.mock import AsyncMock
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_tool_registry.py -v`
Expected: FAIL

- [ ] **Step 3: Implement ToolRegistry in function/tools/__init__.py**

```python
"""Tool registry for MCP tools."""
from typing import Any, Callable, Dict, List, Optional


class ToolRegistry:
    """Registry for MCP tool definitions and their execute functions."""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._handlers: Dict[str, Callable] = {}

    def register(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable,
    ) -> None:
        if name in self._tools:
            raise ValueError(f"Tool '{name}' already registered")
        self._tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
        }
        self._handlers[name] = handler

    def list_all(self) -> List[Dict[str, Any]]:
        return list(self._tools.values())

    def get(self, name: str) -> Optional[Callable]:
        return self._handlers.get(name)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_tool_registry.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_tool_registry.py function/tools/__init__.py
git commit -m "feat: add ToolRegistry for MCP tool management"
```

---

### Task 9: Device tools (TDD)

**Files:**
- Test: `tests/test_tools_device.py`
- Create: `function/tools/device.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for device management tools."""
import pytest
from unittest.mock import MagicMock, patch
from function.tools.device import register_device_tools
from function.tools import ToolRegistry


def _make_mock_manager(device_ids=None):
    mgr = MagicMock()
    mgr.list_devices.return_value = device_ids or ["fw01"]
    mgr.devices = {did: MagicMock() for did in (device_ids or ["fw01"])}
    device = MagicMock()
    device.get_system_status.return_value = {"results": {"hostname": "fw01"}}
    device.test_connection.return_value = True
    device.get_vdoms.return_value = {"results": [{"name": "root"}]}
    mgr.get_device.return_value = device
    return mgr


class TestRegisterDeviceTools:
    def test_registers_all_device_tools(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_device_tools(reg, mgr)
        names = [t["name"] for t in reg.list_all()]
        assert "list_devices" in names
        assert "get_device_status" in names
        assert "test_device_connection" in names
        assert "discover_vdoms" in names
        assert "add_device" in names
        assert "remove_device" in names
        assert "health_check" in names
        assert "get_server_info" in names


class TestListDevices:
    @pytest.mark.asyncio
    async def test_returns_device_list(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager(["fw01", "fw02"])
        register_device_tools(reg, mgr)
        handler = reg.get("list_devices")
        result = await handler({})
        assert len(result) == 1
        assert "fw01" in result[0]["text"]
        assert "fw02" in result[0]["text"]


class TestGetDeviceStatus:
    @pytest.mark.asyncio
    async def test_returns_status(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_device_tools(reg, mgr)
        handler = reg.get("get_device_status")
        result = await handler({"device_id": "fw01"})
        assert len(result) >= 1
        mgr.get_device.assert_called_with("fw01")


class TestTestDeviceConnection:
    @pytest.mark.asyncio
    async def test_successful_connection(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_device_tools(reg, mgr)
        handler = reg.get("test_device_connection")
        result = await handler({"device_id": "fw01"})
        assert any("successful" in r["text"].lower() or "✅" in r["text"] for r in result)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_tools_device.py -v`
Expected: FAIL

- [ ] **Step 3: Implement device.py**

Create `function/tools/device.py` following this pattern — a `register_device_tools(registry, manager)` function that registers all 8 device/system tools. Each tool is an async function that takes `args` dict, calls `manager.get_device()`, invokes the appropriate API method, and returns formatted output via `FortiGateFormatters`.

Migrate the business logic from source `DeviceTools` class methods, plus `health_check` and `get_server_info` from source `server.py`.

Reference source files:
- `/var/home/core/Downloads/fortigate-mcp-server/src/fortigate_mcp/tools/device.py`
- `/var/home/core/Downloads/fortigate-mcp-server/src/fortigate_mcp/tools/definitions.py` (descriptions)
- `/var/home/core/Downloads/fortigate-mcp-server/src/fortigate_mcp/server.py` (health_check, get_server_info tool registration)

Tool input schemas should use JSON Schema format matching the source's parameter definitions.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_tools_device.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_tools_device.py function/tools/device.py
git commit -m "feat: add device management and system tools (8 tools)"
```

---

## Chunk 4: Remaining Tools (Firewall, Network, Routing, VIP)

### Task 10: Firewall tools (TDD)

**Files:**
- Test: `tests/test_tools_firewall.py`
- Create: `function/tools/firewall.py`

- [ ] **Step 1: Write failing tests**

Test that `register_firewall_tools(registry, manager)` registers 5 tools: `list_firewall_policies`, `create_firewall_policy`, `update_firewall_policy`, `delete_firewall_policy`, `get_firewall_policy_detail`. Test at least one tool's behavior (e.g., list_firewall_policies calls the correct API method and returns formatted output).

Reference source: `/var/home/core/Downloads/fortigate-mcp-server/src/fortigate_mcp/tools/firewall.py`

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_tools_firewall.py -v`

- [ ] **Step 3: Implement firewall.py**

Migrate from source `FirewallTools` class. Same pattern as device.py: `register_firewall_tools(registry, manager)` function registering 5 async tool handlers. Use descriptions from source `definitions.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_tools_firewall.py -v`

- [ ] **Step 5: Commit**

```bash
git add tests/test_tools_firewall.py function/tools/firewall.py
git commit -m "feat: add firewall policy tools (5 tools)"
```

---

### Task 11: Network tools (TDD)

**Files:**
- Test: `tests/test_tools_network.py`
- Create: `function/tools/network.py`

- [ ] **Step 1: Write failing tests**

Test that `register_network_tools(registry, manager)` registers 4 tools: `list_address_objects`, `create_address_object`, `list_service_objects`, `create_service_object`.

Reference source: `/var/home/core/Downloads/fortigate-mcp-server/src/fortigate_mcp/tools/network.py`

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_tools_network.py -v`

- [ ] **Step 3: Implement network.py**

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_tools_network.py -v`

- [ ] **Step 5: Commit**

```bash
git add tests/test_tools_network.py function/tools/network.py
git commit -m "feat: add network object tools (4 tools)"
```

---

### Task 12: Routing tools (TDD)

**Files:**
- Test: `tests/test_tools_routing.py`
- Create: `function/tools/routing.py`

- [ ] **Step 1: Write failing tests**

Test that `register_routing_tools(registry, manager)` registers 8 tools: `list_static_routes`, `create_static_route`, `update_static_route`, `delete_static_route`, `get_static_route_detail`, `get_routing_table`, `list_interfaces`, `get_interface_status`.

Reference source: `/var/home/core/Downloads/fortigate-mcp-server/src/fortigate_mcp/tools/routing.py`

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_tools_routing.py -v`

- [ ] **Step 3: Implement routing.py**

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_tools_routing.py -v`

- [ ] **Step 5: Commit**

```bash
git add tests/test_tools_routing.py function/tools/routing.py
git commit -m "feat: add routing tools (8 tools)"
```

---

### Task 13: Virtual IP tools (TDD)

**Files:**
- Test: `tests/test_tools_virtual_ip.py`
- Create: `function/tools/virtual_ip.py`

- [ ] **Step 1: Write failing tests**

Test that `register_virtual_ip_tools(registry, manager)` registers 5 tools: `list_virtual_ips`, `create_virtual_ip`, `update_virtual_ip`, `get_virtual_ip_detail`, `delete_virtual_ip`.

Reference source: `/var/home/core/Downloads/fortigate-mcp-server/src/fortigate_mcp/tools/virtual_ip.py`

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_tools_virtual_ip.py -v`

- [ ] **Step 3: Implement virtual_ip.py**

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_tools_virtual_ip.py -v`

- [ ] **Step 5: Commit**

```bash
git add tests/test_tools_virtual_ip.py function/tools/virtual_ip.py
git commit -m "feat: add virtual IP tools (5 tools)"
```

---

## Chunk 5: ASGI Integration (func.py) + End-to-End Test

### Task 14: Knative Function ASGI entry point (TDD)

**Files:**
- Test: `tests/test_func.py` (replace existing)
- Modify: `function/func.py`
- Modify: `function/__init__.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for Knative Function ASGI entry point."""
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from function import new


class TestFunctionLifecycle:
    @patch("function.func.load_devices_from_env")
    @patch("function.func.FortiGateManager")
    def test_start_initializes_from_env(self, mock_mgr_cls, mock_loader):
        mock_loader.return_value = {"fw01": {"host": "1.2.3.4", "api_token": "tok", "port": 443, "vdom": "root", "verify_ssl": False, "timeout": 30, "username": None, "password": None}}
        f = new()
        f.start({})
        mock_loader.assert_called_once()
        mock_mgr_cls.assert_called_once()

    def test_alive(self):
        f = new()
        alive, msg = f.alive()
        assert alive is True

    def test_ready_before_start(self):
        f = new()
        ready, msg = f.ready()
        assert ready is False

    @patch("function.func.load_devices_from_env")
    @patch("function.func.FortiGateManager")
    def test_ready_after_start(self, mock_mgr_cls, mock_loader):
        mock_loader.return_value = {}
        f = new()
        f.start({})
        ready, msg = f.ready()
        assert ready is True


class TestFunctionHandle:
    @patch("function.func.load_devices_from_env")
    @patch("function.func.FortiGateManager")
    @pytest.mark.asyncio
    async def test_post_json_rpc_ping(self, mock_mgr_cls, mock_loader):
        mock_loader.return_value = {}
        f = new()
        f.start({})

        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"}).encode()
        scope = {"type": "http", "method": "POST", "path": "/"}
        received = False

        async def receive():
            nonlocal received
            if not received:
                received = True
                return {"type": "http.request", "body": body}
            return {"type": "http.disconnect"}

        responses = []
        async def send(msg):
            responses.append(msg)

        await f.handle(scope, receive, send)

        assert len(responses) == 2
        assert responses[0]["status"] == 200
        resp_body = json.loads(responses[1]["body"])
        assert resp_body["result"] == {}

    @patch("function.func.load_devices_from_env")
    @patch("function.func.FortiGateManager")
    @pytest.mark.asyncio
    async def test_get_returns_405(self, mock_mgr_cls, mock_loader):
        mock_loader.return_value = {}
        f = new()
        f.start({})

        scope = {"type": "http", "method": "GET", "path": "/"}
        async def receive(): return {"type": "http.disconnect"}
        responses = []
        async def send(msg): responses.append(msg)

        await f.handle(scope, receive, send)
        assert responses[0]["status"] == 405

    @patch("function.func.load_devices_from_env")
    @patch("function.func.FortiGateManager")
    @pytest.mark.asyncio
    async def test_delete_returns_202(self, mock_mgr_cls, mock_loader):
        mock_loader.return_value = {}
        f = new()
        f.start({})

        scope = {"type": "http", "method": "DELETE", "path": "/"}
        async def receive(): return {"type": "http.disconnect"}
        responses = []
        async def send(msg): responses.append(msg)

        await f.handle(scope, receive, send)
        assert responses[0]["status"] == 202

    @patch("function.func.load_devices_from_env")
    @patch("function.func.FortiGateManager")
    @pytest.mark.asyncio
    async def test_notification_returns_202(self, mock_mgr_cls, mock_loader):
        mock_loader.return_value = {}
        f = new()
        f.start({})

        body = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}).encode()
        scope = {"type": "http", "method": "POST", "path": "/"}
        received = False
        async def receive():
            nonlocal received
            if not received:
                received = True
                return {"type": "http.request", "body": body}
            return {"type": "http.disconnect"}

        responses = []
        async def send(msg): responses.append(msg)

        await f.handle(scope, receive, send)
        assert responses[0]["status"] == 202

    @patch("function.func.load_devices_from_env")
    @patch("function.func.FortiGateManager")
    @pytest.mark.asyncio
    async def test_invalid_json_returns_parse_error(self, mock_mgr_cls, mock_loader):
        mock_loader.return_value = {}
        f = new()
        f.start({})

        body = b"not json"
        scope = {"type": "http", "method": "POST", "path": "/"}
        received = False
        async def receive():
            nonlocal received
            if not received:
                received = True
                return {"type": "http.request", "body": body}
            return {"type": "http.disconnect"}

        responses = []
        async def send(msg): responses.append(msg)

        await f.handle(scope, receive, send)
        resp_body = json.loads(responses[1]["body"])
        assert resp_body["error"]["code"] == -32700
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_func.py -v`
Expected: FAIL

- [ ] **Step 3: Implement func.py**

```python
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
        method = scope.get("method", "GET")

        if method == "GET":
            await self._send(send, 405, b"Method Not Allowed")
            return

        if method == "DELETE":
            await self._send(send, 202, b"")
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
            await self._send(send, 202, b"")
        else:
            await self._send_json(send, 200, response)

    def start(self, cfg):
        device_configs = load_devices_from_env()
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
    async def _send(send, status, body):
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [[b"content-type", b"application/json"]],
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/test_func.py -v`
Expected: all PASS

- [ ] **Step 5: Run ALL tests**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/ -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add function/func.py function/__init__.py tests/test_func.py
git commit -m "feat: implement Knative Function ASGI entry with MCP handler"
```

---

### Task 15: Update CLAUDE.md and final verification

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update CLAUDE.md to reflect new architecture**

Add the new module structure and updated project description.

- [ ] **Step 2: Run full test suite**

Run: `cd /var/home/core/Downloads/fortigate-mcp-func && python -m pytest tests/ -v --tb=short`
Expected: all tests pass

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with migrated architecture"
```
