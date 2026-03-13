# Tekton CD Pipeline Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a Tekton Pipeline that builds and deploys the FortiGate MCP Knative Function on x86_64 OpenShift from a GitHub public repo.

**Architecture:** Tekton Pipeline with 3 tasks: git-clone → buildah build+push → oc apply Knative Service. Uses OpenShift internal image registry. Device credentials via pre-existing `fortigate-config` Secret.

**Tech Stack:** Tekton Pipelines, Buildah, OpenShift CLI, Knative Serving

**Spec:** `docs/superpowers/specs/2026-03-13-tekton-cd-pipeline-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `Dockerfile` | Container image definition (UBI10 + func-python + project code) |
| `tekton/deploy-ksvc-task.yaml` | Custom Tekton Task: deploy Knative Service via `oc apply` |
| `tekton/pipeline.yaml` | Pipeline definition: git-clone → buildah → deploy |
| `tekton/pipelinerun.yaml` | PipelineRun template for manual trigger |

---

## Chunk 1: Dockerfile + Tekton Resources

### Task 1: Create Dockerfile

**Files:**
- Create: `Dockerfile`

- [ ] **Step 1: Write Dockerfile**

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

- [ ] **Step 2: Commit**

```bash
git add Dockerfile
git commit -m "feat: add Dockerfile for x86_64 container build"
```

---

### Task 2: Create deploy-ksvc custom Task

**Files:**
- Create: `tekton/deploy-ksvc-task.yaml`

- [ ] **Step 1: Create tekton directory**

```bash
mkdir -p tekton
```

- [ ] **Step 2: Write deploy-ksvc-task.yaml**

This Task takes an image parameter, generates a Knative Service YAML inline, and applies it with `oc apply`.

```yaml
apiVersion: tekton.dev/v1
kind: Task
metadata:
  name: deploy-ksvc
spec:
  params:
    - name: image
      type: string
      description: Container image reference for the Knative Service
    - name: service-name
      type: string
      default: fortigate-mcp-func
      description: Name of the Knative Service
    - name: secret-name
      type: string
      default: fortigate-config
      description: Secret to inject as environment variables
  steps:
    - name: deploy
      image: image-registry.openshift-image-registry.svc:5000/openshift/cli:latest
      script: |
        #!/usr/bin/env bash
        set -euo pipefail
        cat <<EOF | oc apply -f -
        apiVersion: serving.knative.dev/v1
        kind: Service
        metadata:
          name: $(params.service-name)
        spec:
          template:
            spec:
              containers:
              - image: $(params.image)
                envFrom:
                - secretRef:
                    name: $(params.secret-name)
                ports:
                - containerPort: 8080
        EOF
        echo "Waiting for Knative Service to become ready..."
        oc wait ksvc/$(params.service-name) --for=condition=Ready --timeout=120s
        URL=$(oc get ksvc $(params.service-name) -o jsonpath='{.status.url}')
        echo "Deployed: $URL"
```

- [ ] **Step 3: Commit**

```bash
git add tekton/deploy-ksvc-task.yaml
git commit -m "feat: add deploy-ksvc Tekton Task"
```

---

### Task 3: Create Pipeline

**Files:**
- Create: `tekton/pipeline.yaml`

- [ ] **Step 1: Write pipeline.yaml**

```yaml
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: fortigate-mcp-func-deploy
spec:
  params:
    - name: repo-url
      type: string
      description: Git repository URL
    - name: revision
      type: string
      default: main
      description: Git revision (branch, tag, or commit)
    - name: image
      type: string
      default: image-registry.openshift-image-registry.svc:5000/mcp-servers/fortigate-mcp-func
      description: Target container image reference
  workspaces:
    - name: source
  tasks:
    - name: fetch-source
      taskRef:
        kind: ClusterTask
        name: git-clone
      params:
        - name: url
          value: $(params.repo-url)
        - name: revision
          value: $(params.revision)
      workspaces:
        - name: output
          workspace: source

    - name: build-and-push
      taskRef:
        kind: ClusterTask
        name: buildah
      runAfter:
        - fetch-source
      params:
        - name: IMAGE
          value: $(params.image):$(params.revision)
      workspaces:
        - name: source
          workspace: source

    - name: deploy
      taskRef:
        kind: Task
        name: deploy-ksvc
      runAfter:
        - build-and-push
      params:
        - name: image
          value: $(params.image):$(params.revision)
```

- [ ] **Step 2: Commit**

```bash
git add tekton/pipeline.yaml
git commit -m "feat: add Tekton Pipeline (git-clone, buildah, deploy-ksvc)"
```

---

### Task 4: Create PipelineRun template

**Files:**
- Create: `tekton/pipelinerun.yaml`

- [ ] **Step 1: Write pipelinerun.yaml**

```yaml
apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  generateName: fortigate-mcp-func-deploy-
spec:
  pipelineRef:
    name: fortigate-mcp-func-deploy
  params:
    - name: repo-url
      value: https://github.com/YOUR_USERNAME/fortigate-mcp-func.git
    - name: revision
      value: main
    - name: image
      value: image-registry.openshift-image-registry.svc:5000/mcp-servers/fortigate-mcp-func
  workspaces:
    - name: source
      volumeClaimTemplate:
        spec:
          accessModes:
            - ReadWriteOnce
          resources:
            requests:
              storage: 1Gi
```

> **Note:** Replace `YOUR_USERNAME` with your actual GitHub username after pushing the repo.

- [ ] **Step 2: Commit**

```bash
git add tekton/pipelinerun.yaml
git commit -m "feat: add PipelineRun template for manual trigger"
```

---

## Chunk 2: Deploy and Verify

### Task 5: Push code to GitHub and run Pipeline

- [ ] **Step 1: Create GitHub repo and push**

```bash
gh repo create fortigate-mcp-func --public --source=. --push
```

- [ ] **Step 2: Update pipelinerun.yaml with actual repo URL**

Replace `YOUR_USERNAME` in `tekton/pipelinerun.yaml` with the actual GitHub username from step 1.

- [ ] **Step 3: Commit the URL update**

```bash
git add tekton/pipelinerun.yaml
git commit -m "chore: set actual GitHub repo URL in pipelinerun"
git push
```

- [ ] **Step 4: Ensure fortigate-config Secret exists on cluster**

```bash
oc get secret fortigate-config || \
oc create secret generic fortigate-config \
  --from-literal=FORTIGATE_DEVICE_FW01_HOST=172.16.255.2 \
  --from-literal=FORTIGATE_DEVICE_FW01_API_TOKEN=<your-token>
```

- [ ] **Step 5: Apply Tekton resources**

```bash
oc apply -f tekton/deploy-ksvc-task.yaml
oc apply -f tekton/pipeline.yaml
```

- [ ] **Step 6: Trigger the Pipeline**

```bash
oc create -f tekton/pipelinerun.yaml
```

- [ ] **Step 7: Monitor and verify**

```bash
# Watch pipeline logs
tkn pipelinerun logs -f

# After completion, verify
URL=$(oc get ksvc fortigate-mcp-func -o jsonpath='{.status.url}')

# Test ping
curl -X POST $URL -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"ping"}'

# Test tools/list
curl -X POST $URL -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'

# Test list_devices
curl -X POST $URL -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_devices","arguments":{}}}'
```
