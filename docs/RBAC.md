# RBAC Reference Guide

This document provides a comprehensive reference for the Role-Based Access Control (RBAC) permissions required by the Home Assistant Kubernetes Integration.

## Quick Start

Two ways to install the same `ServiceAccount`, `ClusterRole`, `ClusterRoleBinding`, and token `Secret`. Pick whichever fits your workflow — the permissions are identical.

### Option A: Helm chart (recommended)

The chart is published to the GitHub Container Registry as an OCI artifact, so `helm upgrade` picks up new permissions as the integration gains features:

```bash
# Full permissions — monitoring + control (switches) + Watch API
helm install ha-k8s-rbac oci://ghcr.io/tibuntu/charts/homeassistant-kubernetes-rbac \
  --namespace homeassistant --create-namespace

# Minimal permissions — read-only sensors only
helm install ha-k8s-rbac oci://ghcr.io/tibuntu/charts/homeassistant-kubernetes-rbac \
  --namespace homeassistant --create-namespace \
  --set mode=minimal
```

Pin a version with `--version <chart version>`; the chart version tracks the integration version. To upgrade after updating the integration:

```bash
helm upgrade ha-k8s-rbac oci://ghcr.io/tibuntu/charts/homeassistant-kubernetes-rbac \
  --namespace homeassistant --reset-then-reuse-values
```

`--reset-then-reuse-values` resets to the new chart's defaults and then re-applies your own overrides, so newly added permissions actually land. (`--reuse-values` would keep your old value set verbatim and silently skip them.)

#### Already applied the plain manifests?

Helm refuses to adopt resources it did not create:

```text
Error: INSTALLATION FAILED: Unable to continue with install: ClusterRole
"homeassistant-kubernetes-integration" in namespace "" exists and cannot be
imported into the current release: invalid ownership metadata; label validation
error: missing key "app.kubernetes.io/managed-by": must be set to "Helm"
```

Add `--take-ownership` on the first install to adopt the existing objects instead of failing:

```bash
helm install ha-k8s-rbac oci://ghcr.io/tibuntu/charts/homeassistant-kubernetes-rbac \
  --namespace homeassistant --take-ownership
```

The chart renders the same objects with the same names, so this is an in-place adoption — no permission gap, nothing recreated. Requires Helm 3.17+. On older Helm, `kubectl delete -f manifests/full/` first, then install normally.

#### Chart values

| Value | Default | Purpose |
|-------|---------|---------|
| `mode` | `full` | Permission set: `full` or `minimal`. Anything else fails the render. |
| `nameOverride` | `""` | Name of the ServiceAccount, ClusterRole and ClusterRoleBinding. Defaults to `homeassistant-kubernetes-integration`. |
| `serviceAccount.create` | `true` | Set to `false` to bind the ClusterRole to a ServiceAccount you already manage. |
| `serviceAccount.annotations` | `{}` | Extra annotations on the ServiceAccount. |
| `tokenSecret.create` | `true` | Long-lived token Secret. Set to `false` when Home Assistant runs **inside** the cluster and uses the projected (auto-rotating) token. |
| `rbac.create` | `true` | Set to `false` to render only the ServiceAccount and token Secret. |
| `rbac.extraRules` | `[]` | Extra rules appended verbatim to the ClusterRole — e.g. adding `events` on top of `mode: minimal`. |

The release namespace (`--namespace`) determines the namespace of the ServiceAccount, the token Secret, and the ClusterRoleBinding subject.

### Option B: Plain manifests

The `manifests/` directory contains the same two sets as ready-to-apply YAML — no Helm required:

```bash
# Full permissions — monitoring + control (switches) + Watch API
kubectl apply -f manifests/full/

# Minimal permissions — read-only sensors only
kubectl apply -f manifests/minimal/
```

Both sets create the `ServiceAccount` and `ClusterRoleBinding` in the `homeassistant` namespace. Adjust the namespace in `serviceaccount.yaml`, `serviceaccount-token-secret.yaml`, and `clusterrolebinding.yaml` if your Home Assistant pod runs elsewhere.

