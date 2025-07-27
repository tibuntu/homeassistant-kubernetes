# Home Assistant Kubernetes Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Tibuntu&repository=homeassistant-kubernetes)

A comprehensive Home Assistant integration for monitoring and controlling Kubernetes clusters. Monitor your cluster's health, resource usage, and control deployments directly from Home Assistant.

## 📋 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Sensors](#-sensors)
- [Switches](#-switches)
- [Services](#-services)
- [Service Account Setup](#-service-account-setup)
- [Examples](#-examples)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

- **🔍 Cluster Monitoring**: Monitor pods, nodes, and deployments across your Kubernetes cluster
- **📁 Multi-Namespace Support**: Monitor a single namespace or all namespaces in your cluster
- **🎛️ Deployment Control**: Scale, start, and stop deployments directly from Home Assistant
- **🔄 Robust Connectivity**: Automatic fallback from kubernetes Python client to aiohttp for reliable API communication
- **⚡ Real-time Updates**: Get live updates on your cluster's health and resource usage
- **🛡️ Advanced State Management**: Intelligent polling and state recovery for reliable operation

## 📦 Installation

### HACS Installation (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Add this repository as a custom repository in HACS
3. Search for "Kubernetes" in the integrations section
4. Click "Download" and restart Home Assistant
5. Go to **Settings → Devices & Services** and add the Kubernetes integration

### Manual Installation

1. Download this repository
2. Copy the `custom_components/kubernetes` folder to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Go to **Settings → Devices & Services** and add the Kubernetes integration

## ⚙️ Configuration

### Required Settings

| Setting | Description | Example |
|---------|-------------|---------|
| **Name** | A friendly name for your cluster | `Production Cluster` |
| **Host** | Your Kubernetes API server host (IP address or hostname) | `192.168.1.100` |
| **API Token** | A valid Kubernetes service account token | `eyJhbGciOiJSUzI1NiIs...` |
| **Port** | Kubernetes API port | `6443` |

### Optional Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Cluster Name** | A name for your cluster | `default` |
| **Monitor All Namespaces** | Enable to monitor all namespaces | `false` |
| **Namespace** | The namespace to monitor | `default` |
| **CA Certificate** | Path to your cluster's CA certificate | `null` |
| **Verify SSL** | Whether to verify SSL certificates | `true` |
| **Switch Update Interval** | How often to poll for switch state updates (seconds) | `60` |
| **Scale Verification Timeout** | Maximum time to wait for scaling operations (seconds) | `30` |
| **Scale Cooldown** | Cooldown period after scaling operations (seconds) | `10` |

## 📊 Sensors

The integration provides the following sensors:

| Sensor | Description | Example Value |
|--------|-------------|---------------|
| **Pods Count** | Number of pods in the monitored namespace(s) | `15` |
| **Nodes Count** | Number of nodes in the cluster | `3` |
| **Deployments Count** | Number of deployments in the monitored namespace(s) | `8` |
| **StatefulSets Count** | Number of statefulsets in the monitored namespace(s) | `2` |
| **Cluster Health** | Binary sensor indicating if the cluster is reachable | `on`/`off` |

## 🎛️ Switches

The integration provides switches for controlling Kubernetes workloads:

- **Deployment Switches**: Control individual deployments (scale to 0/1 replicas)
- **StatefulSet Switches**: Control individual statefulsets (scale to 0/1 replicas)

### Switch Features

- **Real-time State**: Switches automatically reflect the actual Kubernetes state through polling
- **Error Recovery**: If scaling operations fail, switches automatically recover the correct state
- **State Verification**: Verifies that scaling operations actually took effect
- **Configurable Polling**: Adjust update intervals to balance responsiveness and API load
- **Failure Indication**: Shows when the last scaling attempt failed via entity attributes

## 🔧 Services

The integration provides the following services:

| Service | Description | Parameters |
|---------|-------------|------------|
| **Scale Deployment** | Scale a deployment to a specific number of replicas | `deployment_name`, `namespace`, `replicas` |
| **Stop Deployment** | Scale a deployment to 0 replicas (stop it) | `deployment_name`, `namespace` |
| **Start Deployment** | Scale a deployment to 1 or more replicas (start it) | `deployment_name`, `namespace`, `replicas` |

## 🔐 Service Account Setup

### Quick Setup

1. Apply the all-in-one manifest:
```bash
kubectl apply -f manifests/all-in-one.yaml
```

2. Extract the token:
```bash
kubectl get secret homeassistant-monitor-token -n default -o jsonpath='{.data.token}' | base64 -d
```

### Individual Resources Setup

Apply resources individually:
```bash
kubectl apply -f manifests/serviceaccount.yaml
kubectl apply -f manifests/clusterrole.yaml
kubectl apply -f manifests/clusterrolebinding.yaml
kubectl apply -f manifests/serviceaccount-token-secret.yaml
```

For detailed RBAC permissions and troubleshooting, see the [Troubleshooting Guide](docs/TROUBLESHOOTING.md).

## 📝 Examples

### Automation: Scale Down Non-Critical Deployments at Night

```yaml
automation:
  - alias: "Scale down non-critical deployments at night"
    trigger:
      platform: time
      at: "22:00:00"
    action:
      - service: kubernetes.scale_deployment
        data:
          deployment_name: "non-critical-app"
          namespace: "production"
          replicas: 0
```

### Automation: Scale Up Deployments in the Morning

```yaml
automation:
  - alias: "Scale up deployments in the morning"
    trigger:
      platform: time
      at: "07:00:00"
    action:
      - service: kubernetes.scale_deployment
        data:
          deployment_name: "web-app"
          namespace: "production"
          replicas: 3
```

### Dashboard: Cluster Overview

```yaml
views:
  - title: "Kubernetes Cluster"
    path: kubernetes
    cards:
      - type: entities
        title: "Cluster Status"
        entities:
          - entity: sensor.kubernetes_pods_count
          - entity: sensor.kubernetes_nodes_count
          - entity: sensor.kubernetes_services_count
          - entity: sensor.kubernetes_deployments_count
          - entity: binary_sensor.kubernetes_cluster_health
```

## 📚 Documentation

For detailed information, see the following documentation:

- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Logging Documentation](docs/LOGGING.md)** - Understanding logs and debugging
- **[Development Guide](docs/DEVELOPMENT.md)** - Contributing and development setup

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

For development information, see the [Development Guide](docs/DEVELOPMENT.md).

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Note**: This integration requires a Kubernetes cluster with proper RBAC permissions configured. Make sure your service account has the necessary permissions for monitoring and controlling deployments.

