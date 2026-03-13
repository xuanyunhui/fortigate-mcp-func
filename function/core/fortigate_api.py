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

    def _make_request(
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
            "verify": self.verify_ssl,
            "timeout": self.timeout,
        }
        if data is not None:
            kwargs["json"] = data
        if self._basic_auth:
            kwargs["auth"] = self._basic_auth

        try:
            with httpx.Client() as client:
                response = client.request(method, **kwargs)
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

    def get_system_status(self) -> Any:
        return self._make_request("GET", "monitor/system/status")

    def test_connection(self) -> bool:
        try:
            self._make_request("GET", "monitor/system/status")
            return True
        except FortiGateAPIError:
            return False

    def get_firewall_policies(self, vdom: Optional[str] = None) -> Any:
        return self._make_request("GET", "cmdb/firewall/policy", vdom=vdom)
