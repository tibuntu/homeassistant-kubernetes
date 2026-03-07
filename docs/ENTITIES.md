# Entities Documentation

This document describes all sensors, binary sensors, and switches provided by the Kubernetes integration.

## Sensors

The integration provides the following sensors to monitor your Kubernetes cluster:

| Sensor | Description | Example Value | Unit |
|--------|-------------|---------------|------|
| **Pods Count** | Number of pods in the monitored namespace(s) | `15` | pods |
| **Nodes Count** | Number of nodes in the cluster | `3` | nodes |
| **Deployments Count** | Number of deployments in the monitored namespace(s) | `8` | deployments |
| **StatefulSets Count** | Number of statefulsets in the monitored namespace(s) | `2` | statefulsets |
| **DaemonSets Count** | Number of daemonsets in the monitored namespace(s) | `3` | daemonsets |
| **CronJobs Count** | Number of cronjobs in the monitored namespace(s) | `5` | cronjobs |
| **Jobs Count** | Number of jobs in the monitored namespace(s) | `3` | jobs |

### Individual Node Sensors

The integration creates a separate sensor for each Kubernetes node in the cluster:

| Sensor | Description | Example Value | Unit |
|--------|-------------|---------------|------|
| **Node [node-name]** | Individual node status and information | `Ready` / `NotReady` / `Unknown` | - |

### Individual DaemonSet Sensors

The integration creates a separate sensor for each Kubernetes DaemonSet in the monitored namespace(s):

| Sensor | Description | Example Value |
|--------|-------------|---------------|
| **[daemonset-name]** | Individual DaemonSet readiness status | `Ready` / `Degraded` / `Not Ready` / `Unknown` |

#### DaemonSet Sensor Attributes

Each DaemonSet sensor provides scheduling and readiness information:

| Attribute | Description | Example Value |
|-----------|-------------|---------------|
| **namespace** | Kubernetes namespace of the DaemonSet | `kube-system` |
| **desired** | Number of nodes that should run the DaemonSet pod | `3` |
| **current** | Number of nodes currently running the DaemonSet pod | `3` |
| **ready** | Number of nodes where the pod is ready | `3` |
| **available** | Number of nodes where the pod is available | `3` |

Status values:
- `Ready` — all desired pods are ready (`ready == desired`)
- `Degraded` — some but not all pods are ready (`0 < ready < desired`)
- `Not Ready` — no pods are ready (`ready == 0`)
- `Unknown` — data is unavailable or no nodes are scheduled

### Workload Status Sensors

The integration creates a readiness status sensor for each deployment and statefulset:

| Sensor | Description | Example Value |
|--------|-------------|---------------|
| **[workload-name]** | Readiness status of the workload | `Ready` / `Degraded` / `Not Ready` / `Scaled Down` / `Unknown` |

Status values:
- `Ready` — all desired replicas are ready (`ready_replicas == replicas > 0`)
- `Degraded` — some but not all replicas are ready (`0 < ready_replicas < replicas`)
- `Not Ready` — no replicas are ready (`ready_replicas == 0` and `replicas > 0`)
- `Scaled Down` — workload is intentionally scaled to zero (`replicas == 0`)
- `Unknown` — data is unavailable

Each sensor exposes the following attributes: `namespace`, `replicas`, `ready_replicas`, `available_replicas`.

### Workload Metric Sensors

