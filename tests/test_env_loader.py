"""Tests for environment variable config loader."""
import os
import pytest
from unittest.mock import patch


class TestLoadDevicesFromEnv:
    def test_single_device_with_token(self):
        env = {
            "FORTIGATE_DEVICE_FW01_HOST": "192.168.1.1",
            "FORTIGATE_DEVICE_FW01_API_TOKEN": "test-token",
        }
        with patch.dict(os.environ, env, clear=True):
            from function.config.env_loader import load_devices_from_env
            devices = load_devices_from_env()
        assert "fw01" in devices
        assert devices["fw01"]["host"] == "192.168.1.1"
        assert devices["fw01"]["api_token"] == "test-token"
        assert devices["fw01"]["port"] == 443
        assert devices["fw01"]["vdom"] == "root"
        assert devices["fw01"]["verify_ssl"] is False
        assert devices["fw01"]["timeout"] == 30

    def test_single_device_with_username_password(self):
        env = {
            "FORTIGATE_DEVICE_FW01_HOST": "10.0.0.1",
            "FORTIGATE_DEVICE_FW01_USERNAME": "admin",
            "FORTIGATE_DEVICE_FW01_PASSWORD": "secret",
        }
        with patch.dict(os.environ, env, clear=True):
            from function.config.env_loader import load_devices_from_env
            devices = load_devices_from_env()
        assert devices["fw01"]["username"] == "admin"
        assert devices["fw01"]["password"] == "secret"
        assert devices["fw01"]["api_token"] is None

    def test_multiple_devices(self):
        env = {
            "FORTIGATE_DEVICE_FW01_HOST": "192.168.1.1",
            "FORTIGATE_DEVICE_FW01_API_TOKEN": "token1",
            "FORTIGATE_DEVICE_FW02_HOST": "10.0.0.1",
            "FORTIGATE_DEVICE_FW02_API_TOKEN": "token2",
        }
        with patch.dict(os.environ, env, clear=True):
            from function.config.env_loader import load_devices_from_env
            devices = load_devices_from_env()
        assert len(devices) == 2
        assert "fw01" in devices
        assert "fw02" in devices

    def test_custom_optional_fields(self):
        env = {
            "FORTIGATE_DEVICE_FW01_HOST": "192.168.1.1",
            "FORTIGATE_DEVICE_FW01_API_TOKEN": "token",
            "FORTIGATE_DEVICE_FW01_PORT": "8443",
            "FORTIGATE_DEVICE_FW01_VDOM": "custom-vdom",
            "FORTIGATE_DEVICE_FW01_VERIFY_SSL": "true",
            "FORTIGATE_DEVICE_FW01_TIMEOUT": "60",
        }
        with patch.dict(os.environ, env, clear=True):
            from function.config.env_loader import load_devices_from_env
            devices = load_devices_from_env()
        d = devices["fw01"]
        assert d["port"] == 8443
        assert d["vdom"] == "custom-vdom"
        assert d["verify_ssl"] is True
        assert d["timeout"] == 60

    def test_device_id_lowercased(self):
        env = {
            "FORTIGATE_DEVICE_MyFirewall_HOST": "1.2.3.4",
            "FORTIGATE_DEVICE_MyFirewall_API_TOKEN": "tok",
        }
        with patch.dict(os.environ, env, clear=True):
            from function.config.env_loader import load_devices_from_env
            devices = load_devices_from_env()
        assert "myfirewall" in devices

    def test_missing_host_raises(self):
        env = {"FORTIGATE_DEVICE_FW01_API_TOKEN": "token"}
        with patch.dict(os.environ, env, clear=True):
            from function.config.env_loader import load_devices_from_env
            with pytest.raises(ValueError, match="HOST"):
                load_devices_from_env()

    def test_missing_auth_raises(self):
        env = {"FORTIGATE_DEVICE_FW01_HOST": "1.2.3.4"}
        with patch.dict(os.environ, env, clear=True):
            from function.config.env_loader import load_devices_from_env
            with pytest.raises(ValueError, match="auth"):
                load_devices_from_env()

    def test_no_devices_returns_empty(self):
        with patch.dict(os.environ, {}, clear=True):
            from function.config.env_loader import load_devices_from_env
            devices = load_devices_from_env()
        assert devices == {}

    def test_unrelated_env_vars_ignored(self):
        env = {
            "HOME": "/home/user",
            "PATH": "/usr/bin",
            "FORTIGATE_DEVICE_FW01_HOST": "1.2.3.4",
            "FORTIGATE_DEVICE_FW01_API_TOKEN": "tok",
        }
        with patch.dict(os.environ, env, clear=True):
            from function.config.env_loader import load_devices_from_env
            devices = load_devices_from_env()
        assert len(devices) == 1