> **Note:** `manifests/` is generated from `chart/` (see [Development Guide](DEVELOPMENT.md#rbac-and-the-helm-chart)) — the two are always in sync, so `mode: full` and `manifests/full/` grant exactly the same permissions.

## Permission Sets

### `full` / `manifests/full/` — Recommended

Enables all integration features:

- Sensors and binary sensors (monitoring)
- Switches (deployment / statefulset scaling, CronJob suspension, node cordon/uncordon)
- Workload rollout restart (deployments, statefulsets, daemonsets)
- Ingress monitoring (Network tab in the sidebar panel, with clickable URLs)
- Pod and Job deletion from the sidebar panel (requires Home Assistant admin role)
- Cluster Events platform (`events`)
- Experimental Watch API (real-time updates via `?watch=true`)
- Legacy API compatibility (Kubernetes < 1.16)

### `minimal` / `manifests/minimal/`

Read-only access to every resource the integration monitors. No write permissions.

**Limitations:**

- No switches (scaling, CronJob control, or node cordon/uncordon)
- No rollout restart, pod deletion, or Job deletion
- No Cluster Events platform (`events` not granted)
- No Watch API support (`watch` verb not granted)
- Sensors and binary sensors only

## Complete Permission Matrix

### Core API Group (`""`)

| Resource | Verbs | Full | Minimal | Purpose |
|----------|-------|:----:|:-------:|---------|
| **pods** | `get`, `list`, `watch`, `delete` | ✅ | `get`, `list` only | Pod count and status sensors, pod deletion |
| **nodes** | `get`, `list`, `watch`, `patch` | ✅ | `get`, `list` only | Node sensors and binary sensors; `patch` enables cordon/uncordon |
| **namespaces** | `get`, `list` | ✅ | ✅ | Namespace discovery |
| **events** | `get`, `list`, `watch` | ✅ | ❌ | Enhanced troubleshooting |

### Apps API Group (`apps`)

| Resource | Verbs | Full | Minimal | Purpose |
|----------|-------|:----:|:-------:|---------|
| **deployments** | `get`, `list`, `watch`, `patch` | ✅ | `get`, `list` only | Deployment sensors + rollout restart |
| **deployments/scale** | `get`, `patch`, `update` | ✅ | ❌ | Deployment switches |
| **replicasets** | `get`, `list`, `watch` | ✅ | ❌ | Deployment status accuracy |
| **statefulsets** | `get`, `list`, `watch`, `patch` | ✅ | `get`, `list` only | StatefulSet sensors + rollout restart |
| **statefulsets/scale** | `get`, `patch`, `update` | ✅ | ❌ | StatefulSet switches |
| **statefulsets/status** | `get`, `patch`, `update` | ✅ | ❌ | Accurate StatefulSet state |
| **daemonsets** | `get`, `list`, `watch`, `patch` | ✅ | `get`, `list` only | DaemonSet sensors + rollout restart |

### Batch API Group (`batch`)

| Resource | Verbs | Full | Minimal | Purpose |
|----------|-------|:----:|:-------:|---------|
| **cronjobs** | `get`, `list`, `watch` | ✅ | `get`, `list` only | CronJob sensors |
| **cronjobs/status** | `get`, `patch`, `update` | ✅ | ❌ | CronJob switch (suspend/resume) |
| **jobs** | `get`, `list`, `watch`, `create` | ✅ | `get`, `list` only | Job sensors + CronJob triggering |

### Networking API Group (`networking.k8s.io`)

| Resource | Verbs | Full | Minimal | Purpose |
|----------|-------|:----:|:-------:|---------|
| **ingresses** | `get`, `list`, `watch` | ✅ | `get`, `list` only | Ingresses count sensor + Network tab in the sidebar panel |

### Metrics API Group (`metrics.k8s.io`)

| Resource | Verbs | Full | Minimal | Purpose |
|----------|-------|:----:|:-------:|---------|
| **nodes** | `get`, `list` | ✅ | ✅ | Real-time node CPU and memory usage in the sidebar panel |
| **pods** | `get`, `list` | ✅ | ✅ | Workload CPU and memory usage sensors |

> **Note:** Requires [metrics-server](https://github.com/kubernetes-sigs/metrics-server) to be installed in your cluster. If unavailable, the integration gracefully falls back to showing capacity only.

### Extensions API Group (`extensions`)

| Resource | Verbs | Full | Minimal | Purpose |
|----------|-------|:----:|:-------:|---------|
| **deployments** | `get`, `list`, `watch` | ✅ | ❌ | Legacy API (K8s < 1.16) |
| **deployments/scale** | `get`, `patch`, `update` | ✅ | ❌ | Legacy scaling (K8s < 1.16) |
| **replicasets** | `get`, `list`, `watch` | ✅ | ❌ | Legacy API (K8s < 1.16) |

## Security Considerations

### Principle of Least Privilege

1. **Start Minimal**: Begin with `mode: minimal` (`manifests/minimal/`) and move to `full` only when you need switches or the Watch API
2. **Namespace Scoping**: For multi-tenant clusters see the namespace-scoped example below
3. **Regular Audits**: Review permissions periodically
4. **Monitor Usage**: Track which permissions are actually used

### Risk Assessment

| Permission Set | Risk Level | Capabilities |
|----------------|------------|--------------|
| **full** | Medium | Complete monitoring + control + Watch API |
| **minimal** | Low | Read-only sensors and binary sensors only |

### Token Security

1. **Secure Storage**: Store tokens securely in Home Assistant secrets
2. **Regular Rotation**: Rotate service account tokens periodically
3. **Audit Logs**: Monitor Kubernetes audit logs for token usage
4. **Network Security**: Ensure secure communication to the API server

## In-Cluster ServiceAccount (recommended when HA runs inside the cluster)

If the Home Assistant pod runs inside the same cluster it monitors, the integration can bind to the pod's ServiceAccount directly instead of using a manually-extracted token. This is the preferred path because:

- **No token extraction step.** The pod already has the projected token mounted at `/var/run/secrets/kubernetes.io/serviceaccount/token`.
- **Automatic rotation.** Kubernetes 1.21+ rotates projected ServiceAccount tokens (commonly hourly). With **Use in-cluster ServiceAccount at runtime** enabled in the config flow, the integration re-reads the token file on each request and follows the rotation seamlessly. With this setting off, the captured-at-config-time token will eventually expire and auth-fail.
- **No persisted credential.** The token never leaves the projected tmpfs; it is not written to Home Assistant's config store.
- **Same RBAC rules apply.** The permission matrix above is unchanged — bind the existing `ClusterRole` (or namespace-scoped `Role`) to the ServiceAccount that the HA pod uses.

### Pod spec

Set `serviceAccountName` on the Home Assistant pod (or Deployment / StatefulSet) to the same SA referenced by your `ClusterRoleBinding`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: homeassistant
  namespace: homeassistant
spec:
  template:
    spec:
      # Bind the integration's SA to the HA pod itself.
      serviceAccountName: homeassistant-kubernetes-integration
      # automountServiceAccountToken: true is the default and is required for
      # the projected volume to be mounted at the standard path. Do not set
      # this to false if you want in-cluster auth.
      containers:
        - name: homeassistant
          image: ghcr.io/home-assistant/home-assistant:latest
```

### Config flow

When Home Assistant detects it is running inside a cluster (the `KUBERNETES_SERVICE_HOST` env var is set **and** the projected token file is readable):

- The **Host**, **Port**, **API Token**, and **CA Certificate** fields on the *Add Integration* form are pre-filled from the pod's ServiceAccount.
- A **Use in-cluster ServiceAccount at runtime** checkbox is shown and defaults to enabled. Leave it on so the integration re-reads the token file on each call and survives token rotation.
- The token entered in the form is kept only as a fallback — used if the projected volume becomes unreadable for any reason (e.g. HA was later moved out of the cluster).

The same checkbox is also available in **Configure → Reconfigure** if you want to flip an existing entry between in-cluster and static-token modes without re-creating it.

### Verifying

Once the HA pod is running with the bound ServiceAccount, you can verify access using the SA's identity:

```bash
# Use the pod's SA token directly (works from any pod in the same namespace)
kubectl auth can-i list pods \
  --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# From inside the HA pod itself, hit the API server with the projected token
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
curl -sS \
  --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  -H "Authorization: Bearer $TOKEN" \
  https://kubernetes.default.svc/api/v1/namespaces
```

## Namespace-Scoped Example

If you want to restrict access to specific namespaces instead of cluster-wide, use a `Role` + `RoleBinding` per namespace and a minimal `ClusterRole` for cluster-scoped resources (nodes, namespaces):

```yaml
# Cluster-scoped access for nodes and namespace discovery.
# Drop `patch` on nodes if you do not want cordon/uncordon — nodes are
# cluster-scoped, so there is no namespaced equivalent.
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: homeassistant-kubernetes-integration-cluster
rules:
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["get", "list", "patch"]
- apiGroups: [""]
  resources: ["namespaces"]
  verbs: ["get", "list"]
---
# Namespace-scoped role (repeat per monitored namespace)
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: target-namespace
  name: homeassistant-kubernetes-integration
rules:
- apiGroups: [""]
  resources: ["pods", "events"]
  verbs: ["get", "list", "watch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "statefulsets", "daemonsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments/scale", "statefulsets/scale", "statefulsets/status"]
  verbs: ["get", "patch", "update"]
- apiGroups: ["batch"]
  resources: ["cronjobs", "cronjobs/status", "jobs"]
  verbs: ["get", "list", "watch", "patch", "update", "create"]
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses"]
  verbs: ["get", "list", "watch"]
```

## Troubleshooting RBAC Issues

> The fixes below say "Apply `manifests/full/`". With the Helm chart the equivalent is `helm upgrade ... --set mode=full`.

### Common Permission Errors

#### 1. "Forbidden: User cannot list pods"

```bash
# Verify pod permissions
kubectl auth can-i list pods --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Fix: Apply manifests/minimal/ or manifests/full/
```

#### 2. "Forbidden: User cannot patch deployments/scale"

```bash
# Verify scaling permissions
kubectl auth can-i patch deployments/scale --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Verify node cordon/uncordon permissions (node schedulable switches)
kubectl auth can-i patch nodes --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Fix: Apply manifests/full/ — the minimal set does not grant write permissions
```

#### 3. "Real-time updates not working" / Watch API failing

The experimental **Watch API** (enabled via **Configure → Enable Watch API**) uses long-lived HTTP streams and requires the `watch` verb on all monitored resources. The `manifests/minimal/` set does **not** include `watch` verbs.

```bash
# Verify watch permissions for key resources
kubectl auth can-i watch pods --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration
kubectl auth can-i watch deployments --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration
kubectl auth can-i watch nodes --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Fix: Apply manifests/full/ to grant the watch verb
```

#### 4. Node CPU/memory usage not showing in sidebar panel

The sidebar panel shows node capacity but no real-time usage data. This requires [metrics-server](https://github.com/kubernetes-sigs/metrics-server) and `metrics.k8s.io` RBAC permissions.

```bash
# Verify metrics-server is running
kubectl get pods -n kube-system -l k8s-app=metrics-server

# Verify node metrics permissions
kubectl auth can-i list nodes.metrics.k8s.io --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Fix: Apply manifests/full/ or manifests/minimal/ (both include metrics permissions)
```

#### 5. "Forbidden: User cannot list cronjobs"

```bash
# Verify CronJob permissions
kubectl auth can-i list cronjobs --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Fix: Apply manifests/minimal/ or manifests/full/
```

#### 6. "Forbidden: User cannot create jobs"

```bash
# Verify job creation permissions (needed for CronJob triggering)
kubectl auth can-i create jobs --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Fix: Apply manifests/full/ — the minimal set only grants get and list on jobs
```

#### 7. "Forbidden: User cannot delete pods"

Pod deletion requires **both** Home Assistant admin role and Kubernetes RBAC permissions. Non-admin HA users will not see the delete action succeed, as the WebSocket command enforces admin access.

```bash
# Verify pod deletion permissions
kubectl auth can-i delete pods --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Fix: Apply manifests/full/ — the minimal set does not grant delete permissions
```

### Diagnostic Commands

```bash
# Check all permissions for the service account
kubectl auth can-i --list --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Test specific resource access in a namespace
kubectl auth can-i get deployments --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration -n your-namespace

# View effective permissions
kubectl describe clusterrolebinding homeassistant-kubernetes-integration
kubectl describe clusterrole homeassistant-kubernetes-integration
```

## Best Practices

1. **Version Control**: Keep your chart values (or the RBAC manifests) in version control alongside your Home Assistant configuration
2. **Start Minimal**: Use `mode: minimal` first and upgrade to `full` only when needed
3. **Stay Current**: Run `helm upgrade` after updating the integration — new features occasionally need new verbs
4. **Testing**: Test permissions in a non-production cluster first
5. **Monitoring**: Watch for permission-denied errors in the Home Assistant logs
6. **Automation**: Manage the chart with your existing GitOps / infrastructure-as-code tooling (Flux `HelmRelease`, Argo CD, Terraform `helm_release`, …)

For setup instructions, see the [Service Account Setup Guide](SETUP.md).
