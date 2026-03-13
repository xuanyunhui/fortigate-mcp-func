"""Multi-device FortiGate manager."""
import logging
from typing import Dict, List, Optional
from .fortigate_api import FortiGateAPI

logger = logging.getLogger(__name__)


class FortiGateManager:
    def __init__(self, device_configs: Dict[str, dict]):
        self.devices: Dict[str, FortiGateAPI] = {}
        for device_id, cfg in device_configs.items():
            try:
                self.devices[device_id] = FortiGateAPI(device_id, cfg)
                logger.info("Initialized device: %s", device_id)
            except Exception as e:
                logger.error("Failed to initialize device %s: %s", device_id, e)

    def get_device(self, device_id: str) -> FortiGateAPI:
        if device_id not in self.devices:
            raise ValueError(f"Device '{device_id}' not found")
        return self.devices[device_id]

    def list_devices(self) -> List[str]:
        return list(self.devices.keys())

    def add_device(self, device_id: str, host: str, port: int = 443,
                   username: Optional[str] = None, password: Optional[str] = None,
                   api_token: Optional[str] = None, vdom: str = "root",
                   verify_ssl: bool = False, timeout: int = 30) -> None:
        if device_id in self.devices:
            raise ValueError(f"Device '{device_id}' already exists")
        cfg = {"host": host, "port": port, "username": username, "password": password,
               "api_token": api_token, "vdom": vdom, "verify_ssl": verify_ssl, "timeout": timeout}
        self.devices[device_id] = FortiGateAPI(device_id, cfg)
        logger.info("Added device: %s", device_id)

    def remove_device(self, device_id: str) -> None:
        if device_id not in self.devices:
            raise ValueError(f"Device '{device_id}' not found")
        del self.devices[device_id]
        logger.info("Removed device: %s", device_id)

    def test_all_connections(self) -> Dict[str, bool]:
        results = {}
        for device_id, api in self.devices.items():
            try:
                results[device_id] = api.test_connection()
            except Exception:
                results[device_id] = False
        return results
