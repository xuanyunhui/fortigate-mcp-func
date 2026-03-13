"""Tests for device management tools."""
import pytest
from unittest.mock import MagicMock
from function.tools.device import register_device_tools
from function.tools import ToolRegistry


def _make_mock_manager(device_ids=None):
    mgr = MagicMock()
    ids = device_ids or ["fw01"]
    mgr.list_devices.return_value = ids
    mgr.devices = {did: MagicMock() for did in ids}
    device = MagicMock()
    device.get_system_status.return_value = {"results": {"hostname": "fw01"}}
    device.test_connection.return_value = True
    device.get_vdoms.return_value = {"results": [{"name": "root"}]}
    mgr.get_device.return_value = device
    return mgr


class TestRegisterDeviceTools:
    def test_registers_all_tools(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_device_tools(reg, mgr)
        names = [t["name"] for t in reg.list_all()]
        expected = ["list_devices", "get_device_status", "test_device_connection",
                    "discover_vdoms", "add_device", "remove_device",
                    "health_check", "get_server_info"]
        for name in expected:
            assert name in names, f"Missing tool: {name}"
        assert len(names) == 8


class TestListDevices:
    @pytest.mark.asyncio
    async def test_returns_device_list(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager(["fw01", "fw02"])
        register_device_tools(reg, mgr)
        result = await reg.get("list_devices")({})
        assert len(result) >= 1
        assert "fw01" in result[0]["text"]
        assert "fw02" in result[0]["text"]


class TestGetDeviceStatus:
    @pytest.mark.asyncio
    async def test_calls_api(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_device_tools(reg, mgr)
        result = await reg.get("get_device_status")({"device_id": "fw01"})
        mgr.get_device.assert_called_with("fw01")
        assert len(result) >= 1


class TestTestConnection:
    @pytest.mark.asyncio
    async def test_success(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_device_tools(reg, mgr)
        result = await reg.get("test_device_connection")({"device_id": "fw01"})
        text = result[0]["text"].lower()
        assert "success" in text or "✅" in result[0]["text"]


class TestAddDevice:
    @pytest.mark.asyncio
    async def test_add(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_device_tools(reg, mgr)
        result = await reg.get("add_device")({"device_id": "fw03", "host": "1.2.3.4", "api_token": "tok"})
        mgr.add_device.assert_called_once()
        assert len(result) >= 1


class TestRemoveDevice:
    @pytest.mark.asyncio
    async def test_remove(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_device_tools(reg, mgr)
        result = await reg.get("remove_device")({"device_id": "fw01"})
        mgr.remove_device.assert_called_with("fw01")


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_returns_status(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        mgr.test_all_connections.return_value = {"fw01": True}
        register_device_tools(reg, mgr)
        result = await reg.get("health_check")({})
        assert len(result) >= 1


class TestGetServerInfo:
    @pytest.mark.asyncio
    async def test_returns_info(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_device_tools(reg, mgr)
        result = await reg.get("get_server_info")({})
        assert len(result) >= 1
        assert "fortigate" in result[0]["text"].lower() or "tool" in result[0]["text"].lower()
