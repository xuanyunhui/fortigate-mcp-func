# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FortiGate MCP Function — a Python Knative Function that exposes 30 FortiGate management tools via the MCP (Model Context Protocol) over Streamable HTTP transport. Designed to run on Kubernetes clusters with Knative installed. Built using the Knative `func` CLI tooling (spec version 0.36.0).

## Commands

```bash
# Run locally (outside container)
func run --builder=host

# Deploy to cluster
func deploy --registry ghcr.io/<user>

# Run tests
pytest tests/

# Run a single test
pytest tests/test_func.py::TestFunctionHandle::test_post_json_rpc_ping
```

## Architecture

Knative Function ASGI handler → MCPHandler (JSON-RPC 2.0) → ToolRegistry → FortiGateManager → FortiGateAPI → httpx → FortiGate devices.

### Module Structure

- `function/func.py` — Knative entry point. `new()` factory returns `Function` instance. `start()` loads env config, creates manager, registers all 30 tools, initializes MCPHandler. `handle(scope, receive, send)` routes HTTP: POST → JSON-RPC dispatch, GET → 405, DELETE → 202.
- `function/mcp/handler.py` — MCPHandler: dispatches JSON-RPC methods (initialize, ping, tools/list, tools/call, notifications/*).
- `function/mcp/protocol.py` — JSON-RPC 2.0 constants and message builders.
- `function/config/env_loader.py` — Parses `FORTIGATE_DEVICE_{ID}_{FIELD}` environment variables into device configs.
- `function/core/fortigate_api.py` — FortiGateAPI: single-device HTTP client using httpx.
- `function/core/manager.py` — FortiGateManager: multi-device registry.
- `function/tools/__init__.py` — ToolRegistry: register/lookup tools by name.
- `function/tools/device.py` — 8 tools: list_devices, get_device_status, test_device_connection, discover_vdoms, add_device, remove_device, health_check, get_server_info.
- `function/tools/firewall.py` — 5 tools: list/create/update/delete_firewall_policy, get_firewall_policy_detail.
- `function/tools/network.py` — 4 tools: list/create_address_objects, list/create_service_objects.
- `function/tools/routing.py` — 8 tools: list/create/update/delete_static_route, get_static_route_detail, get_routing_table, list_interfaces, get_interface_status.
- `function/tools/virtual_ip.py` — 5 tools: list/create/update/delete_virtual_ip, get_virtual_ip_detail.
- `function/formatting/formatters.py` — Response formatting (text templates + MCP content wrappers).

### Device Configuration

Devices are configured via environment variables:
```
FORTIGATE_DEVICE_{ID}_HOST=192.168.1.1
FORTIGATE_DEVICE_{ID}_API_TOKEN=your_token
FORTIGATE_DEVICE_{ID}_PORT=443          # optional, default 443
FORTIGATE_DEVICE_{ID}_VDOM=root         # optional, default root
FORTIGATE_DEVICE_{ID}_VERIFY_SSL=false  # optional, default false
FORTIGATE_DEVICE_{ID}_TIMEOUT=30        # optional, default 30
```

## Testing

Tests use `pytest-asyncio` in **strict** mode (`asyncio_mode = "strict"`). Test functions must be decorated with `@pytest.mark.asyncio`. All FortiGate API calls are mocked — no real devices needed. 89 tests across 11 test files.
