"""Network object management tools for FortiGate MCP Function."""
from typing import Any, Dict, Optional

from function.tools import ToolRegistry
from function.formatting.formatters import FortiGateFormatters


LIST_ADDRESS_OBJECTS_DESC = """List all address objects configured on a FortiGate device.

This tool retrieves all network address objects defined on the device,
including IP addresses, subnets, ranges, and FQDN objects.

Parameters:
- device_id: Identifier of the FortiGate device
- vdom: Virtual Domain name (optional, uses device default)

Returns:
- Object name and type
- IP address or subnet configuration
- Comments and descriptions
"""

CREATE_ADDRESS_OBJECT_DESC = """Create a new address object on a FortiGate device.

This tool adds a new network address object that can be used in
firewall policies and other security rules.

Parameters:
- device_id: Identifier of the FortiGate device
- name: Object name
- address_type: Type: ipmask, iprange, or fqdn
- address: IP/netmask, IP range, or domain name
- vdom: Virtual Domain name (optional, uses device default)

Returns:
- Creation status
- Object configuration summary
"""

LIST_SERVICE_OBJECTS_DESC = """List all service objects configured on a FortiGate device.

This tool retrieves all network service objects defined on the device,
including TCP/UDP port definitions and protocol specifications.

Parameters:
- device_id: Identifier of the FortiGate device
- vdom: Virtual Domain name (optional, uses device default)

Returns:
- Service name and protocol
- Port configurations
- Comments and descriptions
"""

CREATE_SERVICE_OBJECT_DESC = """Create a new service object on a FortiGate device.

This tool adds a new network service object that defines protocols
and ports for use in firewall policies.

Parameters:
- device_id: Identifier of the FortiGate device
- name: Service object name
- service_type: Service type (e.g. TCP, UDP, ICMP)
- protocol: Protocol name
- port: Port number or range (optional)
- vdom: Virtual Domain name (optional, uses device default)

Returns:
- Creation status
- Service configuration summary
"""


def register_network_tools(registry: ToolRegistry, manager: Any) -> None:
    """Register network object tools with the given registry.

    Args:
        registry: ToolRegistry instance to register tools into
        manager: FortiGateManager instance for API access
    """

    async def list_address_objects(params: Dict[str, Any]):
        device_id: str = params["device_id"]
        vdom: Optional[str] = params.get("vdom")
        device = manager.get_device(device_id)
        data = await device.get_address_objects(vdom=vdom)
        return FortiGateFormatters.format_address_objects(data)

    async def create_address_object(params: Dict[str, Any]):
        device_id: str = params["device_id"]
        name: str = params["name"]
        address_type: str = params["address_type"]
        address: str = params["address"]
        vdom: Optional[str] = params.get("vdom")
        device = manager.get_device(device_id)
        address_data = {
            "name": name,
            "type": address_type,
            "subnet": address,
        }
        result = await device.create_address_object(address_data, vdom=vdom)
        return FortiGateFormatters.format_operation_result(
            "create address object", device_id, True,
            f"Address object '{name}' created successfully"
        )

    async def list_service_objects(params: Dict[str, Any]):
        device_id: str = params["device_id"]
        vdom: Optional[str] = params.get("vdom")
        device = manager.get_device(device_id)
        data = await device.get_service_objects(vdom=vdom)
        return FortiGateFormatters.format_service_objects(data)

    async def create_service_object(params: Dict[str, Any]):
        device_id: str = params["device_id"]
        name: str = params["name"]
        service_type: str = params["service_type"]
        protocol: str = params["protocol"]
        port: Optional[str] = params.get("port")
        vdom: Optional[str] = params.get("vdom")
        device = manager.get_device(device_id)
        service_data: Dict[str, Any] = {
            "name": name,
            "type": service_type,
            "protocol": protocol,
        }
        if port:
            service_data["port"] = port
        result = await device.create_service_object(service_data, vdom=vdom)
        return FortiGateFormatters.format_operation_result(
            "create service object", device_id, True,
            f"Service object '{name}' created successfully"
        )

    registry.register(
        name="list_address_objects",
        description=LIST_ADDRESS_OBJECTS_DESC,
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "FortiGate device identifier"},
                "vdom": {"type": "string", "description": "Virtual Domain name (optional)"},
            },
            "required": ["device_id"],
        },
        handler=list_address_objects,
    )

    registry.register(
        name="create_address_object",
        description=CREATE_ADDRESS_OBJECT_DESC,
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "FortiGate device identifier"},
                "name": {"type": "string", "description": "Address object name"},
                "address_type": {"type": "string", "description": "Type: ipmask, iprange, or fqdn"},
                "address": {"type": "string", "description": "IP/netmask, IP range, or domain name"},
                "vdom": {"type": "string", "description": "Virtual Domain name (optional)"},
            },
            "required": ["device_id", "name", "address_type", "address"],
        },
        handler=create_address_object,
    )

    registry.register(
        name="list_service_objects",
        description=LIST_SERVICE_OBJECTS_DESC,
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "FortiGate device identifier"},
                "vdom": {"type": "string", "description": "Virtual Domain name (optional)"},
            },
            "required": ["device_id"],
        },
        handler=list_service_objects,
    )

    registry.register(
        name="create_service_object",
        description=CREATE_SERVICE_OBJECT_DESC,
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "FortiGate device identifier"},
                "name": {"type": "string", "description": "Service object name"},
                "service_type": {"type": "string", "description": "Service type (e.g. TCP, UDP, ICMP)"},
                "protocol": {"type": "string", "description": "Protocol name"},
                "port": {"type": "string", "description": "Port number or range (optional)"},
                "vdom": {"type": "string", "description": "Virtual Domain name (optional)"},
            },
            "required": ["device_id", "name", "service_type", "protocol"],
        },
        handler=create_service_object,
    )
