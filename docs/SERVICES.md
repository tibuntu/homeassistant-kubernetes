# Services Documentation

This document describes all services provided by the Kubernetes integration for programmatic control of your cluster.

## Available Services

The integration provides the following generic services that work with multiple workload types:

| Service | Description | Supported Workloads |
|---------|-------------|---------------------|
| **Scale Workload** | Scale a workload to a specific number of replicas | Deployments, StatefulSets |
| **Start Workload** | Start a workload by scaling to specified replicas, or trigger CronJobs | Deployments, StatefulSets, CronJobs |
| **Stop Workload** | Stop a workload by scaling to 0 replicas | Deployments, StatefulSets |

> **Note**: CronJobs are not affected by `scale_workload` or `stop_workload`. Use the switch entity to suspend/resume CronJobs, or use `start_workload` to trigger them.

## Service Details

### Scale Workload

**Service**: `kubernetes.scale_workload`

Scale one or more Kubernetes workloads (Deployments or StatefulSets) to a specific number of replicas.

**Parameters**:

- `workload_name` (string or entity ID, optional): Single workload name or entity ID (e.g., `switch.my_deployment`)
- `workload_names` (list or target selector, optional): Multiple workload names or entity IDs
- `namespace` (string, optional): Kubernetes namespace (defaults to configured namespace)
- `replicas` (integer, required): Target number of replicas (0 or more)

**Supported Workloads**: Deployments, StatefulSets

**Note**: CronJobs are not supported. If a CronJob is provided, a warning will be logged and the operation will be skipped.

**Examples**:

```yaml
# Scale a single deployment using entity ID
service: kubernetes.scale_workload
data:
  workload_name: switch.web_app
  replicas: 3

# Scale multiple workloads
service: kubernetes.scale_workload
data:
  workload_names:
    - switch.web_app
    - switch.api_server
  replicas: 2
  namespace: production

# Scale using direct workload name
service: kubernetes.scale_workload
data:
  workload_name: web-app
  namespace: production
  replicas: 5
```

### Start Workload

**Service**: `kubernetes.start_workload`

Start one or more Kubernetes workloads by scaling them to the specified number of replicas, or trigger CronJobs (creates a job immediately).

**Parameters**:

- `workload_name` (string or entity ID, optional): Single workload name or entity ID (e.g., `switch.my_deployment`)
- `workload_names` (list or target selector, optional): Multiple workload names or entity IDs
- `namespace` (string, optional): Kubernetes namespace (defaults to configured namespace)
- `replicas` (integer, optional): Number of replicas for Deployments/StatefulSets (default: 1, ignored for CronJobs)

**Supported Workloads**:
- **Deployments**: Scales to the specified number of replicas
- **StatefulSets**: Scales to the specified number of replicas
- **CronJobs**: Triggers the CronJob immediately (creates a job from the CronJob template)

**Examples**:

```yaml
# Start a deployment with 2 replicas
service: kubernetes.start_workload
data:
  workload_name: switch.web_app
  replicas: 2

# Trigger a CronJob
service: kubernetes.start_workload
data:
  workload_name: switch.backup_job
  # replicas parameter is ignored for CronJobs

# Start multiple StatefulSets
service: kubernetes.start_workload
data:
  workload_names:
    - switch.database_primary
    - switch.database_replica
  replicas: 1
  namespace: database
```

### Stop Workload

**Service**: `kubernetes.stop_workload`

Stop one or more Kubernetes workloads by scaling them to 0 replicas (Deployments/StatefulSets only).

**Parameters**:

- `workload_name` (string or entity ID, optional): Single workload name or entity ID (e.g., `switch.my_deployment`)
- `workload_names` (list or target selector, optional): Multiple workload names or entity IDs
- `namespace` (string, optional): Kubernetes namespace (defaults to configured namespace)

**Supported Workloads**: Deployments, StatefulSets