The integration creates CPU and memory usage sensors for each deployment and statefulset. These sensors read live data from the [metrics-server](https://github.com/kubernetes-sigs/metrics-server) and require it to be installed in your cluster.

| Sensor | Description | Example Value | Unit |
|--------|-------------|---------------|------|
| **[workload-name] CPU Usage** | Aggregated CPU usage across all pods of the workload | `142` | m (millicores) |
| **[workload-name] Memory Usage** | Aggregated memory usage across all pods of the workload | `256` | MiB |

These sensors expose numeric values with `SensorStateClass.MEASUREMENT`, making them suitable for history tracking and use in automations:

```yaml
# Scale up a deployment when CPU usage exceeds 800 millicores
trigger:
  - platform: numeric_state
    entity_id: sensor.my_app_cpu_usage
    above: 800
action:
  - service: kubernetes.scale_workload
    data:
      workload_name: my-app
      namespace: default
      replicas: 3
```

> **Note:** If metrics-server is not installed, these sensors will report `0`.

### Individual Pod Sensors

The integration creates a separate sensor for each Kubernetes pod in the monitored namespace(s):

| Sensor | Description | Example Value | Unit |
|--------|-------------|---------------|------|
| **Pod [pod-name]** | Individual pod phase and information | `Running` / `Pending` / `Failed` / `Succeeded` / `Unknown` | - |

#### Node Sensor Attributes

Each node sensor provides comprehensive information about the node:

| Attribute | Description | Example Value |
|-----------|-------------|---------------|
| **internal_ip** | Internal IP address of the node | `10.0.0.1` |
| **external_ip** | External IP address of the node | `203.0.113.1` |
| **memory_capacity_gb** | Total memory capacity in GB | `16.0` |
| **memory_allocatable_gb** | Allocatable memory in GB | `14.5` |
| **cpu_cores** | Number of CPU cores | `4.0` |
| **os_image** | Operating system image | `Ubuntu 22.04.3 LTS` |
| **kernel_version** | Kernel version | `5.15.0-56-generic` |
| **container_runtime** | Container runtime version | `containerd://1.6.6` |
| **kubelet_version** | Kubelet version | `v1.25.4` |
| **cpu_usage_millicores** | Real-time CPU usage (requires metrics-server) | `410.0` |
| **memory_usage_mib** | Real-time memory usage in MiB (requires metrics-server) | `2015.0` |
| **schedulable** | Whether the node can schedule new pods | `true` / `false` |
| **creation_timestamp** | When the node was created | `2023-01-01T00:00:00Z` |

#### Pod Sensor Attributes

Each pod sensor provides comprehensive information about the pod:

| Attribute | Description | Example Value |
|-----------|-------------|---------------|
| **namespace** | Kubernetes namespace where the pod is located | `default` |
| **phase** | Current phase of the pod (useful for filtering with auto-entities) | `Running` / `Pending` / `Failed` / `Succeeded` / `Unknown` |
| **ready_containers** | Number of ready containers in the pod | `2` |
| **total_containers** | Total number of containers in the pod | `2` |
| **restart_count** | Total number of container restarts | `0` |
| **node_name** | Name of the node where the pod is running | `worker-node-1` |
| **pod_ip** | IP address of the pod | `10.244.1.5` |
| **creation_timestamp** | When the pod was created | `2023-01-01T00:00:00Z` |
| **owner_kind** | Type of resource that owns this pod | `ReplicaSet` |
| **owner_name** | Name of the resource that owns this pod | `my-app-7d4b8c9f6b` |

### Individual Job Sensors

The integration creates a separate sensor for each Kubernetes Job in the monitored namespace(s):

| Sensor | Description | Example Value |
|--------|-------------|---------------|
| **[job-name]** | Individual Job status | `Complete` / `Running` / `Failed` / `Unknown` |

Status values:
- `Complete` — all completions have succeeded (`succeeded >= completions`)
- `Running` — the job has active pods (`active > 0`)
- `Failed` — the job has failed pods and no active ones
- `Unknown` — data is unavailable

#### Job Sensor Attributes

Each Job sensor provides execution details:

| Attribute | Description | Example Value |
|-----------|-------------|---------------|
| **namespace** | Kubernetes namespace of the Job | `default` |
| **completions** | Number of completions required | `1` |
| **succeeded** | Number of successfully completed pods | `1` |
| **failed** | Number of failed pods | `0` |
| **active** | Number of currently active pods | `0` |
| **start_time** | When the Job started | `2025-01-01T00:00:00Z` |
| **completion_time** | When the Job completed | `2025-01-01T00:05:00Z` |

### Sensor Attributes

Each sensor includes additional attributes with detailed information:

- **Last Updated**: Timestamp of the last successful update
- **Namespace**: The namespace being monitored
- **Cluster Name**: Name of the Kubernetes cluster
- **API Endpoint**: Kubernetes API server endpoint

## Binary Sensors

| Binary Sensor | Description | States |
|---------------|-------------|--------|
| **Cluster Health** | Indicates if the cluster is reachable and responding | `on` (healthy) / `off` (unhealthy) |

### Node Condition Binary Sensors

The integration creates binary sensors for each node condition on every node in the cluster:

| Binary Sensor | Description | Device Class |
|---------------|-------------|--------------|
| **[node-name] Memory Pressure** | Node is running low on memory | `problem` |
| **[node-name] Disk Pressure** | Node is running low on disk space | `problem` |
| **[node-name] PID Pressure** | Node is running too many processes | `problem` |
| **[node-name] Network Unavailable** | Node network is not correctly configured | `problem` |

- **States**: `on` means the condition is active (problem detected), `off` means normal operation
- **Device assignment**: Assigned to the cluster device alongside individual node sensors

### Binary Sensor Attributes

- **Last Check**: Timestamp of the last health check
- **Error Message**: Details about connection issues (when unhealthy)
- **Response Time**: API response time in milliseconds

## Switches

The integration automatically creates switches for controlling Kubernetes workloads:

### Deployment Switches

- **Entity ID Format**: `switch.kubernetes_deployment_[deployment_name]`
- **Function**: Control individual deployments (scale to 0/1 replicas)
- **States**:
  - `on`: Deployment is running (replicas > 0)
  - `off`: Deployment is stopped (replicas = 0)

### StatefulSet Switches

- **Entity ID Format**: `switch.kubernetes_statefulset_[statefulset_name]`
- **Function**: Control individual statefulsets (scale to 0/1 replicas)
- **States**:
  - `on`: StatefulSet is running (replicas > 0)
  - `off`: StatefulSet is stopped (replicas = 0)

### Switch Features

- **Real-time State**: Switches automatically reflect the actual Kubernetes state through polling
- **Error Recovery**: If scaling operations fail, switches automatically recover the correct state
- **State Verification**: Verifies that scaling operations actually took effect
- **Configurable Polling**: Adjust update intervals to balance responsiveness and API load
- **Failure Indication**: Shows when the last scaling attempt failed via entity attributes

### Switch Attributes

Each switch includes detailed attributes:

- **Current Replicas**: Current number of replicas
- **Desired Replicas**: Target number of replicas
- **Ready Replicas**: Number of ready replicas
- **Last Scaled**: Timestamp of the last scaling operation
- **Scale Status**: Success/failure status of the last scaling operation
- **Namespace**: Kubernetes namespace
- **Resource Type**: `deployment` or `statefulset`
- **CPU Usage**: CPU usage in millicores (for Deployments and StatefulSets)
- **Memory Usage**: Memory usage in MiB (for Deployments and StatefulSets)

## Device Organization

The integration organizes entities using Home Assistant's device system, creating a hierarchical structure that makes it easier to manage large clusters:

### Device Hierarchy

```
Cluster Device (e.g., "production-cluster")
├── Cluster-level entities:
│   ├── Cluster Health (binary_sensor)
│   ├── Nodes Count (sensor)
│   ├── Pods Count (sensor)
│   ├── Deployments Count (sensor)
│   ├── StatefulSets Count (sensor)
│   ├── DaemonSets Count (sensor)
│   ├── CronJobs Count (sensor)
│   ├── Jobs Count (sensor)
│   ├── Individual Node sensors (one per node)
│   └── Node condition binary sensors (4 per node: Memory/Disk/PID Pressure, Network Unavailable)
│
└── Namespace Devices (e.g., "production-cluster: default")
    ├── Pod sensors (all pods in this namespace)
    ├── Deployment switches (all deployments in this namespace)
    ├── Deployment status sensors (one per deployment)
    ├── Deployment CPU/memory sensors (one pair per deployment)
    ├── StatefulSet switches (all statefulsets in this namespace)
    ├── StatefulSet status sensors (one per statefulset)
    ├── StatefulSet CPU/memory sensors (one pair per statefulset)
    ├── DaemonSet sensors (all daemonsets in this namespace)
    ├── CronJob switches (all cronjobs in this namespace)
    └── Job sensors (all jobs in this namespace)
```

### Benefits of Device Organization

- **Better Organization**: Entities are logically grouped by cluster and namespace
- **Easier Filtering**: Filter entities by device in the Home Assistant UI
- **Clearer Context**: Entity names clearly indicate which cluster and namespace they belong to
- **Scalability**: Better handles large clusters with many resources
- **Kubernetes Alignment**: Follows Kubernetes namespace organization pattern

### Device Management

- **Automatic Device Creation**: Devices are automatically created when entities are first discovered
- **Automatic Device Cleanup**: Namespace devices are automatically removed when namespaces are deleted from the cluster
- **Dynamic Updates**: New namespace devices are created when new namespaces are discovered

## Entity Naming

With device-based grouping, entities are automatically named using the following patterns:

- **Cluster-level Sensors**: `sensor.[cluster_name]_[metric_type]` (e.g., `sensor.production_cluster_nodes_count`)
- **Cluster-level Binary Sensors**: `binary_sensor.[cluster_name]_cluster_health` (e.g., `binary_sensor.production_cluster_cluster_health`)
- **Node Sensors**: `sensor.[cluster_name]_[node_name]` (e.g., `sensor.production_cluster_worker_node_1`)
- **Namespace-level Pod Sensors**: `sensor.[cluster_name]_[namespace]_[pod_name]` (e.g., `sensor.production_cluster_default_my_app_pod`)
- **Namespace-level Switches**: `switch.[cluster_name]_[namespace]_[resource_name]_[resource_type]` (e.g., `switch.production_cluster_default_my_deployment_deployment`)

The device hierarchy ensures that entity names include cluster and namespace context, making it clear what each entity represents.

## Dynamic Entity Discovery

The integration automatically discovers and creates entities for:

- All deployments in monitored namespaces (switch + status sensor + CPU/memory sensors)
- All statefulsets in monitored namespaces (switch + status sensor + CPU/memory sensors)
- All daemonsets in monitored namespaces (status sensor)
- All cronjobs in monitored namespaces (switch)
- All jobs in monitored namespaces (status sensor)
- Individual Kubernetes pods in monitored namespaces
- Individual Kubernetes nodes in the cluster
- Node condition binary sensors (4 per node: Memory Pressure, Disk Pressure, PID Pressure, Network Unavailable)
- Cluster-wide metrics (pods, nodes, deployments, statefulsets, daemonsets, cronjobs, jobs count)
- Overall cluster health

Entities are automatically added when new resources are created and removed when resources are deleted from the cluster.

### Node Entity Management

- **Automatic Creation**: Node sensors are automatically created for each node discovered during integration setup
- **Dynamic Updates**: Node information is refreshed during regular coordinator updates
- **Automatic Cleanup**: Node sensors are automatically removed when nodes are deleted from the cluster
- **Entity Naming**: Node entities use the format `sensor.kubernetes_node_[node_name]`

### Pod Entity Management

- **Automatic Creation**: Pod sensors are automatically created for each pod discovered during integration setup
- **Dynamic Updates**: Pod information is refreshed during regular coordinator updates
- **Automatic Cleanup**: Pod sensors are automatically removed when pods are deleted from the cluster
- **Entity Naming**: Pod entities use the format `sensor.kubernetes_[pod_name]`
- **Namespace Support**: Pods are tracked by both namespace and name for proper identification
- **Phase Tracking**: Pod sensors show the current phase (Running, Pending, Failed, Succeeded, etc.)
- **Container Status**: Detailed information about container readiness and restart counts
- **Owner Information**: Shows which workload (Deployment, StatefulSet, etc.) owns the pod

## Using Pod Entities with Auto-Entities

The pod entities are perfect for use with the [auto-entities](https://github.com/thomasloven/lovelace-auto-entities) card to create dynamic dashboards. Here's an example configuration to show pods that are not in a Running or Completed phase:

```yaml
type: custom:auto-entities
card:
  type: entities
  title: "Pods with Issues"
filter:
  include:
    - entity_id: sensor.kubernetes_*
      state:
        - "Pending"
        - "Failed"
        - "Unknown"
  exclude:
    - state: "Running"
    - state: "Succeeded"
```

This configuration will automatically populate a card with all pod entities that are in a problematic state, making it easy to monitor and troubleshoot your Kubernetes cluster.
