"""Tests for network object tools."""
import pytest
from unittest.mock import MagicMock
from function.tools.network import register_network_tools
from function.tools import ToolRegistry


def _make_mock_manager():
    mgr = MagicMock()
    mgr.devices = {"fw01": MagicMock()}
    device = MagicMock()
    device.get_address_objects.return_value = {"results": [{"name": "addr1", "type": "ipmask", "subnet": "10.0.0.0/8"}]}
    device.create_address_object.return_value = {"status": "success"}
    device.get_service_objects.return_value = {"results": [{"name": "svc1", "protocol": "TCP", "tcp-portrange": "80"}]}
    device.create_service_object.return_value = {"status": "success"}
    mgr.get_device.return_value = device
    return mgr


class TestRegister:
    def test_registers_all(self):
        reg = ToolRegistry()
        register_network_tools(reg, _make_mock_manager())
        names = [t["name"] for t in reg.list_all()]
        assert set(names) == {"list_address_objects", "create_address_object", "list_service_objects", "create_service_object"}


class TestListAddressObjects:
    @pytest.mark.asyncio
    async def test_calls_api(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_network_tools(reg, mgr)
        result = await reg.get("list_address_objects")({"device_id": "fw01"})
        mgr.get_device.assert_called_with("fw01")
        assert len(result) >= 1


class TestCreateAddressObject:
    @pytest.mark.asyncio
    async def test_creates(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_network_tools(reg, mgr)
        result = await reg.get("create_address_object")({"device_id": "fw01", "name": "test", "address_type": "ipmask", "address": "10.0.0.0/8"})
        mgr.get_device.return_value.create_address_object.assert_called_once()


class TestListServiceObjects:
    @pytest.mark.asyncio
    async def test_calls_api(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_network_tools(reg, mgr)
        result = await reg.get("list_service_objects")({"device_id": "fw01"})
        assert len(result) >= 1


class TestCreateServiceObject:
    @pytest.mark.asyncio
    async def test_creates(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_network_tools(reg, mgr)
        result = await reg.get("create_service_object")({"device_id": "fw01", "name": "svc", "service_type": "TCP", "protocol": "TCP", "port": "443"})
        mgr.get_device.return_value.create_service_object.assert_called_once()
