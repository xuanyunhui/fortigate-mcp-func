"""FortiGate REST API client."""
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class FortiGateAPIError(Exception):
    """Raised when a FortiGate API request fails."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class FortiGateAPI:
    """Thin HTTP client for the FortiGate REST API (v2)."""

    def __init__(self, device_id: str, config: Dict[str, Any]):
        self.device_id = device_id
        host = config["host"]
        port = config.get("port", 443)
        self.base_url = f"https://{host}:{port}/api/v2"
        self.vdom = config.get("vdom", "root")
        self.verify_ssl = config.get("verify_ssl", False)
        self.timeout = config.get("timeout", 30)

        api_token = config.get("api_token")
        username = config.get("username")
        password = config.get("password")

        if api_token:
            self.auth_method = "token"
            self.headers = {"Authorization": f"Bearer {api_token}"}
            self._basic_auth = None
        elif username:
            self.auth_method = "basic"
            self.headers = {}
            self._basic_auth = (username, password or "")
        else:
            raise ValueError(
                f"Device '{device_id}' requires either api_token or username/password"
            )

    async def _make_request(
        self,
        method: str,
        path: str,
        vdom: Optional[str] = None,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> Any:
        url = f"{self.base_url}/{path}"
        request_params = {"vdom": vdom or self.vdom}
        if params:
            request_params.update(params)

        kwargs: Dict[str, Any] = {
            "url": url,
            "headers": self.headers,
            "params": request_params,
        }
        if data is not None:
            kwargs["json"] = data
        if self._basic_auth:
            kwargs["auth"] = self._basic_auth

        try:
            async with httpx.AsyncClient(
                verify=self.verify_ssl,
                timeout=self.timeout,
            ) as client:
                response = await client.request(method, **kwargs)
        except httpx.ConnectError as exc:
            raise FortiGateAPIError(f"Network error: {exc}") from exc
        except httpx.HTTPError as exc:
            raise FortiGateAPIError(f"HTTP error: {exc}") from exc

        if response.status_code >= 400:
            raise FortiGateAPIError(
                f"Request failed with status {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

        return response.json()

    # ------------------------------------------------------------------
    # Convenience endpoints
    # ------------------------------------------------------------------

    async def get_system_status(self) -> Any:
        return await self._make_request("GET", "monitor/system/status")

    async def test_connection(self) -> bool:
        try:
            await self._make_request("GET", "monitor/system/status")
            return True
        except FortiGateAPIError:
            return False

    # ------------------------------------------------------------------
    # System
    # ------------------------------------------------------------------

    async def get_system_interface(self, vdom: Optional[str] = None) -> Any:
        return await self._make_request("GET", "monitor/system/interface", vdom=vdom)

    async def get_vdoms(self) -> Any:
        return await self._make_request("GET", "cmdb/system/vdom")

    async def get_interfaces(self, vdom: Optional[str] = None) -> Any:
        return await self._make_request("GET", "cmdb/system/interface", vdom=vdom)

    async def get_interface_status(
        self, interface_name: str, vdom: Optional[str] = None
    ) -> Any:
        return await self._make_request(
            "GET",
            "monitor/system/interface",
            params={"interface": interface_name},
            vdom=vdom,
        )

    # ------------------------------------------------------------------
    # Firewall policies
    # ------------------------------------------------------------------

    async def get_firewall_policies(self, vdom: Optional[str] = None) -> Any:
        return await self._make_request("GET", "cmdb/firewall/policy", vdom=vdom)

    async def create_firewall_policy(
        self, policy_data: Dict[str, Any], vdom: Optional[str] = None
    ) -> Any:
        return await self._make_request(
            "POST", "cmdb/firewall/policy", data=policy_data, vdom=vdom
        )

    async def update_firewall_policy(
        self,
        policy_id: int,
        policy_data: Dict[str, Any],
        vdom: Optional[str] = None,
    ) -> Any:
        return await self._make_request(
            "PUT", f"cmdb/firewall/policy/{policy_id}", data=policy_data, vdom=vdom
        )

    async def get_firewall_policy_detail(
        self, policy_id: int, vdom: Optional[str] = None
    ) -> Any:
        return await self._make_request(
            "GET", f"cmdb/firewall/policy/{policy_id}", vdom=vdom
        )

    async def delete_firewall_policy(
        self, policy_id: int, vdom: Optional[str] = None
    ) -> Any:
        return await self._make_request(
            "DELETE", f"cmdb/firewall/policy/{policy_id}", vdom=vdom
        )

    # ------------------------------------------------------------------
    # Address objects
    # ------------------------------------------------------------------

    async def get_address_objects(self, vdom: Optional[str] = None) -> Any:
        return await self._make_request("GET", "cmdb/firewall/address", vdom=vdom)

    async def create_address_object(
        self, address_data: Dict[str, Any], vdom: Optional[str] = None
    ) -> Any:
        return await self._make_request(
            "POST", "cmdb/firewall/address", data=address_data, vdom=vdom
        )

    async def update_address_object(
        self,
        address_name: str,
        address_data: Dict[str, Any],
        vdom: Optional[str] = None,
    ) -> Any:
        return await self._make_request(
            "PUT",
            f"cmdb/firewall/address/{address_name}",
            data=address_data,
            vdom=vdom,
        )

    async def delete_address_object(
        self, address_name: str, vdom: Optional[str] = None
    ) -> Any:
        return await self._make_request(
            "DELETE", f"cmdb/firewall/address/{address_name}", vdom=vdom
        )

    # ------------------------------------------------------------------
    # Service objects
    # ------------------------------------------------------------------

    async def get_service_objects(self, vdom: Optional[str] = None) -> Any:
        return await self._make_request("GET", "cmdb/firewall.service/custom", vdom=vdom)

    async def create_service_object(
        self, service_data: Dict[str, Any], vdom: Optional[str] = None
    ) -> Any:
        return await self._make_request(
            "POST", "cmdb/firewall.service/custom", data=service_data, vdom=vdom
        )

    async def update_service_object(
        self,
        service_name: str,
        service_data: Dict[str, Any],
        vdom: Optional[str] = None,
    ) -> Any:
        return await self._make_request(
            "PUT",
            f"cmdb/firewall.service/custom/{service_name}",
            data=service_data,
            vdom=vdom,
        )

    async def delete_service_object(
        self, service_name: str, vdom: Optional[str] = None
    ) -> Any:
        return await self._make_request(
            "DELETE", f"cmdb/firewall.service/custom/{service_name}", vdom=vdom
        )

    # ------------------------------------------------------------------
    # Static routes
    # ------------------------------------------------------------------

    async def get_static_routes(self, vdom: Optional[str] = None) -> Any:
        return await self._make_request("GET", "cmdb/router/static", vdom=vdom)

    async def create_static_route(
        self, route_data: Dict[str, Any], vdom: Optional[str] = None
    ) -> Any:
        return await self._make_request(
            "POST", "cmdb/router/static", data=route_data, vdom=vdom
        )

    async def update_static_route(
        self,
        route_id: int,
        route_data: Dict[str, Any],
        vdom: Optional[str] = None,
    ) -> Any:
        return await self._make_request(
            "PUT", f"cmdb/router/static/{route_id}", data=route_data, vdom=vdom
        )

    async def delete_static_route(
        self, route_id: int, vdom: Optional[str] = None
    ) -> Any:
        return await self._make_request(
            "DELETE", f"cmdb/router/static/{route_id}", vdom=vdom
        )

    async def get_static_route_detail(
        self, route_id: int, vdom: Optional[str] = None
    ) -> Any:
        return await self._make_request(
            "GET", f"cmdb/router/static/{route_id}", vdom=vdom
        )

    async def get_routing_table(self, vdom: Optional[str] = None) -> Any:
        return await self._make_request("GET", "monitor/router/ipv4", vdom=vdom)

    # ------------------------------------------------------------------
    # Virtual IPs
    # ------------------------------------------------------------------

    async def get_virtual_ips(self, vdom: Optional[str] = None) -> Any:
        return await self._make_request("GET", "cmdb/firewall/vip", vdom=vdom)

    async def create_virtual_ip(
        self, vip_data: Dict[str, Any], vdom: Optional[str] = None
    ) -> Any:
        return await self._make_request(
            "POST", "cmdb/firewall/vip", data=vip_data, vdom=vdom
        )

    async def update_virtual_ip(
        self,
        vip_name: str,
        vip_data: Dict[str, Any],
        vdom: Optional[str] = None,
    ) -> Any:
        return await self._make_request(
            "PUT", f"cmdb/firewall/vip/{vip_name}", data=vip_data, vdom=vdom
        )

    async def delete_virtual_ip(
        self, vip_name: str, vdom: Optional[str] = None
    ) -> Any:
        return await self._make_request(
            "DELETE", f"cmdb/firewall/vip/{vip_name}", vdom=vdom
        )

    async def get_virtual_ip_detail(
        self, vip_name: str, vdom: Optional[str] = None
    ) -> Any:
        return await self._make_request(
            "GET", f"cmdb/firewall/vip/{vip_name}", vdom=vdom
        )
