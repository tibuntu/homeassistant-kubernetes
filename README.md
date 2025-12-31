# Home Assistant Kubernetes Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Tibuntu&repository=homeassistant-kubernetes)

A comprehensive Home Assistant integration for monitoring and controlling Kubernetes clusters. Monitor your cluster's health and control workloads directly from Home Assistant.

## 📋 Table of Contents

- [Home Assistant Kubernetes Integration](#home-assistant-kubernetes-integration)
  - [📋 Table of Contents](#-table-of-contents)
  - [✨ Features](#-features)
  - [🚀 Quick Start](#-quick-start)
    - [Installation](#installation)
      - [HACS (Recommended)](#hacs-recommended)
      - [Manual Installation](#manual-installation)
    - [Setup](#setup)
  - [📚 Documentation](#-documentation)
  - [🤝 Contributing](#-contributing)
  - [📄 License](#-license)

## ✨ Features

- **🔍 Cluster Monitoring**: Monitor pods, nodes, deployments, statefulsets, daemonsets, and cronjobs across your Kubernetes cluster
- **�️ Individual Node Monitoring**: Detailed sensors for each node showing status, IP addresses, memory/CPU resources, and system information
- **�📁 Multi-Namespace Support**: Monitor a single namespace or all namespaces in your cluster
- **🎛️ Workload Control**: Scale, start, and stop deployments and statefulsets directly from Home Assistant
- **⏰ CronJob Management**: Control CronJob suspension state via switches and trigger jobs manually via service calls
- **🔄 Robust Connectivity**: Automatic fallback from kubernetes Python client to aiohttp for reliable API communication
- **🛡️ Advanced State Management**: Intelligent polling and state recovery for reliable operation
- **🔧 Dynamic Entity Management**: Automatic entity creation and cleanup as cluster resources change

## 🚀 Quick Start

### Installation

#### HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed
2. Search for "Kubernetes" and install
3. Restart Home Assistant

#### Manual Installation

1. Copy `custom_components/kubernetes` to your `config/custom_components/` directory
2. Restart Home Assistant

### Setup

1. **Configure Kubernetes Service Account**:

   ```bash
   # Apply the required manifests
   kubectl apply -f https://raw.githubusercontent.com/tibuntu/homeassistant-kubernetes/refs/heads/main/manifests/serviceaccount.yaml
   kubectl apply -f https://raw.githubusercontent.com/tibuntu/homeassistant-kubernetes/refs/heads/main/manifests/clusterrole.yaml
   kubectl apply -f https://raw.githubusercontent.com/tibuntu/homeassistant-kubernetes/refs/heads/main/manifests/clusterrolebinding.yaml
   kubectl apply -f https://raw.githubusercontent.com/tibuntu/homeassistant-kubernetes/refs/heads/main/manifests/serviceaccount-token-secret.yaml

   # Extract the token
   kubectl get secret homeassistant-kubernetes-integration-token -n homeassistant -o jsonpath='{.data.token}' | base64 -d
   ```

2. **Add Integration**:
   - Go to **Settings → Devices & Services**
   - Add "Kubernetes" integration
   - Enter your cluster details and the token from step 1

3. **Start Monitoring**: The integration will automatically discover and create entities for your deployments, statefulsets, daemonsets, cronjobs, individual nodes, and cluster metrics.

## 📚 Documentation

For comprehensive documentation, visit the [Mkdocs site](https://tibuntu.github.io/homeassistant-kubernetes/).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

For development information, see the [Development Guide](https://tibuntu.github.io/homeassistant-kubernetes/DEVELOPMENT/).

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
