# Home Assistant Kubernetes Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![codecov](https://codecov.io/gh/tibuntu/homeassistant-kubernetes/graph/badge.svg)](https://codecov.io/gh/tibuntu/homeassistant-kubernetes)
[![GitHub Release](https://img.shields.io/github/v/release/tibuntu/homeassistant-kubernetes)](https://github.com/tibuntu/homeassistant-kubernetes/releases/latest)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Tibuntu&repository=homeassistant-kubernetes)

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/tibuntu)

A Home Assistant integration for monitoring and controlling Kubernetes clusters.

## Features

- **Cluster Monitoring**: Monitor pods, nodes, deployments, statefulsets, daemonsets, cronjobs, and ingresses
- **Node Sensors**: Per-node sensors for status, IP addresses, memory/CPU resources, real-time usage metrics, and system information
- **Multi-Namespace Support**: Monitor a single namespace or all namespaces
- **Workload Control**: Scale, start, stop, and rolling-restart deployments, statefulsets, and daemonsets from Home Assistant
- **Pod Management**: Delete individual pods directly from the sidebar panel (requires HA admin role); per-pod sensors expose container-state diagnostics — CrashLoopBackOff, ImagePullBackOff, OOMKilled (including a recovered OOMKill that already restarted, via `last_terminated_reason`), and scheduling failures — plus a derived `problem`/`problem_reason` attribute for easy automations and alerts
- **Job Management**: Delete Jobs (including failed Jobs) via the sidebar panel or `kubernetes.delete_job` service; cascades to pods
- **CronJob Management**: Control CronJob suspension state and trigger jobs manually via service calls
- **Node Management**: Cordon and uncordon nodes via per-node switches (on = schedulable) or the `kubernetes.cordon_node` / `kubernetes.uncordon_node` services
- **Dynamic Entity Management**: Automatic entity creation and cleanup as cluster resources change
- **Dashboard Panel**: Built-in sidebar panel with cluster overview, resource counts, health monitoring, and alerts; a Network tab lists Ingresses with clickable URLs, backing service, and TLS status
- **Diagnostics**: Native Home Assistant Diagnostics download with redacted credentials for easier bug reporting
- **System Health**: Cluster reachability and aggregate pod/node counts shown in *Settings → System → Repairs → System Information*
- **Repair Issues**: Surfaces silent failures (missing kubernetes Python package, metrics-server unavailable, watch connection failing) as actionable repair issues with auto-clear once resolved
- **In-Cluster ServiceAccount Support**: When Home Assistant runs inside the Kubernetes cluster, the config flow auto-fills host/port/token/CA cert from the pod's ServiceAccount, and an opt-in runtime mode re-reads the bearer token on each request to handle automatic projected-token rotation
- **Cluster Event Platform**: Opt-in HA event entity ("Cluster events") per cluster that fires Home Assistant events for Kubernetes cluster activity — OOMKilling, FailedScheduling, BackOff, Evicted, Unhealthy, ImagePullBackOff, and more. Use events to drive automations and alerts. Warning-type events only by default; configurable to include all events. Enable via **Configure → Enable Cluster Events**

## Installation

### HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed
2. Search for "Kubernetes" and install
3. Restart Home Assistant

### Manual Installation

1. Copy `custom_components/kubernetes` to your `config/custom_components/` directory
2. Restart Home Assistant

## Setup

1. **Configure Kubernetes Service Account** — with the Helm chart (recommended, so `helm upgrade` keeps the permissions current):

   ```bash
   # Full permissions: monitoring + switches + Watch API
   helm install ha-k8s-rbac oci://ghcr.io/tibuntu/charts/homeassistant-kubernetes-rbac \
     --namespace homeassistant --create-namespace

   # Extract the token
   kubectl get secret homeassistant-kubernetes-integration-token -n homeassistant -o jsonpath='{.data.token}' | base64 -d
   ```

   Or with plain manifests, if you don't use Helm:

   ```bash
   kubectl apply -f https://raw.githubusercontent.com/tibuntu/homeassistant-kubernetes/refs/heads/main/manifests/full/serviceaccount.yaml
   kubectl apply -f https://raw.githubusercontent.com/tibuntu/homeassistant-kubernetes/refs/heads/main/manifests/full/clusterrole.yaml
   kubectl apply -f https://raw.githubusercontent.com/tibuntu/homeassistant-kubernetes/refs/heads/main/manifests/full/clusterrolebinding.yaml
   kubectl apply -f https://raw.githubusercontent.com/tibuntu/homeassistant-kubernetes/refs/heads/main/manifests/full/serviceaccount-token-secret.yaml
   ```

   > **Already applied the manifests?** Add `--take-ownership` to the `helm install` so Helm adopts the existing objects instead of failing on ownership metadata (Helm 3.17+). Same names, same permissions — nothing is recreated. See [RBAC](docs/RBAC.md#already-applied-the-plain-manifests).
   >
   > **Minimal permissions:** If you only need read-only sensors and binary sensors (no switches, no Watch API), add `--set mode=minimal` to the Helm command — or replace `full` with `minimal` in the manifest URLs. See the [RBAC Reference Guide](docs/RBAC.md) for a full comparison and all chart values.
   >
   > **Home Assistant inside the cluster?** Add `--set tokenSecret.create=false` and bind the ServiceAccount to the HA pod instead — see the [Setup Guide](docs/SETUP.md) for automatic token rotation.

2. **Add Integration**:
   - Go to **Settings → Devices & Services**
   - Add "Kubernetes" integration
   - Enter your cluster details and the token from step 1

## Documentation

For full documentation, visit the [documentation site](https://tibuntu.github.io/homeassistant-kubernetes/).

## Quality

Custom integrations are not part of Home Assistant's official [Integration Quality Scale](https://www.home-assistant.io/docs/quality_scale/), but this integration voluntarily meets all **Bronze** and **Silver** tier requirements. In practice this means:

- Fully UI-based setup with connection validation, duplicate detection, a reconfigure flow, and a re-authentication prompt when the API token becomes invalid
- Service calls that surface errors in the UI and in automation traces instead of failing silently
- An enforced test-coverage gate of 95% overall and 100% for the config flow
- Clean config entry lifecycle handling (typed runtime data, proper unload, no leftovers)

These requirements are maintained for every change as part of code review.

## Contributing

Contributions are welcome. Please submit a [Pull Request](https://github.com/tibuntu/homeassistant-kubernetes/pulls) or refer to the [Development Guide](https://tibuntu.github.io/homeassistant-kubernetes/DEVELOPMENT/) to get started.

[![Contributors](https://contrib.rocks/image?repo=tibuntu/homeassistant-kubernetes)](https://github.com/tibuntu/homeassistant-kubernetes/graphs/contributors)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
