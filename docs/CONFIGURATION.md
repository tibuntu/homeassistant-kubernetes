# Configuration Guide

This guide covers all configuration options for the Kubernetes Home Assistant Integration.

## Required Settings

| Setting | Description | Example |
|---------|-------------|---------|
| **Name** | A friendly name for your cluster | `Production Cluster` |
| **Host** | Your Kubernetes API server host (IP address or hostname) | `192.168.1.100` |
| **API Token** | A valid Kubernetes service account token | `eyJhbGciOiJSUzI1NiIs...` |
| **Port** | Kubernetes API port | `6443` |

## Optional Settings

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

## Configuration via UI

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for "Kubernetes"
4. Fill in the required information
5. Configure optional settings as needed

## Advanced Configuration

### Namespace Monitoring

- **Single Namespace**: Set "Monitor All Namespaces" to false and specify the namespace name
- **All Namespaces**: Set "Monitor All Namespaces" to true (requires cluster-wide permissions)

### SSL Configuration

For self-signed certificates or custom CA:

- Set "Verify SSL" to false for self-signed certificates (not recommended for production)
- Provide the CA certificate path for custom Certificate Authorities

### Performance Tuning

- **Switch Update Interval**: Lower values provide more responsive switches but increase API load
- **Scale Verification Timeout**: Increase for slow clusters or large deployments
- **Scale Cooldown**: Prevents rapid successive scaling operations
