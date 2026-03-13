# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FortiGate MCP Function — a Python Knative Function that exposes 30 FortiGate management tools via the MCP (Model Context Protocol) over Streamable HTTP transport. Designed to run on Kubernetes clusters with Knative installed. Built using the Knative `func` CLI tooling (spec version 0.36.0).

## Commands

```bash
# Run locally (outside container)
func run --builder=host

# Deploy to cluster
func deploy --registry ghcr.io/<user>

# Run tests
pytest tests/

# Run a single test
pytest tests/test_func.py::TestFunctionHandle::test_post_json_rpc_ping
```

## Architecture

Knative Function ASGI handler → MCPHandler (JSON-RPC 2.0) → ToolRegistry → FortiGateManager → FortiGateAPI → httpx → FortiGate devices.

### Module Structure

- `function/func.py` — Knative entry point. `new()` factory returns `Function` instance. `start()` loads env config, creates manager, registers all 30 tools, initializes MCPHandler. `handle(scope, receive, send)` routes HTTP: POST → JSON-RPC dispatch, GET → 405, DELETE → 202.
- `function/mcp/handler.py` — MCPHandler: dispatches JSON-RPC methods (initialize, ping, tools/list, tools/call, notifications/*).
- `function/mcp/protocol.py` — JSON-RPC 2.0 constants and message builders.
- `function/config/env_loader.py` — Parses `FORTIGATE_DEVICE_{ID}_{FIELD}` environment variables into device configs.
- `function/core/fortigate_api.py` — FortiGateAPI: single-device HTTP client using httpx.
- `function/core/manager.py` — FortiGateManager: multi-device registry.
- `function/tools/__init__.py` — ToolRegistry: register/lookup tools by name.
- `function/tools/device.py` — 8 tools: list_devices, get_device_status, test_device_connection, discover_vdoms, add_device, remove_device, health_check, get_server_info.
- `function/tools/firewall.py` — 5 tools: list/create/update/delete_firewall_policy, get_firewall_policy_detail.
- `function/tools/network.py` — 4 tools: list/create_address_objects, list/create_service_objects.
- `function/tools/routing.py` — 8 tools: list/create/update/delete_static_route, get_static_route_detail, get_routing_table, list_interfaces, get_interface_status.
- `function/tools/virtual_ip.py` — 5 tools: list/create/update/delete_virtual_ip, get_virtual_ip_detail.
- `function/formatting/formatters.py` — Response formatting (text templates + MCP content wrappers).

### Device Configuration

Devices are configured via environment variables:
```
FORTIGATE_DEVICE_{ID}_HOST=192.168.1.1
FORTIGATE_DEVICE_{ID}_API_TOKEN=your_token
FORTIGATE_DEVICE_{ID}_PORT=443          # optional, default 443
FORTIGATE_DEVICE_{ID}_VDOM=root         # optional, default root
FORTIGATE_DEVICE_{ID}_VERIFY_SSL=false  # optional, default false
FORTIGATE_DEVICE_{ID}_TIMEOUT=30        # optional, default 30
```

## Deployment

### Tekton CD Pipeline

开发机是 aarch64，OpenShift 集群是 x86_64，不能用 `kn func deploy`（会构建错误架构的镜像）。使用 Tekton Pipeline 在集群上原生构建。

```bash
# 部署 Tekton 资源
oc apply -f tekton/deploy-ksvc-task.yaml
oc apply -f tekton/pipeline.yaml

# 触发 Pipeline
oc create -f tekton/pipelinerun.yaml
```

Pipeline 3 个阶段: git-clone → buildah build+push → oc apply Knative Service

**Service URL:** `https://fortigate-mcp-func-mcp-servers.apps.k7xm2q9n.okd.ink`

### OpenShift 集群注意事项

- **Tekton v0.39+** 已移除 ClusterTask，必须用 Cluster Resolver 引用 `openshift-pipelines` namespace 中的 Task（git-clone、buildah）
- **git-clone Task 参数名是大写**：`URL`、`REVISION`（不是小写）
- **registry.redhat.io 需要认证**：pipeline SA 默认没有 Red Hat Registry 凭证，需要通过 buildah 的 `dockerconfig` workspace 传入
- **推送到内部 registry 也需要认证**：需要合并内部 registry 和 Red Hat Registry 的凭证到一个 secret（`buildah-registry-auth`），通过 dockerconfig workspace 同时解决 pull 和 push 认证
- **pyproject.toml 引用了 README.md**：Dockerfile 中 COPY 必须包含 README.md，否则 hatchling 构建失败
- **KnativeServing 实例**：安装 Serverless Operator 后还需要手动创建 KnativeServing CR

### Secrets

- `fortigate-config` — FortiGate 设备凭证（envFrom 注入到 Knative Service）
- `buildah-registry-auth` — 合并的 registry 凭证（registry.redhat.io + 内部 registry），挂载为 buildah dockerconfig workspace
- `redhat-registry-auth` — Red Hat Registry 凭证（从 arc-runners namespace 复制）

## Testing

Tests use `pytest-asyncio` in **strict** mode (`asyncio_mode = "strict"`). Test functions must be decorated with `@pytest.mark.asyncio`. All FortiGate API calls are mocked — no real devices needed. 89 tests across 11 test files.
