# Service Account Setup Guide

This guide walks you through setting up the required Kubernetes service account and RBAC permissions for the Home Assistant Kubernetes Integration.

## Picking the right path

| Where Home Assistant runs | Recommended setup |
|---------------------------|-------------------|
| **Inside the cluster** (HA itself runs as a pod) | [In-cluster ServiceAccount](#in-cluster-serviceaccount-setup) — bind the SA directly to the HA pod, skip the token-extraction step, get automatic token rotation. |
| **Outside the cluster** (HA on a different host) | [Quick Setup](#quick-setup) — install the RBAC, extract a token from the long-lived secret, paste it into the integration. |

Both paths grant the **same RBAC permissions**; only the way the integration receives the token differs.

You can install the RBAC either with the **Helm chart** (recommended — `helm upgrade` picks up new permissions as the integration gains features) or with the **plain manifests** in `manifests/`. Both are described below; see the [RBAC Reference Guide](RBAC.md) for the full permission matrix and the available chart values.

## In-Cluster ServiceAccount Setup

When Home Assistant runs as a pod in the same cluster it monitors, you do not need to extract the token manually. Instead, bind the integration's ServiceAccount to the HA pod and let the integration read the projected token file at runtime — rotation included.

### 1. Install the RBAC

With Helm — note `tokenSecret.create=false`, since the pod uses the projected (auto-rotating) token instead:

```bash
helm install ha-k8s-rbac oci://ghcr.io/tibuntu/charts/homeassistant-kubernetes-rbac \
  --namespace homeassistant --create-namespace \
  --set tokenSecret.create=false
```

> Migrating from the plain manifests? Add `--take-ownership` so Helm adopts the objects you already applied — see [Already applied the plain manifests?](RBAC.md#already-applied-the-plain-manifests)

Or with the plain manifests:

```bash
kubectl apply -f manifests/full/         # or manifests/minimal/
```

Either way you get the ServiceAccount, ClusterRole, and ClusterRoleBinding. The long-lived token `Secret` from the quick-setup path is **not needed** here — the projected token volume is mounted by the kubelet automatically.

### 2. Bind the SA to the Home Assistant pod

Set `serviceAccountName` on the HA pod (or Deployment / StatefulSet) to match the SA referenced in the binding:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: homeassistant
  namespace: homeassistant
spec:
  template:
    spec:
      serviceAccountName: homeassistant-kubernetes-integration
      # automountServiceAccountToken defaults to true. Leave it as-is so the
      # projected token volume is mounted at /var/run/secrets/kubernetes.io/serviceaccount.
      containers:
        - name: homeassistant
          image: ghcr.io/home-assistant/home-assistant:latest
```

### 3. Configure the integration

1. Go to **Settings → Devices & Services → Add Integration → Kubernetes**.
2. The **Host**, **Port**, **API Token**, and **CA Certificate** fields are pre-filled from the pod's ServiceAccount.
3. Leave **Prefer in-cluster ServiceAccount token** enabled (it defaults to on when in-cluster credentials are detected). The integration will re-read the projected token file on each request, so automatic token rotation is handled transparently. While it is enabled, the **API Token** field below it is only used as a fallback — uncheck it if you want to authenticate with a token you paste in.
4. Pick a friendly **Cluster Name** and submit.

> **Tip:** The same checkbox is available in **Configure → Reconfigure** for existing entries, so you can switch between in-cluster and static-token modes without removing the integration.

## Quick Setup

### 1. Install the RBAC

With Helm:

```bash
helm install ha-k8s-rbac oci://ghcr.io/tibuntu/charts/homeassistant-kubernetes-rbac \
  --namespace homeassistant --create-namespace
```

Add `--set mode=minimal` for read-only sensors only. If you previously applied the plain manifests, add `--take-ownership` so Helm adopts the existing objects instead of failing on ownership metadata — see [Already applied the plain manifests?](RBAC.md#already-applied-the-plain-manifests) Later, after updating the integration:

```bash
helm upgrade ha-k8s-rbac oci://ghcr.io/tibuntu/charts/homeassistant-kubernetes-rbac \
  --namespace homeassistant --reset-then-reuse-values
```

Or with the plain manifests:

```bash
kubectl apply -f manifests/full/         # or manifests/minimal/
```

### 2. Extract the Token

```bash
kubectl get secret homeassistant-kubernetes-integration-token -n homeassistant -o jsonpath='{.data.token}' | base64 -d
```

Copy this token for use in the Home Assistant configuration.

> **Important:** If Home Assistant itself runs inside the cluster, the config form pre-checks **Prefer in-cluster ServiceAccount token**. Uncheck it when you want the integration to authenticate with the token extracted here — while it is checked, the pasted token is only used as a fallback and the pod's own ServiceAccount token wins.

> **Note:** Tokens extracted from a long-lived `kubernetes.io/service-account-token` secret do **not** rotate. If you want automatic rotation, run Home Assistant inside the cluster and use the [In-Cluster ServiceAccount Setup](#in-cluster-serviceaccount-setup) path instead.

## Step-by-Step Setup

If you prefer to understand each step or need to customize the setup, apply the four manifests individually (swap `full` for `minimal` for a read-only setup):

### 1. Create Service Account

```bash
kubectl apply -f manifests/full/serviceaccount.yaml
```

This creates a service account named `homeassistant-kubernetes-integration` in the `homeassistant` namespace.

### 2. Create Cluster Role

```bash
kubectl apply -f manifests/full/clusterrole.yaml
```

This defines the RBAC permissions required for monitoring and controlling Kubernetes resources.

### 3. Create Cluster Role Binding

```bash
kubectl apply -f manifests/full/clusterrolebinding.yaml
```

This binds the cluster role to the service account, granting the necessary permissions.

### 4. Create Token Secret

```bash
kubectl apply -f manifests/full/serviceaccount-token-secret.yaml
```

This creates a secret containing the service account token for authentication. Skip this step when Home Assistant runs inside the cluster.

### 5. Extract the Token

```bash
kubectl get secret homeassistant-kubernetes-integration-token -n homeassistant -o jsonpath='{.data.token}' | base64 -d
```

## RBAC Permissions

The authoritative permission list lives in the chart (`chart/templates/clusterrole.yaml`) and its rendered output (`manifests/full/clusterrole.yaml`, `manifests/minimal/clusterrole.yaml`).

For the complete matrix — every API group, resource, and verb, with the feature each one unlocks and a `full` vs `minimal` comparison — see the [RBAC Reference Guide](RBAC.md#complete-permission-matrix).

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
  resources: ["deployments", "replicasets", "statefulsets", "daemonsets"]
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
# Networking permissions within namespace
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses"]
  verbs: ["get", "list", "watch"]
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
