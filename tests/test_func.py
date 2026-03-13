"""Tests for Knative Function ASGI entry point."""
import json
import pytest
from unittest.mock import patch
from function import new


class TestFunctionLifecycle:
    @patch("function.func.load_devices_from_env")
    @patch("function.func.FortiGateManager")
    def test_start_initializes_from_env(self, mock_mgr_cls, mock_loader):
        mock_loader.return_value = {"fw01": {"host": "1.2.3.4", "api_token": "tok", "port": 443, "vdom": "root", "verify_ssl": False, "timeout": 30, "username": None, "password": None}}
        f = new()
        f.start({})
        mock_loader.assert_called_once()
        mock_mgr_cls.assert_called_once()

    def test_alive(self):
        f = new()
        alive, msg = f.alive()
        assert alive is True

    def test_ready_before_start(self):
        f = new()
        ready, msg = f.ready()
        assert ready is False

    @patch("function.func.load_devices_from_env")
    @patch("function.func.FortiGateManager")
    def test_ready_after_start(self, mock_mgr_cls, mock_loader):
        mock_loader.return_value = {}
        f = new()
        f.start({})
        ready, msg = f.ready()
        assert ready is True


class TestFunctionHandle:
    @pytest.mark.asyncio
    async def test_handle_before_start_returns_503(self):
        f = new()
        scope = {"type": "http", "method": "POST", "path": "/"}
        async def receive(): return {"type": "http.disconnect"}
        responses = []
        async def send(msg): responses.append(msg)

        await f.handle(scope, receive, send)
        assert responses[0]["status"] == 503

    @patch("function.func.load_devices_from_env")
    @patch("function.func.FortiGateManager")
    @pytest.mark.asyncio
    async def test_post_json_rpc_ping(self, mock_mgr_cls, mock_loader):
        mock_loader.return_value = {}
        f = new()
        f.start({})

        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"}).encode()
        scope = {"type": "http", "method": "POST", "path": "/"}
        received = False

        async def receive():
            nonlocal received
            if not received:
                received = True
                return {"type": "http.request", "body": body}
            return {"type": "http.disconnect"}

        responses = []
        async def send(msg):
            responses.append(msg)

        await f.handle(scope, receive, send)

        assert len(responses) == 2
        assert responses[0]["status"] == 200
        resp_body = json.loads(responses[1]["body"])
        assert resp_body["result"] == {}

    @patch("function.func.load_devices_from_env")
    @patch("function.func.FortiGateManager")
    @pytest.mark.asyncio
    async def test_get_returns_405(self, mock_mgr_cls, mock_loader):
        mock_loader.return_value = {}
        f = new()
        f.start({})

        scope = {"type": "http", "method": "GET", "path": "/"}
        async def receive(): return {"type": "http.disconnect"}
        responses = []
        async def send(msg): responses.append(msg)

        await f.handle(scope, receive, send)
        assert responses[0]["status"] == 405

    @patch("function.func.load_devices_from_env")
    @patch("function.func.FortiGateManager")
    @pytest.mark.asyncio
    async def test_delete_returns_202(self, mock_mgr_cls, mock_loader):
        mock_loader.return_value = {}
        f = new()
        f.start({})

        scope = {"type": "http", "method": "DELETE", "path": "/"}
        async def receive(): return {"type": "http.disconnect"}
        responses = []
        async def send(msg): responses.append(msg)

        await f.handle(scope, receive, send)
        assert responses[0]["status"] == 202

    @patch("function.func.load_devices_from_env")
    @patch("function.func.FortiGateManager")
    @pytest.mark.asyncio
    async def test_notification_returns_202(self, mock_mgr_cls, mock_loader):
        mock_loader.return_value = {}
        f = new()
        f.start({})

        body = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}).encode()
        scope = {"type": "http", "method": "POST", "path": "/"}
        received = False
        async def receive():
            nonlocal received
            if not received:
                received = True
                return {"type": "http.request", "body": body}
            return {"type": "http.disconnect"}

        responses = []
        async def send(msg): responses.append(msg)

        await f.handle(scope, receive, send)
        assert responses[0]["status"] == 202

    @patch("function.func.load_devices_from_env")
    @patch("function.func.FortiGateManager")
    @pytest.mark.asyncio
    async def test_invalid_json_returns_parse_error(self, mock_mgr_cls, mock_loader):
        mock_loader.return_value = {}
        f = new()
        f.start({})

        body = b"not json"
        scope = {"type": "http", "method": "POST", "path": "/"}
        received = False
        async def receive():
            nonlocal received
            if not received:
                received = True
                return {"type": "http.request", "body": body}
            return {"type": "http.disconnect"}

        responses = []
        async def send(msg): responses.append(msg)

        await f.handle(scope, receive, send)
        resp_body = json.loads(responses[1]["body"])
        assert resp_body["error"]["code"] == -32700
