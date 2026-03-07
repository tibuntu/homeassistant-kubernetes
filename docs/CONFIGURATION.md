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

## Reconfiguring the Integration

To change connection details or settings for an existing integration entry:

1. Go to **Settings → Devices & Services**
2. Find the Kubernetes integration card
3. Click the three-dot menu (**...**) and select **Reconfigure**
4. Update the desired settings (host, port, API token, SSL, namespaces, polling intervals, grouping mode)
5. If "Monitor All Namespaces" is disabled, you will be prompted to select namespaces in a second step

**Note:** The cluster name cannot be changed during reconfiguration as it serves as the unique identifier for the integration entry. To change the cluster name, remove and re-add the integration.

## Dashboard Panel

Once the integration is set up, a **Kubernetes** entry appears in the Home Assistant sidebar. The panel provides a built-in cluster dashboard with five tabs:

- **Overview** — Cluster health badge, resource count cards, namespace breakdown, Watch API status, and alerts (nodes with pressure, degraded workloads, failed pods). Auto-refreshes every 30 seconds.
- **Nodes** — Sortable table of all cluster nodes with status, roles, OS/kernel info, real-time CPU/memory usage (requires metrics-server), resource capacity, and conditions. Filterable by name, status, and role.
- **Pods** — Sortable table of all pods with phase, containers, restarts, node, IP, and age. Filterable by name, namespace, phase, and node.
- **Workloads** — Management view for Deployments, StatefulSets, DaemonSets, CronJobs, and Jobs. Start/stop/scale controls for deployments and statefulsets, suspend/resume for cronjobs. Filterable by type, namespace, and status.
- **Settings** — Read-only view of current integration configuration (connection, namespaces, timing, features). Links to the HA integration page for editing settings.

The panel is registered automatically by default. To disable it, go to **Settings > Devices & Services > Kubernetes > Configure** and set **Enable Panel** to off. The panel is shown if any configured cluster entry has it enabled.

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

## Options (post-setup)

After the integration is set up, you can configure additional options by clicking **Configure** on the integration card in **Settings → Devices & Services**.

### Watch API (Experimental)

| Option | Description | Default |
|--------|-------------|---------|
| **Enable Watch API (Experimental)** | Use the Kubernetes watch API for real-time updates instead of polling | `false` |

When enabled, the integration establishes long-lived HTTP streams to the Kubernetes API server and receives `ADDED`, `MODIFIED`, and `DELETED` events as they happen. Pod and resource state changes typically appear in Home Assistant within seconds. Polling continues every 5 minutes as a fallback.

> ⚠️ **Experimental**: The watch feature requires the service account to have `watch` permission on all monitored resources. See the [RBAC guide](RBAC.md) for details.

Changing this option reloads the integration automatically.
