"""Device management and system tools for FortiGate MCP."""
from typing import Any, Dict

from function.formatting.formatters import FortiGateFormatters


def register_device_tools(registry, manager) -> None:
    """Register all device management and system tools with the registry.

    Args:
        registry: ToolRegistry instance to register tools with
        manager: FortiGateManager instance providing device access
    """

    async def list_devices(args: Dict[str, Any]):
        try:
            device_ids = manager.list_devices()
            device_info = {}
            for did in device_ids:
                try:
                    api = manager.get_device(did)
                    device_info[did] = {
                        "host": getattr(api, "base_url", did),
                        "port": 443,
                        "vdom": getattr(api, "vdom", "root"),
                        "auth_method": "api_token",
                        "verify_ssl": getattr(api, "verify_ssl", False),
                    }
                except Exception:
                    device_info[did] = {
                        "host": did,
                        "port": 443,
                        "vdom": "root",
                        "auth_method": "unknown",
                        "verify_ssl": False,
                    }
            return FortiGateFormatters.format_devices(device_info)
        except Exception as e:
            return [{"type": "text", "text": f"Error listing devices: {e}"}]

    registry.register(
        name="list_devices",
        description=(
            "List all registered FortiGate devices with their configuration details. "
            "Displays device ID, host, VDOM, authentication method, and SSL status."
        ),
        input_schema={"type": "object", "properties": {}},
        handler=list_devices,
    )

    async def get_device_status(args: Dict[str, Any]):
        device_id = args.get("device_id", "")
        try:
            api = manager.get_device(device_id)
            status_data = api.get_system_status()
            return FortiGateFormatters.format_device_status(device_id, status_data)
        except Exception as e:
            return FortiGateFormatters.format_error_response("get_device_status", device_id, str(e))

    registry.register(
        name="get_device_status",
        description=(
            "Get detailed system status information for a specific FortiGate device. "
            "Returns model, serial number, software version, hostname, and operational status."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Device identifier"},
            },
            "required": ["device_id"],
        },
        handler=get_device_status,
    )

    async def test_device_connection(args: Dict[str, Any]):
        device_id = args.get("device_id", "")
        try:
            api = manager.get_device(device_id)
            success = api.test_connection()
            return FortiGateFormatters.format_connection_test(device_id, success)
        except Exception as e:
            return FortiGateFormatters.format_connection_test(device_id, False, str(e))

    registry.register(
        name="test_device_connection",
        description=(
            "Test network connectivity to a specific FortiGate device. "
            "Verifies that the MCP server can communicate with the specified device."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Device identifier"},
            },
            "required": ["device_id"],
        },
        handler=test_device_connection,
    )

    async def discover_vdoms(args: Dict[str, Any]):
        device_id = args.get("device_id", "")
        try:
            api = manager.get_device(device_id)
            vdoms_data = api.get_vdoms()
            return FortiGateFormatters.format_vdoms(vdoms_data)
        except Exception as e:
            return FortiGateFormatters.format_error_response("discover_vdoms", device_id, str(e))

    registry.register(
        name="discover_vdoms",
        description=(
            "Discover and list all Virtual Domains (VDOMs) on a FortiGate device. "
            "Returns VDOM names, status, and configuration details."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Device identifier"},
            },
            "required": ["device_id"],
        },
        handler=discover_vdoms,
    )

    async def add_device(args: Dict[str, Any]):
        device_id = args.get("device_id", "")
        try:
            manager.add_device(
                device_id=device_id,
                host=args.get("host", ""),
                port=int(args.get("port", 443)),
                username=args.get("username"),
                password=args.get("password"),
                api_token=args.get("api_token"),
                vdom=args.get("vdom", "root"),
                verify_ssl=bool(args.get("verify_ssl", False)),
                timeout=int(args.get("timeout", 30)),
            )
            return FortiGateFormatters.format_operation_result(
                "add_device", device_id, True,
                details=f"Device '{device_id}' registered at {args.get('host', '')}",
            )
        except Exception as e:
            return FortiGateFormatters.format_operation_result(
                "add_device", device_id, False, error=str(e)
            )

    registry.register(
        name="add_device",
        description=(
            "Add a new FortiGate device to the MCP server. "
            "Registers a device with connection parameters and authentication credentials."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Unique identifier for the new device"},
                "host": {"type": "string", "description": "IP address or hostname of the FortiGate device"},
                "port": {"type": "integer", "description": "HTTPS port (default: 443)"},
                "username": {"type": "string", "description": "Username for authentication"},
                "password": {"type": "string", "description": "Password for authentication"},
                "api_token": {"type": "string", "description": "API token for authentication (preferred)"},
                "vdom": {"type": "string", "description": "Virtual Domain name (default: root)"},
                "verify_ssl": {"type": "boolean", "description": "Whether to verify SSL certificates"},
                "timeout": {"type": "integer", "description": "Connection timeout in seconds (default: 30)"},
            },
            "required": ["device_id", "host"],
        },
        handler=add_device,
    )

    async def remove_device(args: Dict[str, Any]):
        device_id = args.get("device_id", "")
        try:
            manager.remove_device(device_id)
            return FortiGateFormatters.format_operation_result(
                "remove_device", device_id, True,
                details=f"Device '{device_id}' has been removed",
            )
        except Exception as e:
            return FortiGateFormatters.format_operation_result(
                "remove_device", device_id, False, error=str(e)
            )

    registry.register(
        name="remove_device",
        description=(
            "Remove a FortiGate device from the MCP server. "
            "Unregisters the device and removes all associated configuration."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Identifier of the device to remove"},
            },
            "required": ["device_id"],
        },
        handler=remove_device,
    )

    async def health_check(args: Dict[str, Any]):
        try:
            connection_results = manager.test_all_connections()
            device_count = len(manager.list_devices())
            healthy = all(connection_results.values()) if connection_results else True
            overall_status = "healthy" if healthy else "degraded"
            details = {
                "registered_devices": device_count,
                "connection_results": connection_results,
            }
            return FortiGateFormatters.format_health_status(overall_status, details)
        except Exception as e:
            return [{"type": "text", "text": f"Health check error: {e}"}]

    registry.register(
        name="health_check",
        description=(
            "Perform a comprehensive health check of the FortiGate MCP server. "
            "Checks device connectivity, service availability, and reports overall server health."
        ),
        input_schema={"type": "object", "properties": {}},
        handler=health_check,
    )

    async def get_server_info(args: Dict[str, Any]):
        try:
            device_count = len(manager.list_devices())
            tool_count = 8  # device tools registered by this function
            info_text = (
                "FortiGate MCP Function\n"
                "\n"
                "Server Information\n"
                f"  Version: 1.0.0\n"
                f"  Runtime: Knative Function (ASGI)\n"
                f"  Registered Devices: {device_count}\n"
                f"  Available Tools: {tool_count} device/system tools\n"
                "\n"
                "Capabilities\n"
                "  - Device management (list, add, remove)\n"
                "  - Device status and health monitoring\n"
                "  - VDOM discovery\n"
                "  - Connection testing\n"
            )
            return [{"type": "text", "text": info_text}]
        except Exception as e:
            return [{"type": "text", "text": f"Error retrieving server info: {e}"}]

    registry.register(
        name="get_server_info",
        description=(
            "Get detailed information about the FortiGate MCP server. "
            "Returns server version, available tools, capabilities, and runtime statistics."
        ),
        input_schema={"type": "object", "properties": {}},
        handler=get_server_info,
    )
