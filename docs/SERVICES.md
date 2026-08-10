# Services Documentation

This document describes all services provided by the Kubernetes integration for programmatic control of your cluster.

## Available Services

The integration provides the following services for controlling Kubernetes resources:

| Service | Description | Supported Resources |
|---------|-------------|---------------------|
| **Scale Workload** | Scale a workload to a specific number of replicas | Deployments, StatefulSets |
| **Start Workload** | Start a workload by scaling to specified replicas, or trigger CronJobs | Deployments, StatefulSets, CronJobs |
| **Stop Workload** | Stop a workload by scaling to 0 replicas | Deployments, StatefulSets |
| **Restart Workload** | Perform a rolling restart (equivalent to `kubectl rollout restart`) | Deployments, StatefulSets, DaemonSets |
| **Delete Job** | Delete one or more Jobs (useful for clearing failed Jobs) | Jobs |
| **Cordon Node** | Mark one or more nodes unschedulable (`kubectl cordon`) | Nodes |
| **Uncordon Node** | Mark one or more nodes schedulable again (`kubectl uncordon`) | Nodes |

> **Note**: CronJobs are rejected by `scale_workload` and `stop_workload`. Use the switch entity to suspend/resume CronJobs, or use `start_workload` to trigger them.

All services are registered when Home Assistant starts, before any cluster is configured, and stay registered for the lifetime of Home Assistant. See [Error Handling](#error-handling) for what happens when a call is invalid or an operation fails.

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

**Note**: CronJobs are not supported. If a CronJob is provided, the call fails with a validation error and no workload is scaled.

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

**Note**: CronJobs are rejected by this service with a validation error. To suspend a CronJob, use the switch entity (`switch.turn_off` on the CronJob switch).

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

### Restart Workload

**Service**: `kubernetes.restart_workload`

Perform a rolling restart of one or more Kubernetes workloads. This is equivalent to `kubectl rollout restart` — it patches `spec.template.metadata.annotations` with a `kubectl.kubernetes.io/restartedAt` timestamp, causing the controller to gradually recreate all pods.

**Parameters**:

- `workload_name` (string or entity ID, optional): Single workload name or entity ID (e.g., `switch.my_deployment`)
- `workload_names` (list or target selector, optional): Multiple workload names or entity IDs
- `namespace` (string, optional): Kubernetes namespace (defaults to configured namespace)

**Supported Workloads**: Deployments, StatefulSets, DaemonSets

**Note**: CronJobs and Jobs are not supported. If an unsupported workload type is provided, the call fails with a validation error and no workload is restarted.

**Examples**:

```yaml
# Restart a single deployment
service: kubernetes.restart_workload
data:
  workload_name: switch.web_app

# Restart multiple workloads
service: kubernetes.restart_workload
data:
  workload_names:
    - switch.web_app
    - switch.api_server
  namespace: production

# Restart using direct workload name
service: kubernetes.restart_workload
data:
  workload_name: web-app
  namespace: production
```

### Delete Job

**Service**: `kubernetes.delete_job`

Delete one or more Kubernetes Jobs. This is useful for removing failed Jobs or cleaning up completed Jobs. Deletes the Job and its pods using a Background propagation policy (pods are also deleted).

**Parameters**:

- `job_name` (string, optional): Single Job name
- `job_names` (list, optional): Multiple Job names
- `namespace` (string, optional): Kubernetes namespace (resolved from monitored data if Job exists, falls back to configured default)
- `entry_id` (string, optional): Config entry ID (defaults to the first configured entry if not specified)

**Supported Resources**: Jobs

**Note**: This service deletes Jobs by name (not entity IDs). At least one of `job_name` or `job_names` must be provided. The Job's pods are automatically deleted as part of the background propagation policy.

**Examples**:

```yaml
# Delete a single Job
service: kubernetes.delete_job
data:
  job_name: backup-job-abc123
  namespace: production

# Delete multiple Jobs
service: kubernetes.delete_job
data:
  job_names:
    - failed-job-1
    - failed-job-2
  namespace: production

# Delete using monitored data and default namespace
service: kubernetes.delete_job
data:
  job_name: backup-job-xyz789
```

### Cordon Node / Uncordon Node

**Services**: `kubernetes.cordon_node`, `kubernetes.uncordon_node`

Cordon marks a node unschedulable (the equivalent of `kubectl cordon`): running pods keep running, but no new pods are scheduled onto the node. Uncordon reverses it. The same operation is also available as a per-node switch entity (on = schedulable, off = cordoned).

**Parameters** (both services):

- `node_name` (string, optional): Single node name
- `node_names` (list, optional): Multiple node names
- `entry_id` (string, optional): Config entry ID (defaults to the first configured entry if not specified)

**Note**: Nodes are cluster-scoped — there is no `namespace` parameter. At least one of `node_name` or `node_names` must be provided. Requires the `patch` verb on `nodes` (included in `manifests/full/`).

**Examples**:

```yaml
# Cordon a node before maintenance
service: kubernetes.cordon_node
data:
  node_name: worker-node-1

# Uncordon several nodes after maintenance
service: kubernetes.uncordon_node
data:
  node_names:
    - worker-node-1
    - worker-node-2
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

Services raise errors instead of failing silently — Home Assistant shows them in the UI when a service is called from a dashboard or the Developer Tools, and logs them (together with the failing automation) otherwise.

**Invalid calls** raise a *validation* error before anything is changed in the cluster:

- No Kubernetes integration is configured, or the supplied `entry_id` does not match a loaded config entry
- None of the given `workload_name` / `workload_names` resolve to a known workload (e.g. the entity ID does not exist, or the switch has no `namespace`/`workload_type` attributes)
- `delete_job` / `cordon_node` / `uncordon_node` are called without a usable name
- A workload's type does not support the requested operation — for example scaling, stopping, or restarting a CronJob. The whole call is rejected; no target in the call is touched.

**Failed operations** raise a regular error *after* every target has been attempted:

- Multi-target calls do **not** abort at the first failure. Every workload, Job or node in the call is attempted, and a single error naming all failed targets (with the reason, where the API provided one) is raised at the end.
- Targets that succeeded stay changed — a partial failure is reported, not rolled back.
- Node cordon/uncordon still refreshes the coordinator when at least one node changed, even if others failed.

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
- `apps/deployments`: `get`, `list`, `patch` (for scaling and restart)
- `apps/statefulsets`: `get`, `list`, `patch` (for scaling and restart)

**For DaemonSets (restart only)**:
- `apps/daemonsets`: `get`, `list`, `patch`

**For CronJobs**:
- `batch/cronjobs`: `get`, `list`, `watch`, `patch`
- `batch/jobs`: `get`, `list`, `watch`, `create`

**General**:
- Access to the target namespaces

See the [Setup Guide](SETUP.md) and [RBAC Reference](RBAC.md) for detailed RBAC configuration.

## CronJob Management

For CronJobs, the services work as follows:

- **`start_workload`**: Triggers the CronJob immediately (creates a job from the CronJob template)
- **`scale_workload`**: Not supported (the call is rejected with a validation error)
- **`stop_workload`**: Not supported (the call is rejected with a validation error)

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

### Scheduled Rolling Restart

```yaml
automation:
  - alias: "Weekly rolling restart of production workloads"
    trigger:
      - platform: time
        at: "04:00:00"
    condition:
      condition: time
      weekday:
        - sun
    action:
      service: kubernetes.restart_workload
      data:
        workload_names:
          - switch.web_app
          - switch.api_server
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
