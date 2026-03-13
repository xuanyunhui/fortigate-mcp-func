"""Tests for firewall policy tools."""
import pytest
from unittest.mock import MagicMock
from function.tools.firewall import register_firewall_tools
from function.tools import ToolRegistry


def _make_mock_manager():
    mgr = MagicMock()
    mgr.devices = {"fw01": MagicMock()}
    device = MagicMock()
    device.get_firewall_policies.return_value = {"results": [{"policyid": 1, "name": "test", "status": "enable", "action": "accept", "srcaddr": [], "dstaddr": [], "service": []}]}
    device.create_firewall_policy.return_value = {"status": "success"}
    device.update_firewall_policy.return_value = {"status": "success"}
    device.delete_firewall_policy.return_value = {"status": "success"}
    device.get_firewall_policy_detail.return_value = {"results": [{"policyid": 1, "name": "test", "status": "enable", "action": "accept", "srcintf": [], "dstintf": [], "srcaddr": [], "dstaddr": [], "service": []}]}
    device.get_address_objects.return_value = {"results": []}
    device.get_service_objects.return_value = {"results": []}
    mgr.get_device.return_value = device
    return mgr


class TestRegister:
    def test_registers_all(self):
        reg = ToolRegistry()
        register_firewall_tools(reg, _make_mock_manager())
        names = [t["name"] for t in reg.list_all()]
        expected = ["list_firewall_policies", "create_firewall_policy", "update_firewall_policy", "delete_firewall_policy", "get_firewall_policy_detail"]
        for n in expected:
            assert n in names
        assert len(names) == 5


class TestListPolicies:
    @pytest.mark.asyncio
    async def test_calls_api(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_firewall_tools(reg, mgr)
        result = await reg.get("list_firewall_policies")({"device_id": "fw01"})
        mgr.get_device.assert_called_with("fw01")
        assert len(result) >= 1


class TestCreatePolicy:
    @pytest.mark.asyncio
    async def test_creates(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_firewall_tools(reg, mgr)
        result = await reg.get("create_firewall_policy")({"device_id": "fw01", "policy_data": {"name": "test"}})
        mgr.get_device.return_value.create_firewall_policy.assert_called_once()


class TestDeletePolicy:
    @pytest.mark.asyncio
    async def test_deletes(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_firewall_tools(reg, mgr)
        result = await reg.get("delete_firewall_policy")({"device_id": "fw01", "policy_id": "1"})
        mgr.get_device.return_value.delete_firewall_policy.assert_called_with("1", vdom=None)


class TestGetPolicyDetail:
    @pytest.mark.asyncio
    async def test_gets_detail_with_resolution(self):
        reg = ToolRegistry()
        mgr = _make_mock_manager()
        register_firewall_tools(reg, mgr)
        result = await reg.get("get_firewall_policy_detail")({"device_id": "fw01", "policy_id": "1"})
        assert len(result) >= 1
