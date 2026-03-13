# FortiGate MCP Knative Function Migration Design

## Overview

Migrate the FortiGate MCP Server (`fortigate-mcp-server`) functionality 1:1 into a Knative Function (`fortigate-mcp-func`), implementing the MCP protocol directly without FastMCP dependency. The Knative Function serves as a deployment vehicle for the MCP server on Kubernetes.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| MCP protocol | Retained | 1:1 migration, clients interact via MCP |
| MCP transport | Streamable HTTP | Current MCP spec recommendation for HTTP transport |
| Protocol implementation | Custom (no FastMCP) | Full control, no framework dependency |
| Device config | Environment variables | Cloud-native, Knative-friendly |
| Multi-device | Yes | One Function instance manages N FortiGate devices |
| Security middleware | None | Auth, rate limiting, SSRF handled by Kubernetes infra (Istio/NetworkPolicy) |
| Development approach | TDD | Tests first, then implementation |

## Architecture

```
MCP Client (Claude/Cursor/etc)
        |  HTTP (Streamable HTTP transport)
+---------------------------------------+
| Knative Function (ASGI handler)       |
|  +-- MCPHandler                       |
|       +-- JSON-RPC 2.0 parsing        |
|       +-- initialize / tools/list     |
|       +-- tools/call -> ToolRegistry  |
+---------------------------------------+
        |
+---------------------------------------+
| ToolRegistry                          |
|  +-- DeviceTools (6)                  |
|  +-- FirewallTools (5)                |
|  +-- NetworkTools (4)                 |
|  +-- RoutingTools (8)                 |
|  +-- VirtualIPTools (5)              |
|  +-- SystemTools (2)                 |
|       | calls                         |
| FortiGateManager                      |
|  +-- FortiGateAPI x N                |
+---------------------------------------+
        |  httpx (HTTPS)
+---------------------------------------+
| FortiGate Devices                     |
+---------------------------------------+
```

## MCP Protocol Implementation

### Supported JSON-RPC Methods

- `initialize` — Returns server capabilities (tools support) and server info
- `notifications/initialized` — Client acknowledgment notification; respond with HTTP 202 Accepted, no body
- `ping` — Keep-alive; respond with empty result `{}`
- `tools/list` — Returns all 30 tool schemas (name, description, inputSchema)
- `tools/call` — Executes a tool by name with parameters, returns result

### HTTP Endpoints

- `POST /` — Receives JSON-RPC request, returns JSON-RPC response
- `GET /` — Returns HTTP 405 Method Not Allowed (SSE not needed)
- `DELETE /` — Returns HTTP 202 Accepted with no body (no-op; function is stateless, included for protocol compliance)

### Response Format

```json
// tools/call success (tool execution result)
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {"type": "text", "text": "...formatted result..."}
    ]
  }
}

// tools/call tool execution error (tool ran but failed)
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {"type": "text", "text": "Error: ..."}
    ],
    "isError": true
  }
}

// JSON-RPC protocol error (parse error, method not found, invalid params)
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {"code": -32601, "message": "Method not found"}
}
```

Standard JSON-RPC 2.0 error codes:
- `-32700` — Parse error
- `-32600` — Invalid request
- `-32601` — Method not found
- `-32602` — Invalid params
- `-32603` — Internal error

### Not Implemented

- `resources/*`, `prompts/*` — Source project does not use these
- SSE push — All tools are request-response
- Session management — Knative is stateless; device connections initialized in `start()` and shared for the Function instance lifetime

## Environment Variable Configuration

### Format

```bash
FORTIGATE_DEVICE_{ID}_{FIELD}

# Required per device
FORTIGATE_DEVICE_{ID}_HOST=192.168.1.1
FORTIGATE_DEVICE_{ID}_API_TOKEN=your_token

# Optional per device (with defaults)
FORTIGATE_DEVICE_{ID}_PORT=443
FORTIGATE_DEVICE_{ID}_VDOM=root
FORTIGATE_DEVICE_{ID}_VERIFY_SSL=false
FORTIGATE_DEVICE_{ID}_TIMEOUT=30

# Alternative auth (instead of API_TOKEN)
FORTIGATE_DEVICE_{ID}_USERNAME=admin
FORTIGATE_DEVICE_{ID}_PASSWORD=secret
```

### Parsing Rules

- Scan all env vars with `FORTIGATE_DEVICE_` prefix
- Group by third segment as device ID (e.g., `FW01`)
- Device ID lowercased for internal use (`FW01` -> `fw01`)
- `HOST` + (`API_TOKEN` or `USERNAME`+`PASSWORD`) required; fail at startup if missing

## File Structure

```
fortigate-mcp-func/
├── function/
│   ├── __init__.py              # re-export new()
│   ├── func.py                  # Knative entry, handle() delegates to MCPHandler
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── handler.py           # MCPHandler — JSON-RPC parsing and dispatch
│   │   └── protocol.py          # MCP protocol constants, message builders
│   ├── config/
│   │   ├── __init__.py
│   │   └── env_loader.py        # Parse device config from env vars
│   ├── core/
│   │   ├── __init__.py
│   │   ├── fortigate_api.py     # FortiGateAPI — single device HTTP client
│   │   └── manager.py           # FortiGateManager — multi-device management
│   ├── tools/
│   │   ├── __init__.py          # ToolRegistry + auto-registration
│   │   ├── device.py            # 6 device management tools
│   │   ├── firewall.py          # 5 firewall policy tools
│   │   ├── network.py           # 4 network object tools
│   │   ├── routing.py           # 8 routing tools
│   │   └── virtual_ip.py        # 5 virtual IP tools
│   └── formatting/
│       ├── __init__.py
│       └── formatters.py        # Response formatting (merged from source formatters.py + templates.py)
├── tests/
│   ├── test_func.py             # ASGI entry point tests
│   ├── test_mcp_handler.py      # MCP protocol tests
│   ├── test_env_loader.py       # Env var parsing tests
│   ├── test_fortigate_api.py    # API client tests (mock httpx)
│   ├── test_manager.py          # Multi-device management tests
│   ├── test_tools_device.py     # Device tool tests
│   ├── test_tools_firewall.py   # Firewall tool tests
│   ├── test_tools_network.py    # Network object tool tests
│   ├── test_tools_routing.py    # Routing tool tests
│   └── test_tools_virtual_ip.py # Virtual IP tool tests
├── func.yaml
├── pyproject.toml
└── CLAUDE.md
```

