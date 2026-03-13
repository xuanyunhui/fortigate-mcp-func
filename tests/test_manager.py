"""Tests for FortiGateManager."""
import pytest
from unittest.mock import patch, MagicMock
from function.core.manager import FortiGateManager


def _make_configs():
    return {
        "fw01": {"host": "192.168.1.1", "port": 443, "api_token": "tok1",
                 "username": None, "password": None, "vdom": "root", "verify_ssl": False, "timeout": 30},
        "fw02": {"host": "10.0.0.1", "port": 443, "api_token": "tok2",
                 "username": None, "password": None, "vdom": "root", "verify_ssl": False, "timeout": 30},
    }


class TestFortiGateManager:
    @patch("function.core.manager.FortiGateAPI")
    def test_init_creates_devices(self, mock_cls):
        mgr = FortiGateManager(_make_configs())
        assert len(mgr.devices) == 2

    @patch("function.core.manager.FortiGateAPI")
    def test_get_device(self, mock_cls):
        mgr = FortiGateManager(_make_configs())
        assert mgr.get_device("fw01") is not None

    @patch("function.core.manager.FortiGateAPI")
    def test_get_device_not_found(self, mock_cls):
        mgr = FortiGateManager(_make_configs())
        with pytest.raises(ValueError, match="not found"):
            mgr.get_device("nonexistent")

    @patch("function.core.manager.FortiGateAPI")
    def test_list_devices(self, mock_cls):
        mgr = FortiGateManager(_make_configs())
        assert set(mgr.list_devices()) == {"fw01", "fw02"}

    @patch("function.core.manager.FortiGateAPI")
    def test_add_device(self, mock_cls):
        mgr = FortiGateManager({})
        mgr.add_device("fw03", host="1.2.3.4", api_token="tok")
        assert "fw03" in mgr.devices

    @patch("function.core.manager.FortiGateAPI")
    def test_add_duplicate_raises(self, mock_cls):
        mgr = FortiGateManager(_make_configs())
        with pytest.raises(ValueError, match="already exists"):
            mgr.add_device("fw01", host="1.2.3.4", api_token="tok")

    @patch("function.core.manager.FortiGateAPI")
    def test_remove_device(self, mock_cls):
        mgr = FortiGateManager(_make_configs())
        mgr.remove_device("fw01")
        assert "fw01" not in mgr.devices

    @patch("function.core.manager.FortiGateAPI")
    def test_remove_nonexistent_raises(self, mock_cls):
        mgr = FortiGateManager({})
        with pytest.raises(ValueError, match="not found"):
            mgr.remove_device("nope")
