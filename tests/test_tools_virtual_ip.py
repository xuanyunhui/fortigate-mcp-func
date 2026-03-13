"""Tests for virtual IP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from function.tools.virtual_ip import register_virtual_ip_tools
from function.tools import ToolRegistry


def _make_mock_manager():
    mgr = MagicMock()
    mgr.devices = {"fw01": MagicMock()}
    device = MagicMock()
    device.get_virtual_ips = AsyncMock(return_value={"results": [{"name": "vip1", "extip": "1.2.3.4", "mappedip": [{"range": "10.0.0.1"}], "extintf": "port1"}]})
    device.create_virtual_ip = AsyncMock(return_value={"status": "success"})
    device.update_virtual_ip = AsyncMock(return_value={"status": "success"})
    device.delete_virtual_ip = AsyncMock(return_value={"status": "success"})
    device.get_virtual_ip_detail = AsyncMock(return_value={"results": [{"name": "vip1", "extip": "1.2.3.4"}]})
    mgr.get_device.return_value = device
    return mgr


class TestRegister:
    def test_registers_all(self):
        reg = ToolRegistry()
        register_virtual_ip_tools(reg, _make_mock_manager())
        names = [t["name"] for t in reg.list_all()]
        expected = ["list_virtual_ips", "create_virtual_ip", "update_virtual_ip", "get_virtual_ip_detail", "delete_virtual_ip"]
        for n in expected:
            assert n in names
        assert len(names) == 5


class TestListVIPs:
    @pytest.mark.asyncio
    async def test_calls_api(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_virtual_ip_tools(reg, mgr)
        result = await reg.get("list_virtual_ips")({"device_id": "fw01"})
        assert len(result) >= 1


class TestCreateVIP:
    @pytest.mark.asyncio
    async def test_creates(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_virtual_ip_tools(reg, mgr)
        result = await reg.get("create_virtual_ip")({"device_id": "fw01", "name": "vip2", "extip": "1.2.3.4", "mappedip": "10.0.0.2", "extintf": "port1"})
        mgr.get_device.return_value.create_virtual_ip.assert_called_once()


class TestUpdateVIP:
    @pytest.mark.asyncio
    async def test_updates(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_virtual_ip_tools(reg, mgr)
        result = await reg.get("update_virtual_ip")({"device_id": "fw01", "name": "vip1", "vip_data": {"extip": "5.6.7.8"}})
        mgr.get_device.return_value.update_virtual_ip.assert_called_once()


class TestGetVIPDetail:
    @pytest.mark.asyncio
    async def test_gets_detail(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_virtual_ip_tools(reg, mgr)
        result = await reg.get("get_virtual_ip_detail")({"device_id": "fw01", "name": "vip1"})
        assert len(result) >= 1


class TestDeleteVIP:
    @pytest.mark.asyncio
    async def test_deletes(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_virtual_ip_tools(reg, mgr)
        result = await reg.get("delete_virtual_ip")({"device_id": "fw01", "name": "vip1"})
        mgr.get_device.return_value.delete_virtual_ip.assert_called_with("vip1", vdom=None)
