"""Load FortiGate device configuration from environment variables."""
import os
import re
from typing import Dict, Any

_PREFIX = "FORTIGATE_DEVICE_"
_FIELD_RE = re.compile(rf"^{_PREFIX}([^_]+)_(.+)$")

_DEFAULTS: Dict[str, Any] = {
    "port": 443,
    "vdom": "root",
    "verify_ssl": False,
    "timeout": 30,
    "api_token": None,
    "username": None,
    "password": None,
}


def load_devices_from_env() -> Dict[str, Dict[str, Any]]:
    raw: Dict[str, Dict[str, str]] = {}
    for key, value in os.environ.items():
        m = _FIELD_RE.match(key)
        if not m:
            continue
        device_id = m.group(1).lower()
        field = m.group(2).upper()
        raw.setdefault(device_id, {})[field] = value

    devices: Dict[str, Dict[str, Any]] = {}
    for device_id, fields in raw.items():
        if "HOST" not in fields:
            raise ValueError(
                f"Device '{device_id}': HOST is required "
                f"(set FORTIGATE_DEVICE_{device_id.upper()}_HOST)"
            )
        has_token = "API_TOKEN" in fields
        has_userpass = "USERNAME" in fields and "PASSWORD" in fields
        if not has_token and not has_userpass:
            raise ValueError(
                f"Device '{device_id}': auth credentials required — "
                "set API_TOKEN or USERNAME+PASSWORD"
            )
        cfg = dict(_DEFAULTS)
        cfg["host"] = fields["HOST"]
        if has_token:
            cfg["api_token"] = fields["API_TOKEN"]
        if "USERNAME" in fields:
            cfg["username"] = fields["USERNAME"]
        if "PASSWORD" in fields:
            cfg["password"] = fields["PASSWORD"]
        if "PORT" in fields:
            cfg["port"] = int(fields["PORT"])
        if "VDOM" in fields:
            cfg["vdom"] = fields["VDOM"]
        if "VERIFY_SSL" in fields:
            cfg["verify_ssl"] = fields["VERIFY_SSL"].lower() in ("true", "1", "yes")
        if "TIMEOUT" in fields:
            cfg["timeout"] = int(fields["TIMEOUT"])
        devices[device_id] = cfg
    return devices