### Module Responsibilities

- **func.py** — Thin ASGI-to-MCPHandler bridge; lifecycle management (`start` initializes devices)
- **mcp/** — Pure MCP protocol layer; no FortiGate business logic
- **core/** — Pure FortiGate API communication; no MCP concepts
- **tools/** — Business logic glue connecting MCP tool definitions to core API calls; includes `health_check` and `get_server_info` system tools in `device.py`
- **formatting/** — Pure data formatting, no side effects; merges source `formatters.py` and `templates.py` into one file

## Data Flow

### Request Processing

```
1. HTTP POST / -> func.py handle(scope, receive, send)
2. Read request body -> JSON parse
3. MCPHandler.dispatch(json_rpc_request)
   +-- method="initialize" -> return capabilities
   +-- method="notifications/initialized" -> HTTP 202, no body
   +-- method="ping" -> return empty result {}
   +-- method="tools/list" -> ToolRegistry.list_all() -> 30 tool schemas
   +-- method="tools/call"
       +-- ToolRegistry.get(tool_name)
       +-- Validate params against inputSchema
       +-- tool.execute(params, manager)
       |   +-- manager.get_device(device_id)
       |   +-- FortiGateAPI.xxx() -> httpx request to FortiGate
       |   +-- Formatters.format_xxx(response)
       +-- Wrap as JSON-RPC response -> send()
   +-- unknown method -> JSON-RPC error -32601
   +-- parse failure -> JSON-RPC error -32700
```

### Function Lifecycle

```
start(cfg) -> EnvLoader parses device config from env vars
           -> FortiGateManager created, registers FortiGateAPI instances
           -> ToolRegistry initialized, registers all 30 tools

handle()   -> Processes MCP requests (concurrent capable)

stop()     -> Closes all httpx.AsyncClient connections
```

### ToolRegistry Design

- Each tool module exports a list of tool definitions: `name`, `description`, `input_schema` (JSON Schema), `execute` async function
- Registry registers all tools at `start()` time
- `tools/call` looks up by name and executes

## Dependencies

### Required (pyproject.toml)

- `httpx` — FortiGate API communication
- `pytest` + `pytest-asyncio` — Testing

### Not Needed (removed from source)

- `fastmcp`, `mcp` — Replaced by custom protocol implementation
- `fastapi`, `uvicorn`, `asgiref` — Knative provides ASGI runtime
- `pydantic` — Env var parsing is simple enough without it

## Testing Strategy (TDD)

All modules: write tests first, then implement.

| Test File | What It Tests | Mocking |
|-----------|---------------|---------|
| `test_env_loader.py` | Env var parsing, defaults, error cases | `os.environ` |
| `test_mcp_handler.py` | JSON-RPC protocol correctness, error codes, all methods | ToolRegistry |
| `test_fortigate_api.py` | API path construction, request params, error handling | `httpx` |
| `test_manager.py` | Multi-device register/get/add/remove | FortiGateAPI |
| `test_tools_device.py` | Device tool params and formatting (incl. health_check, get_server_info) | FortiGateManager |
| `test_tools_firewall.py` | Firewall tool params and formatting | FortiGateManager |
| `test_tools_network.py` | Network tool params and formatting | FortiGateManager |
| `test_tools_routing.py` | Routing tool params and formatting | FortiGateManager |
| `test_tools_virtual_ip.py` | VIP tool params and formatting | FortiGateManager |
| `test_func.py` | End-to-end ASGI test | MCPHandler |

No real FortiGate devices in tests — all httpx calls mocked.

## Tools Inventory (30 total)

### Device Management (6)
1. `list_devices` — List all registered devices
2. `get_device_status` — Get device system status
3. `test_device_connection` — Test device connectivity
4. `discover_vdoms` — Discover VDOMs on device
5. `add_device` — Dynamically add a device
6. `remove_device` — Remove a registered device

### Firewall Policies (5)
1. `list_firewall_policies` — List policies
2. `create_firewall_policy` — Create policy
3. `update_firewall_policy` — Update policy
4. `delete_firewall_policy` — Delete policy
5. `get_firewall_policy_detail` — Get policy detail with object resolution

### Network Objects (4)
1. `list_address_objects` — List address objects
2. `create_address_object` — Create address object
3. `list_service_objects` — List service objects
4. `create_service_object` — Create service object

### Routing (8)
1. `list_static_routes` — List static routes
2. `create_static_route` — Create static route
3. `update_static_route` — Update static route
4. `delete_static_route` — Delete static route
5. `get_static_route_detail` — Get route detail
6. `get_routing_table` — Get active routing table
7. `list_interfaces` — List network interfaces
8. `get_interface_status` — Get specific interface status by name

### Virtual IP (5)
1. `list_virtual_ips` — List VIPs
2. `create_virtual_ip` — Create VIP
3. `update_virtual_ip` — Update VIP
4. `get_virtual_ip_detail` — Get VIP detail
5. `delete_virtual_ip` — Delete VIP

### System (2)
1. `health_check` — Health check returning device connection status
2. `get_server_info` — Get server info and available tools list
