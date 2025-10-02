# Kubernetes Home Assistant Integration

Welcome to the documentation for the Kubernetes Home Assistant Integration. This custom integration allows Home Assistant to monitor and interact with Kubernetes clusters.

## Quick Navigation

### Getting Started

- [Configuration Guide](CONFIGURATION.md) - Detailed configuration options and settings
- [Service Account Setup](SETUP.md) - Kubernetes RBAC and service account configuration
- [RBAC Reference](RBAC.md) - Comprehensive RBAC permissions guide
- [Examples and Automations](EXAMPLES.md) - Practical examples and automation ideas

### Reference Documentation

- [Entities Documentation](ENTITIES.md) - Sensors, binary sensors, and switches reference
- [Services Documentation](SERVICES.md) - Available services for programmatic control

### Advanced Topics

- [Development Guide](DEVELOPMENT.md) - Information for developers and contributors
- [Entity Management](ENTITY_MANAGEMENT.md) - Automatic entity cleanup and dynamic discovery
- [Logging Configuration](LOGGING.md) - How to configure and troubleshoot logging
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions

## Overview

This integration provides sensors, binary sensors, and switches to monitor your Kubernetes cluster directly from Home Assistant. You can track pod counts, individual node status with detailed system information, resource usage, and control deployments and statefulsets.

### Key Features

- **Cluster Metrics**: Monitor pod, node, deployment, statefulset, and cronjob counts
- **Individual Node Monitoring**: Detailed sensors for each Kubernetes node with status, IP addresses, memory/CPU resources, and system information
- **Workload Control**: Start/stop deployments and statefulsets via Home Assistant switches
- **Health Monitoring**: Binary sensor for overall cluster health
- **Dynamic Discovery**: Automatic entity creation and cleanup as resources change

## Getting Started

For installation instructions, please refer to the main [README](../README.md) in the project repository, then follow the [Configuration Guide](CONFIGURATION.md) and [Service Account Setup](SETUP.md) for detailed setup instructions.

## Support

If you encounter issues, please check the [Troubleshooting](TROUBLESHOOTING.md) guide first, then feel free to open an issue on the GitHub repository.
