# Home Assistant Kubernetes Integration

A Home Assistant integration for monitoring and controlling Kubernetes clusters.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Tibuntu&repository=homeassistant-kubernetes)

## Features

- **Cluster Monitoring**: Monitor pods, nodes, services, and deployments across your Kubernetes cluster
- **Multi-Namespace Support**: Monitor a single namespace or all namespaces in your cluster
- **Deployment Control**: Scale, start, and stop deployments directly from Home Assistant
- **Robust Connectivity**: Automatic fallback from kubernetes Python client to aiohttp for reliable API communication
- **Real-time Updates**: Get live updates on your cluster's health and resource usage

## Installation

### Manual Installation

1. Download this repository
2. Copy the `custom_components/kubernetes` folder to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Go to **Settings → Devices & Services** and add the Kubernetes integration

### Configuration

#### Required Settings

- **Name**: A friendly name for your cluster
- **Host**: Your Kubernetes API server host (IP address or hostname)
- **API Token**: A valid Kubernetes service account token
- **Port**: Kubernetes API port (default: 6443)

#### Optional Settings

- **Cluster Name**: A name for your cluster (default: "default")
- **Monitor All Namespaces**: Enable to monitor all namespaces instead of a single namespace
- **Namespace**: The namespace to monitor (only shown when "Monitor All Namespaces" is disabled)
- **CA Certificate**: Path to your cluster's CA certificate (if using self-signed certificates)
- **Verify SSL**: Whether to verify SSL certificates (default: true)

#### Namespace Monitoring Options

The integration supports two namespace monitoring modes:

1. **Single Namespace Mode** (default):
   - Monitor only the specified namespace
   - Good for focused monitoring of specific applications
   - Faster API calls and less resource usage

2. **All Namespaces Mode**:
   - Monitor all namespaces in your cluster
   - Provides a complete cluster-wide view
   - Shows total counts across all namespaces
   - Useful for cluster administrators

## Sensors

The integration provides the following sensors:

- **Pods Count**: Number of pods in the monitored namespace(s)
- **Nodes Count**: Number of nodes in the cluster
- **Services Count**: Number of services in the monitored namespace(s)
- **Deployments Count**: Number of deployments in the monitored namespace(s)
- **Cluster Health**: Binary sensor indicating if the cluster is reachable

## Services

The integration provides the following services:

- **Scale Deployment**: Scale a deployment to a specific number of replicas
- **Stop Deployment**: Scale a deployment to 0 replicas (stop it)
- **Start Deployment**: Scale a deployment to 1 or more replicas (start it)

### Service Parameters

- **deployment_name**: Name of the deployment to control
- **namespace**: Namespace containing the deployment (optional, uses configured namespace if not specified)
- **replicas**: Number of replicas for scaling operations

## Service Account Setup

### Option 2: Individual Resources
Apply resources individually:
```bash
kubectl apply -f manifests/serviceaccount.yaml
kubectl apply -f manifests/clusterrole.yaml
kubectl apply -f manifests/clusterrolebinding.yaml
kubectl apply -f manifests/serviceaccount-token-secret.yaml
```

3. Extract the token:
```bash
kubectl get secret homeassistant-monitor-token -n default -o jsonpath='{.data.token}' | base64 -d
```

### Required Permissions

The service account needs these permissions for full functionality:

```yaml
# Read permissions for monitoring
- apiGroups: [""]
  resources: ["pods", "services", "nodes", "namespaces"]
  verbs: ["get", "list", "watch"]

# Deployment permissions (including scaling)
- apiGroups: ["apps"]
  resources: ["deployments", "deployments/scale"]
  verbs: ["get", "list", "watch", "patch", "update"]
```

## Troubleshooting

### 401 Unauthorized Errors

If you encounter 401 Unauthorized errors, this typically indicates an authentication or permission issue.

**Common causes:**
- Token has expired (tokens typically expire after 1 hour)
- Incorrect token format
- Insufficient permissions for the service account
- Missing RBAC permissions for deployment scaling

**Solutions:**
1. **Verify the token works** with curl:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" https://YOUR_HOST:6443/api/v1/
   ```

2. **Test deployment scaling permissions**:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" https://YOUR_HOST:6443/apis/apps/v1/namespaces/default/deployments
   ```

3. **Check service account permissions**:
   ```bash
   kubectl auth can-i patch deployments --as=system:serviceaccount:default:homeassistant-monitor
   kubectl auth can-i patch deployments/scale --as=system:serviceaccount:default:homeassistant-monitor
   ```

For detailed troubleshooting steps, see the [Troubleshooting Guide](docs/TROUBLESHOOTING.md) and [Logging Documentation](docs/LOGGING.md).

### Connection Issues

**Host Format**: Make sure to use only the hostname or IP address (without protocol):
- ✅ Correct: `192.168.1.49` or `k8s.example.com`
- ❌ Incorrect: `https://192.168.1.49` or `http://k8s.example.com`

**SSL Verification**: For self-signed certificates, you may need to:
1. Provide the CA certificate path
2. Or disable SSL verification (not recommended for production)

### Performance Considerations

When using "Monitor All Namespaces" mode:
- API calls may take longer due to larger data sets
- Consider increasing the scan interval if you have many namespaces
- Monitor resource usage on your Home Assistant instance

## Examples

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
## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

