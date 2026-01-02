# Configuration Guide

This guide covers all configuration options for the Kubernetes Home Assistant Integration.

## Required Settings

| Setting | Description | Example |
|---------|-------------|---------|
| **Cluster Name** | A friendly name to identify this Kubernetes cluster in Home Assistant | `Production Cluster` |
| **Host** | Your Kubernetes API server host (IP address or hostname) | `192.168.1.100` |
| **API Token** | A valid Kubernetes service account token | `eyJhbGciOiJSUzI1NiIs...` |

## Optional Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Port** | Kubernetes API port | `6443` |
| **CA Certificate** | Path to your cluster's CA certificate | `null` |
| **Verify SSL** | Whether to verify SSL certificates | `false` |
| **Monitor All Namespaces** | Enable to monitor all namespaces | `true` |
| **Namespaces** | List of namespaces to monitor (only shown when "Monitor All Namespaces" is disabled) | Selected from cluster |
| **Device Grouping Mode** | How entities are organized (by Namespace or by Cluster) | `namespace` |
| **Switch Update Interval** | How often to poll for switch state updates (seconds) | `60` |
| **Scale Verification Timeout** | Maximum time to wait for scaling operations (seconds) | `30` |
| **Scale Cooldown** | Cooldown period after scaling operations (seconds) | `10` |

## Configuration via UI

The integration uses a two-step configuration process:

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for "Kubernetes"
4. **Step 1 - Connection Details**: Fill in the required connection information:
   - Cluster Name (used as the integration name)
   - Kubernetes API Host
   - API Token
   - Optional: Port, CA Certificate, Verify SSL, and other settings
   - **Monitor All Namespaces** (defaults to `true`)
5. **Step 2 - Namespace Selection** (only if "Monitor All Namespaces" is disabled):
   - The integration will automatically fetch available namespaces from your cluster
   - Select one or more namespaces from the dropdown list
   - You can select multiple namespaces by clicking on them

## Advanced Configuration

### Namespace Monitoring

- **All Namespaces** (default): Set "Monitor All Namespaces" to `true` to monitor all namespaces in your cluster. Requires cluster-wide permissions.
- **Selected Namespaces**: Set "Monitor All Namespaces" to `false` to select specific namespaces. You'll be prompted in a second step to choose which namespaces to monitor from a dropdown list populated from your cluster.

### SSL Configuration

For self-signed certificates or custom CA:

- **Verify SSL** defaults to `false` to support self-signed certificates out of the box
- Set "Verify SSL" to `true` for production environments with proper certificates
- Provide the CA certificate path for custom Certificate Authorities

### Performance Tuning

- **Switch Update Interval**: Lower values provide more responsive switches but increase API load
- **Scale Verification Timeout**: Increase for slow clusters or large deployments
- **Scale Cooldown**: Prevents rapid successive scaling operations
