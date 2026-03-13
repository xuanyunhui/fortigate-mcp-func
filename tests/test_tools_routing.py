"""Tests for routing tools."""
import pytest
from unittest.mock import MagicMock
from function.tools.routing import register_routing_tools
from function.tools import ToolRegistry


def _make_mock_manager():
    mgr = MagicMock()
    mgr.devices = {"fw01": MagicMock()}
    device = MagicMock()
    device.get_static_routes.return_value = {"results": [{"seq-num": 1, "dst": "0.0.0.0/0", "gateway": "10.0.0.1", "device": "port1", "status": "enable"}]}
    device.create_static_route.return_value = {"status": "success"}
    device.update_static_route.return_value = {"status": "success"}
    device.delete_static_route.return_value = {"status": "success"}
    device.get_static_route_detail.return_value = {"results": [{"seq-num": 1, "dst": "0.0.0.0/0"}]}
    device.get_routing_table.return_value = {"results": [{"dst": "10.0.0.0/8", "gateway": "10.0.0.1", "interface": "port1"}]}
    device.get_interfaces.return_value = {"results": [{"name": "port1", "status": "up", "type": "physical", "mode": "static", "ip": "10.0.0.2"}]}
    device.get_interface_status.return_value = {"results": [{"name": "port1"}]}
    mgr.get_device.return_value = device
    return mgr


class TestRegister:
    def test_registers_all(self):
        reg = ToolRegistry()
        register_routing_tools(reg, _make_mock_manager())
        names = [t["name"] for t in reg.list_all()]
        expected = ["list_static_routes", "create_static_route", "update_static_route",
                    "delete_static_route", "get_static_route_detail", "get_routing_table",
                    "list_interfaces", "get_interface_status"]
        for n in expected:
            assert n in names
        assert len(names) == 8


class TestListStaticRoutes:
    @pytest.mark.asyncio
    async def test_calls_api(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_routing_tools(reg, mgr)
        result = await reg.get("list_static_routes")({"device_id": "fw01"})
        assert len(result) >= 1


class TestCreateStaticRoute:
    @pytest.mark.asyncio
    async def test_creates(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_routing_tools(reg, mgr)
        result = await reg.get("create_static_route")({"device_id": "fw01", "dst": "10.0.0.0/8", "gateway": "192.168.1.1"})
        mgr.get_device.return_value.create_static_route.assert_called_once()


class TestGetRoutingTable:
    @pytest.mark.asyncio
    async def test_returns_table(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_routing_tools(reg, mgr)
        result = await reg.get("get_routing_table")({"device_id": "fw01"})
        assert len(result) >= 1


class TestListInterfaces:
    @pytest.mark.asyncio
    async def test_lists(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_routing_tools(reg, mgr)
        result = await reg.get("list_interfaces")({"device_id": "fw01"})
        assert len(result) >= 1


class TestGetInterfaceStatus:
    @pytest.mark.asyncio
    async def test_gets_status(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_routing_tools(reg, mgr)
        result = await reg.get("get_interface_status")({"device_id": "fw01", "interface_name": "port1"})
        mgr.get_device.return_value.get_interface_status.assert_called_with("port1", vdom=None)
