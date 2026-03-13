"""Tests for FortiGateAPI client."""
import pytest
import httpx
from unittest.mock import patch, MagicMock, AsyncMock
from function.core.fortigate_api import FortiGateAPI, FortiGateAPIError


def _make_config(**overrides):
    cfg = {
        "host": "192.168.1.1", "port": 443, "api_token": "test-token",
        "username": None, "password": None,
        "vdom": "root", "verify_ssl": False, "timeout": 30,
    }
    cfg.update(overrides)
    return cfg


def _mock_client(mock_cls, status=200, json_data=None):
    mock_resp = MagicMock()
    mock_resp.status_code = status
    mock_resp.json.return_value = json_data or {}
    mock_resp.text = ""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.request = AsyncMock(return_value=mock_resp)
    mock_cls.return_value = mock_client
    return mock_client


class TestInit:
    def test_token_auth(self):
        api = FortiGateAPI("fw01", _make_config())
        assert api.base_url == "https://192.168.1.1:443/api/v2"
        assert "Bearer test-token" in api.headers["Authorization"]
        assert api.auth_method == "token"

    def test_basic_auth(self):
        api = FortiGateAPI("fw01", _make_config(api_token=None, username="admin", password="pass"))
        assert api.auth_method == "basic"

    def test_no_auth_raises(self):
        with pytest.raises(ValueError):
            FortiGateAPI("fw01", _make_config(api_token=None))


class TestMakeRequest:
    @pytest.mark.asyncio
    @patch("function.core.fortigate_api.httpx.AsyncClient")
    async def test_get_request(self, mock_cls):
        client = _mock_client(mock_cls, json_data={"results": []})
        api = FortiGateAPI("fw01", _make_config())
        result = await api._make_request("GET", "cmdb/firewall/policy")
        assert result == {"results": []}

    @pytest.mark.asyncio
    @patch("function.core.fortigate_api.httpx.AsyncClient")
    async def test_error_response_raises(self, mock_cls):
        _mock_client(mock_cls, status=404, json_data={"error": "not found"})
        api = FortiGateAPI("fw01", _make_config())
        with pytest.raises(FortiGateAPIError) as exc:
            await api._make_request("GET", "cmdb/firewall/policy/999")
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    @patch("function.core.fortigate_api.httpx.AsyncClient")
    async def test_network_error(self, mock_cls):
        client = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        client.request = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_cls.return_value = client
        api = FortiGateAPI("fw01", _make_config())
        with pytest.raises(FortiGateAPIError, match="Network error"):
            await api._make_request("GET", "monitor/system/status")

    @pytest.mark.asyncio
    @patch("function.core.fortigate_api.httpx.AsyncClient")
    async def test_vdom_param(self, mock_cls):
        client = _mock_client(mock_cls)
        api = FortiGateAPI("fw01", _make_config())
        await api._make_request("GET", "cmdb/firewall/policy", vdom="custom")
        assert client.request.call_args.kwargs["params"]["vdom"] == "custom"

    @pytest.mark.asyncio
    @patch("function.core.fortigate_api.httpx.AsyncClient")
    async def test_post_with_data(self, mock_cls):
        client = _mock_client(mock_cls)
        api = FortiGateAPI("fw01", _make_config())
        await api._make_request("POST", "cmdb/firewall/policy", data={"name": "test"})
        assert client.request.call_args.kwargs["json"] == {"name": "test"}


class TestEndpoints:
    @pytest.mark.asyncio
    @patch("function.core.fortigate_api.httpx.AsyncClient")
    async def test_get_system_status(self, mock_cls):
        _mock_client(mock_cls, json_data={"results": {"hostname": "fw01"}})
        api = FortiGateAPI("fw01", _make_config())
        result = await api.get_system_status()
        assert result["results"]["hostname"] == "fw01"

    @pytest.mark.asyncio
    @patch("function.core.fortigate_api.httpx.AsyncClient")
    async def test_test_connection_success(self, mock_cls):
        _mock_client(mock_cls, json_data={"results": {}})
        api = FortiGateAPI("fw01", _make_config())
        assert await api.test_connection() is True

    @pytest.mark.asyncio
    @patch("function.core.fortigate_api.httpx.AsyncClient")
    async def test_test_connection_failure(self, mock_cls):
        client = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        client.request = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_cls.return_value = client
        api = FortiGateAPI("fw01", _make_config())
        assert await api.test_connection() is False

    @pytest.mark.asyncio
    @patch("function.core.fortigate_api.httpx.AsyncClient")
    async def test_get_firewall_policies(self, mock_cls):
        _mock_client(mock_cls, json_data={"results": [{"policyid": 1}]})
        api = FortiGateAPI("fw01", _make_config())
        result = await api.get_firewall_policies()
        assert result["results"][0]["policyid"] == 1
