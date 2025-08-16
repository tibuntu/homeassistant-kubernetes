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

## Entity Naming

Entities are automatically named using the following patterns:

- **Sensors**: `sensor.kubernetes_[cluster_name]_[metric_type]`
- **Binary Sensors**: `binary_sensor.kubernetes_[cluster_name]_cluster_health`
- **Switches**: `switch.kubernetes_[cluster_name]_[resource_type]_[resource_name]`

## Dynamic Entity Discovery

The integration automatically discovers and creates entities for:

- All deployments in monitored namespaces
- All statefulsets in monitored namespaces
- Cluster-wide metrics (nodes, overall health)

Entities are automatically added when new resources are created and removed when resources are deleted from the cluster.
