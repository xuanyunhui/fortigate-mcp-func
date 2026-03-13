"""Virtual IP management tools for FortiGate MCP Function."""
from typing import Any, Dict, Optional

from function.formatting.formatters import FortiGateFormatters
from function.tools import ToolRegistry


def register_virtual_ip_tools(registry: ToolRegistry, manager) -> None:
    """Register all virtual IP tools with the given registry."""

    async def list_virtual_ips(params: Dict[str, Any]):
        device_id = params["device_id"]
        vdom = params.get("vdom")
        api = manager.get_device(device_id)
        data = api.get_virtual_ips(vdom=vdom)
        return FortiGateFormatters.format_virtual_ips(data)

    registry.register(
        name="list_virtual_ips",
        description="List all virtual IPs configured on a FortiGate device",
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Device identifier"},
                "vdom": {"type": "string", "description": "Virtual domain name"},
            },
            "required": ["device_id"],
        },
        handler=list_virtual_ips,
    )

    async def create_virtual_ip(params: Dict[str, Any]):
        device_id = params["device_id"]
        name = params["name"]
        extip = params["extip"]
        mappedip = params["mappedip"]
        extintf = params["extintf"]
        portforward = params.get("portforward", "disable")
        protocol = params.get("protocol", "tcp")
        extport = params.get("extport")
        mappedport = params.get("mappedport")
        vdom = params.get("vdom")

        if isinstance(mappedip, str):
            mappedip = [{"range": mappedip}]

        vip_data: Dict[str, Any] = {
            "name": name,
            "extip": extip,
            "mappedip": mappedip,
            "extintf": extintf,
            "portforward": portforward,
        }

        if protocol:
            vip_data["protocol"] = protocol
        if extport:
            vip_data["extport"] = extport
        if mappedport:
            vip_data["mappedport"] = mappedport

        api = manager.get_device(device_id)
        api.create_virtual_ip(vip_data, vdom=vdom)
        return FortiGateFormatters.format_operation_result(
            "create virtual IP", device_id, True, f"Virtual IP '{name}' created successfully"
        )

    registry.register(
        name="create_virtual_ip",
        description="Create a new virtual IP (VIP) on a FortiGate device",
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Device identifier"},
                "name": {"type": "string", "description": "VIP name"},
                "extip": {"type": "string", "description": "External IP address"},
                "mappedip": {"type": "string", "description": "Mapped internal IP address"},
                "extintf": {"type": "string", "description": "External interface"},
                "portforward": {"type": "string", "description": "Enable port forwarding (enable/disable)"},
                "protocol": {"type": "string", "description": "Protocol (tcp/udp)"},
                "extport": {"type": "string", "description": "External port range"},
                "mappedport": {"type": "string", "description": "Mapped port range"},
                "vdom": {"type": "string", "description": "Virtual domain name"},
            },
            "required": ["device_id", "name", "extip", "mappedip", "extintf"],
        },
        handler=create_virtual_ip,
    )

    async def update_virtual_ip(params: Dict[str, Any]):
        device_id = params["device_id"]
        name = params["name"]
        vip_data = params["vip_data"]
        vdom = params.get("vdom")

        api = manager.get_device(device_id)
        api.update_virtual_ip(name, vip_data, vdom=vdom)
        return FortiGateFormatters.format_operation_result(
            "update virtual IP", device_id, True, f"Virtual IP '{name}' updated successfully"
        )

    registry.register(
        name="update_virtual_ip",
        description="Update an existing virtual IP on a FortiGate device",
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Device identifier"},
                "name": {"type": "string", "description": "VIP name"},
                "vip_data": {"type": "object", "description": "Fields to update"},
                "vdom": {"type": "string", "description": "Virtual domain name"},
            },
            "required": ["device_id", "name", "vip_data"],
        },
        handler=update_virtual_ip,
    )

    async def get_virtual_ip_detail(params: Dict[str, Any]):
        device_id = params["device_id"]
        name = params["name"]
        vdom = params.get("vdom")

        api = manager.get_device(device_id)
        data = api.get_virtual_ip_detail(name, vdom=vdom)
        return FortiGateFormatters.format_virtual_ip_detail(data)

    registry.register(
        name="get_virtual_ip_detail",
        description="Get detailed information about a specific virtual IP on a FortiGate device",
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Device identifier"},
                "name": {"type": "string", "description": "VIP name"},
                "vdom": {"type": "string", "description": "Virtual domain name"},
            },
            "required": ["device_id", "name"],
        },
        handler=get_virtual_ip_detail,
    )

    async def delete_virtual_ip(params: Dict[str, Any]):
        device_id = params["device_id"]
        name = params["name"]
        vdom = params.get("vdom")

        api = manager.get_device(device_id)
        api.delete_virtual_ip(name, vdom=vdom)
        return FortiGateFormatters.format_operation_result(
            "delete virtual IP", device_id, True, f"Virtual IP '{name}' deleted successfully"
        )

    registry.register(
        name="delete_virtual_ip",
        description="Delete a virtual IP from a FortiGate device",
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Device identifier"},
                "name": {"type": "string", "description": "VIP name"},
                "vdom": {"type": "string", "description": "Virtual domain name"},
            },
            "required": ["device_id", "name"],
        },
        handler=delete_virtual_ip,
    )
