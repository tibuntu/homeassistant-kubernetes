# Service Account Setup Guide

This guide walks you through setting up the required Kubernetes service account and RBAC permissions for the Home Assistant Kubernetes Integration.

## Quick Setup

For a quick setup using the provided manifests:

### 1. Apply Required Manifests

```bash
kubectl apply -f manifests/serviceaccount.yaml
kubectl apply -f manifests/clusterrole.yaml
kubectl apply -f manifests/clusterrolebinding.yaml
kubectl apply -f manifests/serviceaccount-token-secret.yaml
```

### 2. Extract the Token

```bash
kubectl get secret homeassistant-kubernetes-integration-token -n homeassistant -o jsonpath='{.data.token}' | base64 -d
```

Copy this token for use in the Home Assistant configuration.

## Step-by-Step Setup

If you prefer to understand each step or need to customize the setup:

### 1. Create Service Account

```bash
kubectl apply -f manifests/serviceaccount.yaml
```

This creates a service account named `homeassistant-kubernetes-integration` in the `homeassistant` namespace.

### 2. Create Cluster Role

```bash
kubectl apply -f manifests/clusterrole.yaml
```

This defines the RBAC permissions required for monitoring and controlling Kubernetes resources.

### 3. Create Cluster Role Binding

```bash
kubectl apply -f manifests/clusterrolebinding.yaml
```

This binds the cluster role to the service account, granting the necessary permissions.

### 4. Create Token Secret

```bash
kubectl apply -f manifests/serviceaccount-token-secret.yaml
```

This creates a secret containing the service account token for authentication.

### 5. Extract the Token

```bash
kubectl get secret homeassistant-kubernetes-integration-token -n homeassistant -o jsonpath='{.data.token}' | base64 -d
```

## RBAC Permissions

The integration requires comprehensive permissions for monitoring and controlling Kubernetes resources. The actual permissions are defined in the `manifests/clusterrole.yaml` file.

