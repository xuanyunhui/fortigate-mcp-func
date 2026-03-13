"""Routing management tools for FortiGate MCP Function."""
from typing import Any, Dict, List

from function.formatting.formatters import FortiGateFormatters


LIST_STATIC_ROUTES_DESC = """List static routes configured on a FortiGate device.

This tool retrieves all static routes from the specified device and Virtual Domain,
displaying routing entries with destination, gateway, and interface information.

Parameters:
- device_id: Identifier of the FortiGate device
- vdom: Virtual Domain name (optional, uses device default)

Returns:
- Route sequence number and status
- Destination network
- Gateway address
- Outgoing interface
- Distance and priority
"""

CREATE_STATIC_ROUTE_DESC = """Create a new static route on a FortiGate device.

This tool adds a new static route to the device routing table,
defining the path for traffic destined to a specific network.

Parameters:
- device_id: Identifier of the FortiGate device
- dst: Destination network in CIDR notation (e.g. 10.0.0.0/8)
- gateway: Next-hop gateway IP address
- device: Outgoing interface name (optional)
- vdom: Virtual Domain name (optional, uses device default)

Returns:
- Creation status
- Route configuration summary
"""

UPDATE_STATIC_ROUTE_DESC = """Update an existing static route on a FortiGate device.

This tool modifies an existing static route configuration,
allowing changes to gateway, interface, distance, or other settings.

Parameters:
- device_id: Identifier of the FortiGate device
- route_id: Sequence number of the route to update
- route_data: Updated route configuration as JSON object
- vdom: Virtual Domain name (optional, uses device default)

Returns:
- Update status
- Configuration changes applied
"""

DELETE_STATIC_ROUTE_DESC = """Delete a static route from a FortiGate device.

This tool removes an existing static route from the device routing table,
permanently deleting the specified routing entry.

Parameters:
- device_id: Identifier of the FortiGate device
- route_id: Sequence number of the route to delete
- vdom: Virtual Domain name (optional, uses device default)

Returns:
- Deletion status confirmation
"""

GET_STATIC_ROUTE_DETAIL_DESC = """Get detailed information for a specific static route.

This tool retrieves comprehensive configuration details for a specific
static route entry identified by its sequence number.

Parameters:
- device_id: Identifier of the FortiGate device
- route_id: Sequence number of the route to query
- vdom: Virtual Domain name (optional, uses device default)

Returns:
- Complete route configuration
- Status information
"""

GET_ROUTING_TABLE_DESC = """Get the active routing table from a FortiGate device.

This tool retrieves the current routing table showing all active routes,
including static, connected, and dynamic routing protocol entries.

Parameters:
- device_id: Identifier of the FortiGate device
- vdom: Virtual Domain name (optional, uses device default)

Returns:
- Destination networks
- Gateway addresses
- Route types and distances
- Interface assignments
"""

LIST_INTERFACES_DESC = """List network interfaces configured on a FortiGate device.

This tool retrieves all network interfaces from the specified device,
displaying interface configuration and status information.

Parameters:
- device_id: Identifier of the FortiGate device
- vdom: Virtual Domain name (optional, uses device default)

Returns:
- Interface names and types
- IP addresses and modes
- Administrative and operational status
- Alias information
"""

GET_INTERFACE_STATUS_DESC = """Get status and configuration for a specific network interface.

This tool retrieves detailed status information for a specific network interface
on the FortiGate device.

Parameters:
- device_id: Identifier of the FortiGate device
- interface_name: Name of the interface to query
- vdom: Virtual Domain name (optional, uses device default)

Returns:
- Interface operational status
- IP configuration
- Traffic statistics
- Link status details
"""


