"""Firewall policy tools for FortiGate MCP Function."""
from typing import Any, Dict, List

from function.formatting.formatters import FortiGateFormatters


LIST_FIREWALL_POLICIES_DESC = """List all firewall policies configured on a FortiGate device.

This tool retrieves and displays all firewall security policies from the
specified device and Virtual Domain, showing traffic control rules and settings.

Parameters:
- device_id: Identifier of the FortiGate device
- vdom: Virtual Domain name (optional, uses device default)

Returns:
- Policy ID and name
- Source and destination addresses
- Services and ports
- Action (allow/deny)
- Policy status (enabled/disabled)
"""

CREATE_FIREWALL_POLICY_DESC = """Create a new firewall policy on a FortiGate device.

This tool adds a new security policy to control traffic flow through
the FortiGate device, defining rules for source, destination, and services.

Parameters:
- device_id: Identifier of the FortiGate device
- policy_data: Policy configuration as JSON object
- vdom: Virtual Domain name (optional, uses device default)

Policy data should include:
- name: Policy name
- srcintf: Source interface(s)
- dstintf: Destination interface(s)
- srcaddr: Source address object(s)
- dstaddr: Destination address object(s)
- service: Service object(s)
- action: accept or deny

Returns:
- Creation status
- Policy ID assigned
- Configuration summary
"""

UPDATE_FIREWALL_POLICY_DESC = """Update an existing firewall policy on a FortiGate device.

This tool modifies the configuration of an existing firewall policy,
allowing changes to rules, addresses, services, and other settings.

Parameters:
- device_id: Identifier of the FortiGate device
- policy_id: ID of the policy to update
- policy_data: Updated policy configuration as JSON object
- vdom: Virtual Domain name (optional, uses device default)

Returns:
- Update status
- Configuration changes applied
"""

DELETE_FIREWALL_POLICY_DESC = """Delete a firewall policy from a FortiGate device.

This tool removes an existing firewall policy from the device configuration,
permanently deleting the specified security rule.

Parameters:
- device_id: Identifier of the FortiGate device
- policy_id: ID of the policy to delete
- vdom: Virtual Domain name (optional, uses device default)

Returns:
- Deletion status confirmation
"""

GET_FIREWALL_POLICY_DETAIL_DESC = """Get detailed information for a specific firewall policy.

This tool retrieves comprehensive configuration details for a specific
firewall policy, including resolved address and service objects.

Parameters:
- device_id: Identifier of the FortiGate device
- policy_id: ID of the policy to query
- vdom: Virtual Domain name (optional, uses device default)

Returns:
- Complete policy configuration
- Resolved address and service objects
- Security profile assignments
- Status information
"""


