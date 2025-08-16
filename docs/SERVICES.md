# Services Documentation

This document describes all services provided by the Kubernetes integration for programmatic control of your cluster.

## Available Services

The integration provides the following services:

| Service | Description | Target |
|---------|-------------|---------|
| **Scale Deployment** | Scale a deployment to a specific number of replicas | Deployments |
| **Stop Deployment** | Scale a deployment to 0 replicas (stop it) | Deployments |
| **Start Deployment** | Scale a deployment to 1 or more replicas (start it) | Deployments |
| **Scale StatefulSet** | Scale a statefulset to a specific number of replicas | StatefulSets |
| **Stop StatefulSet** | Scale a statefulset to 0 replicas (stop it) | StatefulSets |
| **Start StatefulSet** | Scale a statefulset to 1 or more replicas (start it) | StatefulSets |

## Service Details

### Scale Deployment

**Service**: `kubernetes.scale_deployment`

Scale one or more deployments to a specific number of replicas.

**Parameters**:
- `deployment_name` (string, optional): Single deployment name
- `deployment_names` (list, optional): Multiple deployment names
- `namespace` (string, required): Kubernetes namespace
- `replicas` (integer, required): Target number of replicas

**Example**:
```yaml
service: kubernetes.scale_deployment
data:
  deployment_name: "web-app"
  namespace: "production"
  replicas: 3
```

**Multiple deployments**:
```yaml
service: kubernetes.scale_deployment
data:
  deployment_names:
    - "web-app"
    - "api-server"
  namespace: "production"
  replicas: 2
```

### Stop Deployment

**Service**: `kubernetes.stop_deployment`

Scale one or more deployments to 0 replicas (effectively stopping them).

**Parameters**:
- `deployment_name` (string, optional): Single deployment name
- `deployment_names` (list, optional): Multiple deployment names
- `namespace` (string, required): Kubernetes namespace

**Example**:
```yaml
service: kubernetes.stop_deployment
data:
  deployment_names:
    - "development-api"
    - "staging-api"
  namespace: "development"
```

### Start Deployment

**Service**: `kubernetes.start_deployment`

Scale one or more deployments to 1 or more replicas (starting them).

**Parameters**:
- `deployment_name` (string, optional): Single deployment name
- `deployment_names` (list, optional): Multiple deployment names
- `namespace` (string, required): Kubernetes namespace
- `replicas` (integer, optional): Number of replicas (default: 1)

**Example**:
```yaml
service: kubernetes.start_deployment
data:
  deployment_name: "web-app"
  namespace: "production"
  replicas: 2
```

### Scale StatefulSet

**Service**: `kubernetes.scale_statefulset`

Scale one or more statefulsets to a specific number of replicas.

**Parameters**:
- `statefulset_name` (string, optional): Single statefulset name
- `statefulset_names` (list, optional): Multiple statefulset names
- `namespace` (string, required): Kubernetes namespace
- `replicas` (integer, required): Target number of replicas

**Example**:
```yaml
service: kubernetes.scale_statefulset
data:
  statefulset_names:
    - "database-primary"
    - "database-replica"
  namespace: "database"
  replicas: 1
```

### Stop StatefulSet

**Service**: `kubernetes.stop_statefulset`

Scale one or more statefulsets to 0 replicas.

**Parameters**:
- `statefulset_name` (string, optional): Single statefulset name
- `statefulset_names` (list, optional): Multiple statefulset names
- `namespace` (string, required): Kubernetes namespace

### Start StatefulSet

**Service**: `kubernetes.start_statefulset`

Scale one or more statefulsets to 1 or more replicas.

**Parameters**:
- `statefulset_name` (string, optional): Single statefulset name
- `statefulset_names` (list, optional): Multiple statefulset names
- `namespace` (string, required): Kubernetes namespace
- `replicas` (integer, optional): Number of replicas (default: 1)

## Service Behavior

### Error Handling

- Services validate that the target namespace exists
- Services check that the specified deployments/statefulsets exist
- Failed operations return detailed error messages
- Partial failures are reported for multi-resource operations

### Asynchronous Operations

- All scaling operations are asynchronous
- Services return immediately after initiating the scaling operation
- Use the entity states to monitor the actual scaling progress
- Configure `scale_verification_timeout` to adjust how long to wait for operations

### Permissions Required

Services require the following Kubernetes RBAC permissions:

- `deployments`: `get`, `list`, `patch` (for scaling)
- `statefulsets`: `get`, `list`, `patch` (for scaling)
- Access to the target namespaces

See the [Setup Guide](SETUP.md) for detailed RBAC configuration.