def register_routing_tools(registry, manager) -> None:
    """Register all routing management tools into the registry.

    Args:
        registry: ToolRegistry instance
        manager: FortiGateManager instance
    """

    async def list_static_routes(args: Dict[str, Any]) -> List[Dict[str, str]]:
        device_id = args["device_id"]
        vdom = args.get("vdom")
        try:
            api = manager.get_device(device_id)
            data = await api.get_static_routes(vdom=vdom)
            return FortiGateFormatters.format_static_routes(data)
        except Exception as e:
            return FortiGateFormatters.format_error_response(
                "list_static_routes", device_id, str(e)
            )

    registry.register(
        name="list_static_routes",
        description=LIST_STATIC_ROUTES_DESC,
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Identifier of the FortiGate device"},
                "vdom": {"type": "string", "description": "Virtual Domain name (optional)"},
            },
            "required": ["device_id"],
        },
        handler=list_static_routes,
    )

    async def create_static_route(args: Dict[str, Any]) -> List[Dict[str, str]]:
        device_id = args["device_id"]
        dst = args["dst"]
        gateway = args["gateway"]
        device = args.get("device")
        vdom = args.get("vdom")
        try:
            api = manager.get_device(device_id)
            route_data: Dict[str, Any] = {"dst": dst, "gateway": gateway}
            if device:
                route_data["device"] = device
            await api.create_static_route(route_data, vdom=vdom)
            return FortiGateFormatters.format_operation_result(
                "create static route", device_id, True,
                f"Static route to {dst} created successfully"
            )
        except Exception as e:
            return FortiGateFormatters.format_error_response(
                "create_static_route", device_id, str(e)
            )

    registry.register(
        name="create_static_route",
        description=CREATE_STATIC_ROUTE_DESC,
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Identifier of the FortiGate device"},
                "dst": {"type": "string", "description": "Destination network in CIDR notation"},
                "gateway": {"type": "string", "description": "Next-hop gateway IP address"},
                "device": {"type": "string", "description": "Outgoing interface name (optional)"},
                "vdom": {"type": "string", "description": "Virtual Domain name (optional)"},
            },
            "required": ["device_id", "dst", "gateway"],
        },
        handler=create_static_route,
    )

    async def update_static_route(args: Dict[str, Any]) -> List[Dict[str, str]]:
        device_id = args["device_id"]
        route_id = args["route_id"]
        route_data = args["route_data"]
        vdom = args.get("vdom")
        try:
            api = manager.get_device(device_id)
            await api.update_static_route(route_id, route_data, vdom=vdom)
            return FortiGateFormatters.format_operation_result(
                "update static route", device_id, True,
                f"Static route {route_id} updated successfully"
            )
        except Exception as e:
            return FortiGateFormatters.format_error_response(
                "update_static_route", device_id, str(e)
            )

    registry.register(
        name="update_static_route",
        description=UPDATE_STATIC_ROUTE_DESC,
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Identifier of the FortiGate device"},
                "route_id": {"type": "string", "description": "Sequence number of the route to update"},
                "route_data": {"type": "object", "description": "Updated route configuration as JSON object"},
                "vdom": {"type": "string", "description": "Virtual Domain name (optional)"},
            },
            "required": ["device_id", "route_id", "route_data"],
        },
        handler=update_static_route,
    )

    async def delete_static_route(args: Dict[str, Any]) -> List[Dict[str, str]]:
        device_id = args["device_id"]
        route_id = args["route_id"]
        vdom = args.get("vdom")
        try:
            api = manager.get_device(device_id)
            await api.delete_static_route(route_id, vdom=vdom)
            return FortiGateFormatters.format_operation_result(
                "delete static route", device_id, True,
                f"Static route {route_id} deleted successfully"
            )
        except Exception as e:
            return FortiGateFormatters.format_error_response(
                "delete_static_route", device_id, str(e)
            )

    registry.register(
        name="delete_static_route",
        description=DELETE_STATIC_ROUTE_DESC,
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Identifier of the FortiGate device"},
                "route_id": {"type": "string", "description": "Sequence number of the route to delete"},
                "vdom": {"type": "string", "description": "Virtual Domain name (optional)"},
            },
            "required": ["device_id", "route_id"],
        },
        handler=delete_static_route,
    )

    async def get_static_route_detail(args: Dict[str, Any]) -> List[Dict[str, str]]:
        device_id = args["device_id"]
        route_id = args["route_id"]
        vdom = args.get("vdom")
        try:
            api = manager.get_device(device_id)
            data = await api.get_static_route_detail(route_id, vdom=vdom)
            return FortiGateFormatters.format_json_response(data, "Static Route Detail")
        except Exception as e:
            return FortiGateFormatters.format_error_response(
                "get_static_route_detail", device_id, str(e)
            )

    registry.register(
        name="get_static_route_detail",
        description=GET_STATIC_ROUTE_DETAIL_DESC,
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Identifier of the FortiGate device"},
                "route_id": {"type": "string", "description": "Sequence number of the route to query"},
                "vdom": {"type": "string", "description": "Virtual Domain name (optional)"},
            },
            "required": ["device_id", "route_id"],
        },
        handler=get_static_route_detail,
    )

    async def get_routing_table(args: Dict[str, Any]) -> List[Dict[str, str]]:
        device_id = args["device_id"]
        vdom = args.get("vdom")
        try:
            api = manager.get_device(device_id)
            data = await api.get_routing_table(vdom=vdom)
            return FortiGateFormatters.format_routing_table(data)
        except Exception as e:
            return FortiGateFormatters.format_error_response(
                "get_routing_table", device_id, str(e)
            )

    registry.register(
        name="get_routing_table",
        description=GET_ROUTING_TABLE_DESC,
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Identifier of the FortiGate device"},
                "vdom": {"type": "string", "description": "Virtual Domain name (optional)"},
            },
            "required": ["device_id"],
        },
        handler=get_routing_table,
    )

    async def list_interfaces(args: Dict[str, Any]) -> List[Dict[str, str]]:
        device_id = args["device_id"]
        vdom = args.get("vdom")
        try:
            api = manager.get_device(device_id)
            data = await api.get_interfaces(vdom=vdom)
            return FortiGateFormatters.format_interfaces(data)
        except Exception as e:
            return FortiGateFormatters.format_error_response(
                "list_interfaces", device_id, str(e)
            )

    registry.register(
        name="list_interfaces",
        description=LIST_INTERFACES_DESC,
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Identifier of the FortiGate device"},
                "vdom": {"type": "string", "description": "Virtual Domain name (optional)"},
            },
            "required": ["device_id"],
        },
        handler=list_interfaces,
    )

    async def get_interface_status(args: Dict[str, Any]) -> List[Dict[str, str]]:
        device_id = args["device_id"]
        interface_name = args["interface_name"]
        vdom = args.get("vdom")
        try:
            api = manager.get_device(device_id)
            data = await api.get_interface_status(interface_name, vdom=vdom)
            return FortiGateFormatters.format_json_response(data, f"Interface Status: {interface_name}")
        except Exception as e:
            return FortiGateFormatters.format_error_response(
                "get_interface_status", device_id, str(e)
            )

    registry.register(
        name="get_interface_status",
        description=GET_INTERFACE_STATUS_DESC,
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Identifier of the FortiGate device"},
                "interface_name": {"type": "string", "description": "Name of the interface to query"},
                "vdom": {"type": "string", "description": "Virtual Domain name (optional)"},
            },
            "required": ["device_id", "interface_name"],
        },
        handler=get_interface_status,
    )
