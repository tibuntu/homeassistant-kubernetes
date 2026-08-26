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

## Re-authentication

If the Kubernetes API starts rejecting the stored API token (HTTP 401 — the token expired, was revoked, or its ServiceAccount was deleted), the integration stops polling and Home Assistant raises a **"Reauthentication needed"** notification for that entry. Opening it shows a form that asks for a new API token only; the host, port, CA certificate, SSL, and namespace settings stay as configured. Once a valid token is submitted, the entry is updated and reloaded automatically.

Entries using **Use in-cluster ServiceAccount at runtime** re-read the projected token file and retry before reporting an authentication failure, so ordinary token rotation never triggers this prompt. If such an entry does reach re-authentication, the projected token is being rejected persistently — submitting a token therefore also turns **Use in-cluster ServiceAccount at runtime** off for that entry, so the token you entered is the one actually used. Re-enable the checkbox via **Reconfigure** once the ServiceAccount is healthy again. See [Authentication Issues](TROUBLESHOOTING.md#authentication-issues-401-unauthorized) for how to obtain a fresh token.

## Dashboard Panel

Once the integration is set up, a **Kubernetes** entry appears in the Home Assistant sidebar. The panel provides a built-in cluster dashboard with six tabs:

- **Overview** — Cluster health badge, resource count cards, namespace breakdown, Watch API status, and alerts (nodes with pressure, degraded workloads, failed pods). Updates live whenever cluster data changes — immediately via the Watch API (enabled by default), otherwise on each coordinator poll cycle — with a 60-second fallback refresh.
- **Nodes** — Sortable table of all cluster nodes with status, roles, OS/kernel info, real-time CPU/memory usage (requires metrics-server), resource capacity, and conditions. Filterable by name, status, and role.
- **Workloads** — Management view for Deployments, StatefulSets, DaemonSets, CronJobs, and Jobs. Start/stop/scale controls for deployments and statefulsets, suspend/resume for cronjobs. Filterable by type, namespace, and status.
- **Pods** — Sortable table of all pods with phase, containers, restarts, node, IP, and age. Filterable by name, namespace, phase, and node.
- **Network** — Table of all Ingresses with class, clickable URLs (derived from TLS coverage), backing service, TLS status, and age. Filterable by name, namespace, and host. Auto-refreshes every 30 seconds.
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

### Watch API

| Option | Description | Default |
|--------|-------------|---------|
| **Enable Watch API** | Use the Kubernetes watch API for real-time updates instead of interval polling | `true` |

When enabled (the default), the integration establishes long-lived HTTP streams to the Kubernetes API server and receives `ADDED`, `MODIFIED`, and `DELETED` events as they happen. Pod and resource state changes typically appear in Home Assistant within seconds. Polling continues every 5 minutes as a fallback. Disable the option to use interval polling only (the **Switch Update Interval**, 60 seconds by default).

> **RBAC:** The watch feature requires the service account to have `watch` permission on all monitored resources — granted by the `full` permission set, but **not** by `minimal`. If the permission is missing, the watch connection cannot be established: the integration raises a repair issue and automatically falls back to regular interval polling, so data stays current. See the [RBAC guide](RBAC.md) for details.

Changing this option reloads the integration automatically.

### Job and CronJob Pods

| Option | Description | Default |
|--------|-------------|---------|
| **Exclude Job and CronJob pods** | Skip pods owned by a Job or CronJob so they never become entities | `true` |

Every run of a Job or CronJob creates a pod with a fresh, single-use name. Tracking those pods means one new entity per run, and Home Assistant keeps a record of each one in its entity registry forever — deleted entities that still belong to a live config entry are never purged. On a cluster with a handful of CronJobs this accumulates quickly: one deployment reached **265,000 registry records (200 MB)** from this alone, which is loaded into memory on every Home Assistant start.

Excluding them is the default. Pods owned by a Deployment, StatefulSet, DaemonSet or ReplicaSet, and pods with no owner at all, are unaffected — only `ownerReferences[0].kind == "Job"` is filtered. Because a CronJob owns a Job which owns the pod, this covers both.

Turn the option off if you genuinely need an entity per Job run.

Changing this option reloads the integration automatically.

### Cluster Events

| Option | Description | Default |
|--------|-------------|---------|
| **Enable Cluster Events** | Create a "Cluster events" event entity that fires Home Assistant events for Kubernetes cluster activity | `false` |
| **Event Types** | Which Kubernetes event types to surface — `warning` (Warning-type events only) or `all` (Warning and Normal) | `warning` |

When **Enable Cluster Events** is on, the integration creates one `event` entity per cluster named **Cluster events**. It tails the Kubernetes Events API using the same hardened watch infrastructure as the Watch API feature and dispatches matching events to Home Assistant.

The Kubernetes event `reason` becomes the HA `event_type`. A curated set of reasons (OOMKilling, FailedScheduling, BackOff, Evicted, Unhealthy, ImagePullBackOff, and others) are surfaced as distinct types; any unrecognised reason maps to `other`. Each event carries attributes for the involved object kind, name, namespace, message, count, and timestamp.

> **Note:** The cluster event watch loop is independent of the Watch API toggle — enabling one does not enable the other.

**RBAC:** Reading Kubernetes events requires `get`, `list`, and `watch` verbs on the core `v1` `events` resource. The `full` permission set (`mode: full` / `manifests/full/`) already grants these. The `minimal` set does **not** include events — with the Helm chart, add them via `rbac.extraRules`:

```yaml
rbac:
  extraRules:
    - apiGroups: [""]
      resources: ["events"]
      verbs: ["get", "list", "watch"]
```

With the plain manifests, add the same rule to `manifests/minimal/clusterrole.yaml` by hand. See the [RBAC guide](RBAC.md) for details.

Changing these options reloads the integration automatically.

### Data Collection Opt-Out

| Option | Description | Default |
|--------|-------------|---------|
| **Disable data collection for** | Multi-select of data categories to stop collecting | *(empty — everything collected)* |

Large clusters can produce hundreds of entities and constant recorder writes. This option lets you opt out of categories you don't need, reducing entity count, database growth, and Kubernetes API load.

The categories come in two tiers:

| Category | Effect when disabled |
|----------|----------------------|
| **Pods** | Pod detail fetch skipped entirely; no per-pod sensors |
| **DaemonSets** | Fetch skipped entirely; no DaemonSet sensors |
| **Jobs** | Fetch skipped entirely; no Job sensors |
| **Ingresses** | Fetch skipped entirely; ingress data disappears from the panel |
| **Node sensors** | Node status sensors and the 4 condition binary sensors are removed; the fetch continues so the cordon/uncordon switches keep working |
| **Deployment sensors** | Status and CPU/memory sensors removed; scale switches keep working |
| **StatefulSet sensors** | Same as Deployment sensors |
| **CronJob sensors** | CronJob status sensors removed; suspend switches keep working |
| **CPU/memory metrics** | The Kubernetes Metrics API is never called — removes all workload CPU/memory sensors and node usage data (the "metrics server unavailable" repair issue is suppressed too) |
| **Aggregate count sensors** | The 8 per-cluster count sensors (Pods Count, Nodes Count, …) are removed and their count API calls skipped |

Notes:

- Fully-skipped categories (Pods, DaemonSets, Jobs, Ingresses) also stop their watch streams when the Watch API is enabled.
- Existing entities of a disabled category are removed from Home Assistant automatically on the next update cycle.
- If a fully-skipped category is disabled while **Aggregate count sensors** stay enabled, its count sensor keeps working via a lightweight count API call.
- The `delete_job` service still works with Jobs disabled, but can no longer resolve a Job's namespace automatically — it falls back to the configured default namespace, so pass the namespace explicitly.

Changing this option reloads the integration automatically.
