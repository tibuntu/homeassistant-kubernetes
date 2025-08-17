# Home Assistant Kubernetes Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Tibuntu&repository=homeassistant-kubernetes)

A comprehensive Home Assistant integration for monitoring and controlling Kubernetes clusters. Monitor your cluster's health, resource usage, and control deployments directly from Home Assistant.

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
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

## 🚀 Quick Start

### Installation

#### HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed
2. Add this repository as a custom repository in HACS
3. Search for "Kubernetes" and install
4. Restart Home Assistant

#### Manual Installation

1. Copy `custom_components/kubernetes` to your `config/custom_components/` directory
2. Restart Home Assistant

### Setup

1. **Configure Kubernetes Service Account**:

   ```bash
   # Apply the required manifests
   kubectl apply -f manifests/serviceaccount.yaml
   kubectl apply -f manifests/clusterrole.yaml
   kubectl apply -f manifests/clusterrolebinding.yaml
   kubectl apply -f manifests/serviceaccount-token-secret.yaml

   # Extract the token
   kubectl get secret homeassistant-kubernetes-integration-token -n homeassistant -o jsonpath='{.data.token}' | base64 -d
   ```

2. **Add Integration**:
   - Go to **Settings → Devices & Services**
   - Add "Kubernetes" integration
   - Enter your cluster details and the token from step 1

3. **Start Monitoring**: The integration will automatically discover and create entities for your deployments, statefulsets, and cluster metrics.

## 📚 Documentation

For comprehensive documentation, visit the [docs directory](docs/):

### Getting Started

- **[Configuration Guide](docs/CONFIGURATION.md)** - Detailed configuration options and settings
- **[Service Account Setup](docs/SETUP.md)** - Kubernetes RBAC and security configuration
- **[Examples & Automations](docs/EXAMPLES.md)** - Practical examples and automation ideas

### Reference

- **[Entities Documentation](docs/ENTITIES.md)** - Complete sensors, switches, and binary sensors reference
- **[Services Documentation](docs/SERVICES.md)** - Available services for programmatic control

### Advanced

- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Development Guide](docs/DEVELOPMENT.md)** - Contributing and development setup
- **[Logging Configuration](docs/LOGGING.md)** - Understanding logs and debugging

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

For development information, see the [Development Guide](https://tibuntu.github.io/homeassistant-kubernetes/DEVELOPMENT/).

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Note**: This integration requires a Kubernetes cluster with proper RBAC permissions configured. Make sure your service account has the necessary permissions for monitoring and controlling deployments.