### Complete Cluster Role Permissions

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: homeassistant-kubernetes-integration
rules:
# Read permissions for monitoring
- apiGroups: [""]
  resources: ["pods", "nodes", "namespaces"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "statefulsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["extensions"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
# Write permissions for control - including scaling
- apiGroups: ["apps"]
  resources: ["deployments", "deployments/scale", "statefulsets", "statefulsets/scale"]
  verbs: ["patch", "update", "get", "create", "delete"]
- apiGroups: ["extensions"]
  resources: ["deployments", "deployments/scale"]
  verbs: ["patch", "update", "get", "create", "delete"]
# Events for better monitoring and troubleshooting
- apiGroups: [""]
  resources: ["events"]
  verbs: ["get", "list", "watch"]
# StatefulSet status for accurate state reporting
- apiGroups: ["apps"]
  resources: ["statefulsets/status"]
  verbs: ["get", "patch", "update"]
# Batch API permissions for CronJobs
- apiGroups: ["batch"]
  resources: ["cronjobs", "jobs"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["batch"]
  resources: ["cronjobs", "cronjobs/status", "jobs"]
  verbs: ["get", "patch", "update", "create"]
```

### Permission Breakdown

| API Group | Resource | Verbs | Purpose |
|-----------|----------|-------|---------|
| **""** (Core) | **pods** | `get`, `list`, `watch` | Monitor pod counts and status across namespaces |
| **""** (Core) | **nodes** | `get`, `list`, `watch` | Monitor cluster nodes count and health |
| **""** (Core) | **namespaces** | `get`, `list` | List and access namespaces for monitoring |
| **""** (Core) | **events** | `get`, `list`, `watch` | Access events for troubleshooting and monitoring |
| **apps** | **deployments** | `get`, `list`, `watch` | Monitor deployment status and metadata |
| **apps** | **deployments/scale** | `patch`, `update`, `get`, `create`, `delete` | Scale deployments up/down |
| **apps** | **replicasets** | `get`, `list`, `watch` | Monitor replica sets (underlying deployment resource) |
| **apps** | **statefulsets** | `get`, `list`, `watch` | Monitor statefulset status and metadata |
| **apps** | **statefulsets/scale** | `patch`, `update`, `get`, `create`, `delete` | Scale statefulsets up/down |
| **apps** | **statefulsets/status** | `get`, `patch`, `update` | Update and monitor statefulset status |
| **batch** | **cronjobs** | `get`, `list`, `watch` | Monitor CronJob status and metadata |
| **batch** | **cronjobs/status** | `get`, `patch`, `update` | Update and monitor CronJob status |
| **batch** | **jobs** | `get`, `list`, `watch`, `create` | Monitor and create jobs (for CronJob triggering) |
| **extensions** | **deployments** | `get`, `list`, `watch` | Legacy API compatibility for older clusters |
| **extensions** | **deployments/scale** | `patch`, `update`, `get`, `create`, `delete` | Legacy scaling API compatibility |

### Why These Permissions Are Required

#### Monitoring Permissions (`get`, `list`, `watch`)

- **Essential for sensor data**: Pod counts, node counts, deployment status
- **Real-time updates**: `watch` enables efficient real-time monitoring
- **Cross-namespace visibility**: Required when monitoring all namespaces

#### Control Permissions (`patch`, `update`, `create`, `delete`)

- **Scaling operations**: Required to scale deployments and statefulsets
- **State management**: Update resource scales and status
- **Switch functionality**: Enable on/off control of workloads

#### Legacy API Groups

- **extensions**: Provides compatibility with older Kubernetes clusters
- **Dual API coverage**: Ensures the integration works across different cluster versions

## Namespace-Specific Setup

If you prefer to limit permissions to specific namespaces for enhanced security:

### 1. Create Service Account in Target Namespace

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: homeassistant-kubernetes-integration
  namespace: your-target-namespace
```

### 2. Create Role (instead of ClusterRole)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: your-target-namespace
  name: homeassistant-kubernetes-integration
rules:
# Monitoring permissions within namespace
- apiGroups: [""]
  resources: ["pods", "events"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "statefulsets"]
  verbs: ["get", "list", "watch"]
# Control permissions within namespace
- apiGroups: ["apps"]
  resources: ["deployments", "deployments/scale", "statefulsets", "statefulsets/scale"]
  verbs: ["patch", "update", "get"]
- apiGroups: ["apps"]
  resources: ["statefulsets/status"]
  verbs: ["get", "patch", "update"]
# Batch API permissions for CronJobs within namespace
- apiGroups: ["batch"]
  resources: ["cronjobs", "jobs"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["batch"]
  resources: ["cronjobs", "cronjobs/status", "jobs"]
  verbs: ["get", "patch", "update", "create"]
```

### 3. Create RoleBinding (instead of ClusterRoleBinding)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: homeassistant-kubernetes-integration
  namespace: your-target-namespace
subjects:
- kind: ServiceAccount
  name: homeassistant-kubernetes-integration
  namespace: your-target-namespace
roleRef:
  kind: Role
  name: homeassistant-kubernetes-integration
  apiGroup: rbac.authorization.k8s.io
```

### 4. Create Token Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: homeassistant-kubernetes-integration-token
  namespace: your-target-namespace
  annotations:
    kubernetes.io/service-account.name: homeassistant-kubernetes-integration
type: kubernetes.io/service-account-token
```

### Limitations of Namespace-Specific Setup

- **No cluster-wide metrics**: Cannot see total nodes count or cluster health
- **No cross-namespace monitoring**: Cannot monitor multiple namespaces simultaneously
- **Limited visibility**: Reduced overall cluster insight
- **Still need namespace permissions**: To list namespaces, you'll need at least cluster-level `get` and `list` on `namespaces`

### Hybrid Approach: Namespace-Scoped with Minimal Cluster Permissions

For a balanced approach, use namespace-scoped roles with minimal cluster permissions:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: homeassistant-kubernetes-integration-minimal
rules:
# Minimal cluster-wide permissions for basic functionality
- apiGroups: [""]
  resources: ["nodes", "namespaces"]
  verbs: ["get", "list"]
- apiGroups: ["batch"]
  resources: ["cronjobs"]
  verbs: ["get", "list"]
```

Then combine with namespace-specific roles for actual workload control.

## Security Considerations

### Token Security

- Store the service account token securely in Home Assistant
- Regularly rotate service account tokens
- Use Kubernetes secrets for token storage

### Minimal Permissions

- The provided RBAC permissions follow the principle of least privilege
- Only `patch` permission is granted for scaling operations
- No `delete` or `create` permissions are included

### Network Security

- Ensure Home Assistant can reach the Kubernetes API server
- Consider using a VPN or private network for API access
- Verify SSL certificates are properly configured

## Troubleshooting

### Common Issues

1. **Token Extraction Fails**

   ```bash
   # Check if the secret exists
   kubectl get secret homeassistant-kubernetes-integration-token -n homeassistant

   # If not found, ensure the service account was created
   kubectl get serviceaccount homeassistant-kubernetes-integration -n homeassistant
   ```

2. **Permission Denied Errors**

   ```bash
   # Check the cluster role binding
   kubectl get clusterrolebinding homeassistant-kubernetes-integration

   # Verify the role permissions
   kubectl describe clusterrole homeassistant-kubernetes-integration
   ```

3. **Namespace Access Issues**

   ```bash
   # Test API access with the token
   kubectl auth can-i get pods --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration
   ```

### Verification Commands

Test your setup with these commands:

```bash
# Test basic connectivity
kubectl auth can-i get nodes --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Test deployment access
kubectl auth can-i get deployments --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Test scaling permissions
kubectl auth can-i patch deployments/scale --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Test statefulset scaling
kubectl auth can-i patch statefulsets/scale --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Test watch permissions (important for real-time updates)
kubectl auth can-i watch pods --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration
```

## Additional Resources

- **[RBAC Reference Guide](RBAC.md)** - Comprehensive RBAC permissions documentation and security scenarios
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions
