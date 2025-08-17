# RBAC Reference Guide

This document provides a comprehensive reference for the Role-Based Access Control (RBAC) permissions required by the Home Assistant Kubernetes Integration.

## Overview

The integration requires specific Kubernetes RBAC permissions to monitor cluster resources and control workloads. This document explains each permission, why it's needed, and provides alternatives for different security scenarios.

## Complete Permission Matrix

### Core API Group (`""`)

| Resource | Verbs | Required | Purpose | Impact if Missing |
|----------|-------|----------|---------|-------------------|
| **pods** | `get`, `list`, `watch` | ✅ | Monitor pod counts and status | No pod count sensors |
| **nodes** | `get`, `list`, `watch` | ✅ | Monitor cluster node count | No node count sensors |
| **namespaces** | `get`, `list` | ✅ | List available namespaces for monitoring | Cannot discover namespaces |
| **events** | `get`, `list`, `watch` | ⚠️ | Enhanced troubleshooting and monitoring | Reduced troubleshooting capability |

### Apps API Group (`apps`)

| Resource | Verbs | Required | Purpose | Impact if Missing |
|----------|-------|----------|---------|-------------------|
| **deployments** | `get`, `list`, `watch` | ✅ | Monitor deployment status and count | No deployment sensors or switches |
| **deployments/scale** | `get`, `patch`, `update`, `create`, `delete` | ✅ | Scale deployments up/down | Cannot control deployment switches |
| **replicasets** | `get`, `list`, `watch` | ⚠️ | Monitor underlying deployment resources | Limited deployment status accuracy |
| **statefulsets** | `get`, `list`, `watch` | ✅ | Monitor statefulset status and count | No statefulset sensors or switches |
| **statefulsets/scale** | `get`, `patch`, `update`, `create`, `delete` | ✅ | Scale statefulsets up/down | Cannot control statefulset switches |
| **statefulsets/status** | `get`, `patch`, `update` | ⚠️ | Accurate statefulset state reporting | Potential state inconsistencies |

### Extensions API Group (`extensions`)

| Resource | Verbs | Required | Purpose | Impact if Missing |
|----------|-------|----------|---------|-------------------|
| **deployments** | `get`, `list`, `watch` | ⚠️ | Legacy API compatibility (K8s < 1.16) | May not work on older clusters |
| **deployments/scale** | `get`, `patch`, `update`, `create`, `delete` | ⚠️ | Legacy scaling API compatibility | May not work on older clusters |
| **replicasets** | `get`, `list`, `watch` | ⚠️ | Legacy API compatibility | May not work on older clusters |

**Legend:**

- ✅ **Required**: Essential for core functionality
- ⚠️ **Recommended**: Enhances functionality or compatibility
- ❌ **Not Used**: Not required by the integration

## Permission Scenarios

### Scenario 1: Full Cluster Access (Recommended)

**Use Case**: Complete monitoring and control across all namespaces
**Security Level**: Medium - requires cluster-wide permissions

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: homeassistant-kubernetes-integration
rules:
# Monitoring permissions
- apiGroups: [""]
  resources: ["pods", "nodes", "namespaces", "events"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "statefulsets"]
  verbs: ["get", "list", "watch"]
# Control permissions
- apiGroups: ["apps"]
  resources: ["deployments", "deployments/scale", "statefulsets", "statefulsets/scale", "statefulsets/status"]
  verbs: ["get", "patch", "update", "create", "delete"]
# Legacy compatibility
- apiGroups: ["extensions"]
  resources: ["deployments", "deployments/scale", "replicasets"]
  verbs: ["get", "list", "watch", "patch", "update", "create", "delete"]
```

### Scenario 2: Read-Only Monitoring

**Use Case**: Monitoring only, no control capabilities
**Security Level**: High - no write permissions

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: homeassistant-kubernetes-integration-readonly
rules:
- apiGroups: [""]
  resources: ["pods", "nodes", "namespaces", "events"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "statefulsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["extensions"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
```

**Limitations:**

- No switches will be created
- No scaling services available
- Sensors and binary sensors only

### Scenario 3: Namespace-Scoped

**Use Case**: Limit access to specific namespaces
**Security Level**: High - limited scope

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: target-namespace
  name: homeassistant-kubernetes-integration
rules:
- apiGroups: [""]
  resources: ["pods", "events"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "statefulsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "deployments/scale", "statefulsets", "statefulsets/scale", "statefulsets/status"]
  verbs: ["get", "patch", "update", "create", "delete"]
```

**Additional Requirements:**

```yaml
# Minimal cluster permissions for basic functionality
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: homeassistant-kubernetes-integration-minimal
rules:
- apiGroups: [""]
  resources: ["nodes", "namespaces"]
  verbs: ["get", "list"]
```

### Scenario 4: Minimal Permissions

**Use Case**: Absolute minimum permissions for basic operation
**Security Level**: Very High - extremely limited

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: homeassistant-kubernetes-integration-minimal
rules:
# Core monitoring only
- apiGroups: [""]
  resources: ["pods", "nodes"]
  verbs: ["get", "list"]
- apiGroups: ["apps"]
  resources: ["deployments", "statefulsets"]
  verbs: ["get", "list"]
```

**Severe Limitations:**

- No real-time updates (no `watch`)
- No control capabilities
- No event access for troubleshooting
- Limited sensor accuracy

## Security Considerations

### Principle of Least Privilege

1. **Start Minimal**: Begin with read-only permissions and add as needed
2. **Namespace Scoping**: Use namespace-scoped roles when possible
3. **Regular Audits**: Review permissions periodically
4. **Monitor Usage**: Track which permissions are actually used

### Risk Assessment

| Permission Level | Risk Level | Capabilities | Recommendation |
|------------------|------------|--------------|----------------|
| **Full Cluster** | Medium | Complete monitoring + control | Production clusters with dedicated SA |
| **Read-Only** | Low | Monitoring only | Security-sensitive environments |
| **Namespace-Scoped** | Low-Medium | Limited scope control | Multi-tenant clusters |
| **Minimal** | Very Low | Basic monitoring | Proof of concept only |

### Token Security

1. **Secure Storage**: Store tokens securely in Home Assistant secrets
2. **Regular Rotation**: Rotate service account tokens periodically
3. **Audit Logs**: Monitor Kubernetes audit logs for token usage
4. **Network Security**: Ensure secure communication to API server

## Troubleshooting RBAC Issues

### Common Permission Errors

#### 1. "Forbidden: User cannot list pods"

```bash
# Verify pod permissions
kubectl auth can-i list pods --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Fix: Ensure pods are included in the role with 'get', 'list' verbs
```

#### 2. "Forbidden: User cannot patch deployments/scale"

```bash
# Verify scaling permissions
kubectl auth can-i patch deployments/scale --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Fix: Ensure deployments/scale subresource has 'patch' verb
```

#### 3. "Real-time updates not working"

```bash
# Verify watch permissions
kubectl auth can-i watch pods --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Fix: Add 'watch' verb to relevant resources
```

### Diagnostic Commands

```bash
# Check all permissions for the service account
kubectl auth can-i --list --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Test specific resource access
kubectl auth can-i get deployments --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration -n your-namespace

# View effective permissions
kubectl describe clusterrolebinding homeassistant-kubernetes-integration
kubectl describe clusterrole homeassistant-kubernetes-integration
```

## Best Practices

1. **Version Control**: Keep RBAC manifests in version control
2. **Documentation**: Document why each permission is needed
3. **Testing**: Test permissions in non-production first
4. **Monitoring**: Monitor for permission denied errors
5. **Automation**: Use infrastructure as code for RBAC setup

For implementation details, see the [Service Account Setup Guide](SETUP.md).