def register_firewall_tools(registry, manager) -> None:
    """Register all firewall policy tools into the registry.

    Args:
        registry: ToolRegistry instance
        manager: FortiGateManager instance
    """

    async def list_firewall_policies(args: Dict[str, Any]) -> List[Dict[str, str]]:
        device_id = args["device_id"]
        vdom = args.get("vdom")
        try:
            api = manager.get_device(device_id)
            data = await api.get_firewall_policies(vdom=vdom)
            return FortiGateFormatters.format_firewall_policies(data)
        except Exception as e:
            return FortiGateFormatters.format_error_response(
                "list_firewall_policies", device_id, str(e)
            )

    registry.register(
        name="list_firewall_policies",
        description=LIST_FIREWALL_POLICIES_DESC,
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Identifier of the FortiGate device"},
                "vdom": {"type": "string", "description": "Virtual Domain name (optional)"},
            },
            "required": ["device_id"],
        },
        handler=list_firewall_policies,
    )

    async def create_firewall_policy(args: Dict[str, Any]) -> List[Dict[str, str]]:
        device_id = args["device_id"]
        policy_data = args["policy_data"]
        vdom = args.get("vdom")
        try:
            api = manager.get_device(device_id)
            await api.create_firewall_policy(policy_data, vdom=vdom)
            return FortiGateFormatters.format_operation_result(
                "create firewall policy", device_id, True, "Policy created successfully"
            )
        except Exception as e:
            return FortiGateFormatters.format_error_response(
                "create_firewall_policy", device_id, str(e)
            )

    registry.register(
        name="create_firewall_policy",
        description=CREATE_FIREWALL_POLICY_DESC,
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Identifier of the FortiGate device"},
                "policy_data": {"type": "object", "description": "Policy configuration as JSON object"},
                "vdom": {"type": "string", "description": "Virtual Domain name (optional)"},
            },
            "required": ["device_id", "policy_data"],
        },
        handler=create_firewall_policy,
    )

    async def update_firewall_policy(args: Dict[str, Any]) -> List[Dict[str, str]]:
        device_id = args["device_id"]
        policy_id = args["policy_id"]
        policy_data = args["policy_data"]
        vdom = args.get("vdom")
        try:
            api = manager.get_device(device_id)
            await api.update_firewall_policy(policy_id, policy_data, vdom=vdom)
            return FortiGateFormatters.format_operation_result(
                "update firewall policy", device_id, True,
                f"Policy {policy_id} updated successfully"
            )
        except Exception as e:
            return FortiGateFormatters.format_error_response(
                "update_firewall_policy", device_id, str(e)
            )

    registry.register(
        name="update_firewall_policy",
        description=UPDATE_FIREWALL_POLICY_DESC,
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Identifier of the FortiGate device"},
                "policy_id": {"type": "string", "description": "ID of the policy to update"},
                "policy_data": {"type": "object", "description": "Updated policy configuration as JSON object"},
                "vdom": {"type": "string", "description": "Virtual Domain name (optional)"},
            },
            "required": ["device_id", "policy_id", "policy_data"],
        },
        handler=update_firewall_policy,
    )

    async def delete_firewall_policy(args: Dict[str, Any]) -> List[Dict[str, str]]:
        device_id = args["device_id"]
        policy_id = args["policy_id"]
        vdom = args.get("vdom")
        try:
            api = manager.get_device(device_id)
            await api.delete_firewall_policy(policy_id, vdom=vdom)
            return FortiGateFormatters.format_operation_result(
                "delete firewall policy", device_id, True,
                f"Policy {policy_id} deleted successfully"
            )
        except Exception as e:
            return FortiGateFormatters.format_error_response(
                "delete_firewall_policy", device_id, str(e)
            )

    registry.register(
        name="delete_firewall_policy",
        description=DELETE_FIREWALL_POLICY_DESC,
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Identifier of the FortiGate device"},
                "policy_id": {"type": "string", "description": "ID of the policy to delete"},
                "vdom": {"type": "string", "description": "Virtual Domain name (optional)"},
            },
            "required": ["device_id", "policy_id"],
        },
        handler=delete_firewall_policy,
    )

    async def get_firewall_policy_detail(args: Dict[str, Any]) -> List[Dict[str, str]]:
        device_id = args["device_id"]
        policy_id = args["policy_id"]
        vdom = args.get("vdom")
        try:
            api = manager.get_device(device_id)
            policy_data = await api.get_firewall_policy_detail(policy_id, vdom=vdom)
            try:
                address_objects = await api.get_address_objects(vdom=vdom)
            except Exception:
                address_objects = None
            try:
                service_objects = await api.get_service_objects(vdom=vdom)
            except Exception:
                service_objects = None
            return FortiGateFormatters.format_firewall_policy_detail(
                policy_data, device_id,
                address_objects=address_objects,
                service_objects=service_objects,
            )
        except Exception as e:
            return FortiGateFormatters.format_error_response(
                "get_firewall_policy_detail", device_id, str(e)
            )

    registry.register(
        name="get_firewall_policy_detail",
        description=GET_FIREWALL_POLICY_DETAIL_DESC,
        input_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Identifier of the FortiGate device"},
                "policy_id": {"type": "string", "description": "ID of the policy to query"},
                "vdom": {"type": "string", "description": "Virtual Domain name (optional)"},
            },
            "required": ["device_id", "policy_id"],
        },
        handler=get_firewall_policy_detail,
    )
