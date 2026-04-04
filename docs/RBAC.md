# RBAC Reference Guide

This document provides a comprehensive reference for the Role-Based Access Control (RBAC) permissions required by the Home Assistant Kubernetes Integration.

## Quick Start

The `manifests/` directory contains two ready-to-apply sets of Kubernetes manifests. Pick the one that matches your requirements and apply it:

```bash
# Full permissions — monitoring + control (switches) + Watch API
kubectl apply -f manifests/full/

# Minimal permissions — read-only sensors only
kubectl apply -f manifests/minimal/
```

Both sets create the same `ServiceAccount` and `ClusterRoleBinding` in the `homeassistant` namespace. Adjust the namespace in `serviceaccount.yaml` and `clusterrolebinding.yaml` if your Home Assistant pod runs elsewhere.

## Manifest Sets

### `manifests/full/` — Recommended

Enables all integration features:

- Sensors and binary sensors (monitoring)
- Switches (deployment / statefulset scaling, CronJob suspension)
- Pod deletion from the sidebar panel (requires Home Assistant admin role)
- Experimental Watch API (real-time updates via `?watch=true`)
- Legacy API compatibility (Kubernetes < 1.16)

### `manifests/minimal/`

Read-only access to every resource the integration monitors. No write permissions.

**Limitations:**

- No switches (scaling or CronJob control)
- No Watch API support (`watch` verb not granted)
- Sensors and binary sensors only

## Complete Permission Matrix

### Core API Group (`""`)

| Resource | Verbs | Full | Minimal | Purpose |
|----------|-------|:----:|:-------:|---------|
| **pods** | `get`, `list`, `watch`, `delete` | ✅ | `get`, `list` only | Pod count and status sensors, pod deletion |
| **nodes** | `get`, `list`, `watch` | ✅ | `get`, `list` only | Node count sensors and binary sensors |
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

1. **Start Minimal**: Begin with `manifests/minimal/` and move to `manifests/full/` only when you need switches or the Watch API
2. **Namespace Scoping**: For multi-tenant clusters see the namespace-scoped example below
3. **Regular Audits**: Review permissions periodically
4. **Monitor Usage**: Track which permissions are actually used

### Risk Assessment

| Manifest Set | Risk Level | Capabilities |
|--------------|------------|--------------|
| **full** | Medium | Complete monitoring + control + Watch API |
| **minimal** | Low | Read-only sensors and binary sensors only |

### Token Security

1. **Secure Storage**: Store tokens securely in Home Assistant secrets
2. **Regular Rotation**: Rotate service account tokens periodically
3. **Audit Logs**: Monitor Kubernetes audit logs for token usage
4. **Network Security**: Ensure secure communication to the API server

## Namespace-Scoped Example

If you want to restrict access to specific namespaces instead of cluster-wide, use a `Role` + `RoleBinding` per namespace and a minimal `ClusterRole` for cluster-scoped resources (nodes, namespaces):

```yaml
# Cluster-scoped read access for nodes and namespace discovery
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: homeassistant-kubernetes-integration-cluster
rules:
- apiGroups: [""]
  resources: ["nodes", "namespaces"]
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
```

## Troubleshooting RBAC Issues

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

1. **Version Control**: Keep RBAC manifests in version control alongside your Home Assistant configuration
2. **Start Minimal**: Use `manifests/minimal/` first and upgrade to `manifests/full/` only when needed
3. **Testing**: Test permissions in a non-production cluster first
4. **Monitoring**: Watch for permission-denied errors in the Home Assistant logs
5. **Automation**: Manage manifests with your existing GitOps / infrastructure-as-code tooling

For setup instructions, see the [Service Account Setup Guide](SETUP.md).
