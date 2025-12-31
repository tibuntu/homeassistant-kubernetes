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

### Individual Node Sensors

The integration creates a separate sensor for each Kubernetes node in the cluster:

| Sensor | Description | Example Value | Unit |
|--------|-------------|---------------|------|
| **Node [node-name]** | Individual node status and information | `Ready` / `NotReady` / `Unknown` | - |

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

## Entity Naming

Entities are automatically named using the following patterns:

- **Sensors**: `sensor.kubernetes_[cluster_name]_[metric_type]`
- **Binary Sensors**: `binary_sensor.kubernetes_[cluster_name]_cluster_health`
- **Switches**: `switch.kubernetes_[cluster_name]_[resource_type]_[resource_name]`
- **Pod Sensors**: `sensor.kubernetes_[cluster_name]_[pod_name]`

## Dynamic Entity Discovery

The integration automatically discovers and creates entities for:

- All deployments in monitored namespaces
- All statefulsets in monitored namespaces
- All daemonsets in monitored namespaces
- All cronjobs in monitored namespaces
- Individual Kubernetes pods in monitored namespaces
- Individual Kubernetes nodes in the cluster
- Cluster-wide metrics (pods, nodes, deployments, statefulsets, daemonsets, cronjobs count)
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
