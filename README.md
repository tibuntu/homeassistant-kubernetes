# Home Assistant Kubernetes Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Tibuntu&repository=homeassistant-kubernetes)

A Home Assistant integration for monitoring and controlling Kubernetes clusters.

## Features

- **Cluster Monitoring**: Monitor pods, nodes, deployments, statefulsets, daemonsets, and cronjobs
- **Node Sensors**: Per-node sensors for status, IP addresses, memory/CPU resources, and system information
- **Multi-Namespace Support**: Monitor a single namespace or all namespaces
- **Workload Control**: Scale, start, and stop deployments and statefulsets from Home Assistant
- **CronJob Management**: Control CronJob suspension state and trigger jobs manually via service calls
- **Dynamic Entity Management**: Automatic entity creation and cleanup as cluster resources change
- **Dashboard Panel**: Built-in sidebar panel with cluster overview, resource counts, health monitoring, and alerts

## Installation

### HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed
2. Search for "Kubernetes" and install
3. Restart Home Assistant

### Manual Installation

1. Copy `custom_components/kubernetes` to your `config/custom_components/` directory
2. Restart Home Assistant

## Setup

1. **Configure Kubernetes Service Account**:

   ```bash
   # Apply the full RBAC manifests (monitoring + switches + Watch API)
   kubectl apply -f https://raw.githubusercontent.com/tibuntu/homeassistant-kubernetes/refs/heads/main/manifests/full/serviceaccount.yaml
   kubectl apply -f https://raw.githubusercontent.com/tibuntu/homeassistant-kubernetes/refs/heads/main/manifests/full/clusterrole.yaml
   kubectl apply -f https://raw.githubusercontent.com/tibuntu/homeassistant-kubernetes/refs/heads/main/manifests/full/clusterrolebinding.yaml
   kubectl apply -f https://raw.githubusercontent.com/tibuntu/homeassistant-kubernetes/refs/heads/main/manifests/full/serviceaccount-token-secret.yaml

   # Extract the token
   kubectl get secret homeassistant-kubernetes-integration-token -n homeassistant -o jsonpath='{.data.token}' | base64 -d
   ```

   > **Minimal permissions:** If you only need read-only sensors and binary sensors (no switches, no Watch API), use the `manifests/minimal/` variants instead — replace `full` with `minimal` in the URLs above. See the [RBAC Reference Guide](docs/RBAC.md) for a full comparison.

2. **Add Integration**:
   - Go to **Settings → Devices & Services**
   - Add "Kubernetes" integration
   - Enter your cluster details and the token from step 1

## Documentation

For full documentation, visit the [documentation site](https://tibuntu.github.io/homeassistant-kubernetes/).

## Contributing

Contributions are welcome. Please submit a [Pull Request](https://github.com/tibuntu/homeassistant-kubernetes/pulls) or refer to the [Development Guide](https://tibuntu.github.io/homeassistant-kubernetes/DEVELOPMENT/) to get started.

[![Contributors](https://contrib.rocks/image?repo=tibuntu/homeassistant-kubernetes)](https://github.com/tibuntu/homeassistant-kubernetes/graphs/contributors)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
