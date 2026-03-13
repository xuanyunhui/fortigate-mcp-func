# Tekton CD Pipeline for FortiGate MCP Knative Function

## Overview

Tekton Pipeline on OpenShift (x86_64) to build and deploy the FortiGate MCP Knative Function from a GitHub public repository. Manual trigger via `oc create -f pipelinerun.yaml`.

## Problem

Development machine is aarch64 but the OpenShift cluster is x86_64. `kn func build --builder=host` produces aarch64 images that won't run on the cluster. The Pipeline builds natively on the cluster.

## Architecture

```
GitHub (public repo)
    │
    ▼ git-clone
Tekton Pipeline (x86_64 OpenShift)
    │
    ├─ Task 1: fetch-source       ── ClusterTask: git-clone
    ├─ Task 2: build-and-push     ── ClusterTask: buildah (build Dockerfile, push to internal registry)
    └─ Task 3: deploy             ── Custom Task: oc apply Knative Service YAML

Image Registry: image-registry.openshift-image-registry.svc:5000/mcp-servers/fortigate-mcp-func
```

## Dockerfile

Located at project root. Based on UBI10 Python 3.12 minimal image.

```dockerfile
FROM registry.redhat.io/ubi10/python-312-minimal:10.1

WORKDIR /opt/app-root/src

COPY pyproject.toml .
COPY function/ function/
RUN pip install --no-cache-dir func-python==0.7.0 httpx .

RUN echo 'from func_python.http import serve; from function import new; serve(new)' > main.py

EXPOSE 8080
CMD ["python", "main.py"]
```

## Pipeline Definition

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `repo-url` | (required) | GitHub repository URL |
| `revision` | `main` | Branch or tag to build |
| `image` | `image-registry.openshift-image-registry.svc:5000/mcp-servers/fortigate-mcp-func` | Target image reference |

### Workspaces

| Workspace | Type | Description |
|-----------|------|-------------|
| `source` | PVC (VolumeClaimTemplate, 1Gi) | Shared source code between tasks |

### Tasks

**1. fetch-source** (ClusterTask: `git-clone`)
- Clones the GitHub repo into the `source` workspace

**2. build-and-push** (ClusterTask: `buildah`)
- Builds the Dockerfile in the workspace
- Pushes to the internal OpenShift image registry
- Runs after fetch-source

**3. deploy** (Custom Task: `deploy-ksvc`)
- Applies a Knative Service manifest via `oc apply`
- The Knative Service references the built image and `fortigate-config` Secret via `envFrom`
- Runs after build-and-push

## Knative Service Manifest

Applied by the deploy task:

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: fortigate-mcp-func
spec:
  template:
    spec:
      containers:
      - image: <pipeline-image-param>:latest
        envFrom:
        - secretRef:
            name: fortigate-config
        ports:
        - containerPort: 8080
```

The `fortigate-config` Secret injects all `FORTIGATE_DEVICE_*` environment variables. The `start(cfg)` method in `func.py` passes `os.environ.copy()` to `load_devices_from_env()`.

## Device Credentials

Managed via OpenShift Secret (pre-existing, not created by Pipeline):

```bash
oc create secret generic fortigate-config \
  --from-literal=FORTIGATE_DEVICE_FW01_HOST=172.16.255.2 \
  --from-literal=FORTIGATE_DEVICE_FW01_API_TOKEN=<token>
```

## Files to Create

| File | Description |
|------|-------------|
| `Dockerfile` | Container image build definition |
| `tekton/pipeline.yaml` | Pipeline with 3 tasks |
| `tekton/pipelinerun.yaml` | Manual trigger PipelineRun template |
| `tekton/deploy-ksvc-task.yaml` | Custom Task for deploying Knative Service |

## Usage

```bash
# 1. Ensure fortigate-config Secret exists
# 2. Apply Tekton resources
oc apply -f tekton/deploy-ksvc-task.yaml
oc apply -f tekton/pipeline.yaml

# 3. Trigger pipeline
oc create -f tekton/pipelinerun.yaml

# 4. Monitor
tkn pipelinerun logs -f

# 5. Verify
URL=$(oc get ksvc fortigate-mcp-func -o jsonpath='{.status.url}')
curl -X POST $URL -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"ping"}'
```