**Note**: CronJobs are not affected by this service. To suspend a CronJob, use the switch entity (`switch.turn_off` on the CronJob switch).

**Examples**:

```yaml
# Stop a single deployment
service: kubernetes.stop_workload
data:
  workload_name: switch.web_app

# Stop multiple workloads
service: kubernetes.stop_workload
data:
  workload_names:
    - switch.development_api
    - switch.staging_api
  namespace: development
```

## Using Entity IDs vs. Workload Names

The services accept both entity IDs and direct workload names:

**Entity IDs** (recommended for UI usage):
```yaml
workload_name: switch.web_app
# or
workload_names:
  - switch.web_app
  - switch.api_server
```

**Direct Names** (for programmatic usage):
```yaml
workload_name: web-app
# or
workload_names:
  - web-app
  - api-server
```

When using entity IDs, the service automatically extracts the workload name, namespace, and workload type from the entity attributes.

## Service Behavior

### Error Handling

- Services validate that the target namespace exists
- Services check that the specified workloads exist
- Failed operations return detailed error messages
- Partial failures are reported for multi-resource operations
- CronJobs provided to `scale_workload` or `stop_workload` are ignored with a warning

### Asynchronous Operations

- All scaling operations are asynchronous
- Services return immediately after initiating the scaling operation
- Use the entity states to monitor the actual scaling progress
- Configure `scale_verification_timeout` to adjust how long to wait for operations

### Workload Type Detection

The services automatically detect the workload type from entity attributes:
- If an entity ID is provided (e.g., `switch.web_app`), the service reads the `workload_type` attribute
- If a direct name is provided, the service attempts to determine the type from the entity registry
- CronJobs are automatically handled differently (triggered instead of scaled)

### Permissions Required

Services require the following Kubernetes RBAC permissions:

**For Deployments and StatefulSets**:
- `apps/deployments`: `get`, `list`, `patch` (for scaling)
- `apps/statefulsets`: `get`, `list`, `patch` (for scaling)

**For CronJobs**:
- `batch/cronjobs`: `get`, `list`, `watch`, `patch`
- `batch/jobs`: `get`, `list`, `watch`, `create`

**General**:
- Access to the target namespaces

See the [Setup Guide](SETUP.md) and [RBAC Reference](RBAC.md) for detailed RBAC configuration.

## CronJob Management

For CronJobs, the services work as follows:

- **`start_workload`**: Triggers the CronJob immediately (creates a job from the CronJob template)
- **`scale_workload`**: Not supported (warning logged, operation skipped)
- **`stop_workload`**: Not supported (warning logged, operation skipped)

To suspend or resume CronJobs, use the switch entities:
- Turn the switch **ON** to resume (unsuspend) a CronJob
- Turn the switch **OFF** to suspend a CronJob

For more information about CronJob management, see the [CronJobs Documentation](CRONJOBS.md).

## Examples

### Scale Multiple Deployments

```yaml
automation:
  - alias: "Scale Down During Off Hours"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      service: kubernetes.scale_workload
      data:
        workload_names:
          - switch.web_app
          - switch.api_server
        replicas: 1
        namespace: production
```

### Start Workloads on Schedule

```yaml
automation:
  - alias: "Start Services in Morning"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      service: kubernetes.start_workload
      data:
        workload_names:
          - switch.web_app
          - switch.database
        replicas: 3
```

### Trigger CronJob Manually

```yaml
automation:
  - alias: "Manual Backup Trigger"
    trigger:
      - platform: event
        event_type: manual_backup_requested
    action:
      service: kubernetes.start_workload
      data:
        workload_name: switch.backup_job
        namespace: production
```

### Stop All Workloads in Namespace

```yaml
script:
  stop_all_workloads:
    sequence:
      - service: kubernetes.stop_workload
        data:
          workload_names:
            - switch.app1
            - switch.app2
            - switch.app3
          namespace: staging
```
