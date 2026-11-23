# RBAC Reference Guide

This document provides a comprehensive reference for the Role-Based Access Control (RBAC) permissions required by the Home Assistant Kubernetes Integration.

## Quick Start

Two ways to install the same `ServiceAccount`, `ClusterRole`, `ClusterRoleBinding`, and token `Secret`. Pick whichever fits your workflow — the permissions are identical.

### Option A: Helm chart (recommended)

The chart is published to the GitHub Container Registry as an OCI artifact, so `helm upgrade` picks up new permissions as the integration gains features:

```bash
# Full permissions — monitoring + control (switches) + Watch API
helm install ha-k8s-rbac oci://ghcr.io/tibuntu/charts/homeassistant-kubernetes-rbac \
  --namespace homeassistant --create-namespace

# Minimal permissions — read-only sensors only
helm install ha-k8s-rbac oci://ghcr.io/tibuntu/charts/homeassistant-kubernetes-rbac \
  --namespace homeassistant --create-namespace \
  --set mode=minimal
```

Pin a version with `--version <chart version>`; the chart version tracks the integration version. To upgrade after updating the integration:

```bash
helm upgrade ha-k8s-rbac oci://ghcr.io/tibuntu/charts/homeassistant-kubernetes-rbac \
  --namespace homeassistant --reset-then-reuse-values
```

`--reset-then-reuse-values` resets to the new chart's defaults and then re-applies your own overrides, so newly added permissions actually land. (`--reuse-values` would keep your old value set verbatim and silently skip them.)

#### Already applied the plain manifests?

Helm refuses to adopt resources it did not create:

```text
Error: INSTALLATION FAILED: Unable to continue with install: ClusterRole
"homeassistant-kubernetes-integration" in namespace "" exists and cannot be
imported into the current release: invalid ownership metadata; label validation
error: missing key "app.kubernetes.io/managed-by": must be set to "Helm"
```

Add `--take-ownership` on the first install to adopt the existing objects instead of failing:

```bash
helm install ha-k8s-rbac oci://ghcr.io/tibuntu/charts/homeassistant-kubernetes-rbac \
  --namespace homeassistant --take-ownership
```

The chart renders the same objects with the same names, so this is an in-place adoption — no permission gap, nothing recreated. Requires Helm 3.17+. On older Helm, `kubectl delete -f manifests/full/` first, then install normally.

#### Chart values

| Value | Default | Purpose |
|-------|---------|---------|
| `mode` | `full` | Permission set: `full` or `minimal`. Anything else fails the render. |
| `nameOverride` | `""` | Name of the ServiceAccount, ClusterRole and ClusterRoleBinding, and the prefix of the `<name>-write` ClusterRole and RoleBindings. Defaults to `homeassistant-kubernetes-integration`. |
| `serviceAccount.create` | `true` | Set to `false` to bind the ClusterRole to a ServiceAccount you already manage. |
| `serviceAccount.annotations` | `{}` | Extra annotations on the ServiceAccount. |
| `tokenSecret.create` | `true` | Long-lived token Secret. Set to `false` when Home Assistant runs **inside** the cluster and uses the projected (auto-rotating) token. |
| `rbac.create` | `true` | Set to `false` to render only the ServiceAccount and token Secret. |
| `rbac.writeNamespaces` | `["*"]` | Namespaces where `full` may change things. `["*"]` is cluster-wide, names scope the write rules to those namespaces, `[]` grants none. See [Limiting write access to namespaces](#limiting-write-access-to-namespaces). |
| `rbac.extraRules` | `[]` | Extra rules appended verbatim to the ClusterRole — e.g. adding `events` on top of `mode: minimal`. |

The release namespace (`--namespace`) determines the namespace of the ServiceAccount, the token Secret, and the subject of the ClusterRoleBinding and of the RoleBindings.

### Option B: Plain manifests

The `manifests/` directory contains the same two sets as ready-to-apply YAML — no Helm required:

```bash
# Full permissions — monitoring + control (switches) + Watch API
kubectl apply -f manifests/full/

# Minimal permissions — read-only sensors only
kubectl apply -f manifests/minimal/
```

Both sets create the `ServiceAccount` and `ClusterRoleBinding` in the `homeassistant` namespace. Adjust the namespace in `serviceaccount.yaml`, `serviceaccount-token-secret.yaml`, and `clusterrolebinding.yaml` if your Home Assistant pod runs elsewhere.

> **Note:** `manifests/` is generated from `chart/` (see [Development Guide](DEVELOPMENT.md#rbac-and-the-helm-chart)) — the two are always in sync, so `mode: full` and `manifests/full/` grant exactly the same permissions.

## Permission Sets

### `full` / `manifests/full/` — Recommended

Enables all integration features:

- Sensors and binary sensors (monitoring)
- Switches (deployment / statefulset scaling, CronJob suspension, node cordon/uncordon)
- Workload rollout restart (deployments, statefulsets, daemonsets)
- Ingress, HTTPRoute, and Service monitoring (Network tab in the sidebar panel, with clickable URLs)
- cert-manager Certificate monitoring (Certificate Problems sensor + Network tab; the TLS Secrets are never read)
- Pod and Job deletion from the sidebar panel (requires Home Assistant admin role)
- Node drain via the `drain_node` service (`pods/eviction`)
- Cluster Events platform (`events`)
- Watch API (real-time updates via `?watch=true`, enabled by default)

### `minimal` / `manifests/minimal/`

Read-only access to every resource the integration monitors. No write permissions.

**Limitations:**

- No switches (scaling, CronJob control, or node cordon/uncordon)
- No rollout restart, pod deletion, Job deletion, or node drain
- No pod logs in the sidebar panel (`pods/log` not granted)
- No Cluster Events platform and no events in the panel's pod detail dialog (`events` not granted) — the dialog still lists the containers and their states
- No Watch API support (`watch` verb not granted) — each stream gets HTTP 403 on connect and retries once a minute, a **Missing permissions** repair issue names the affected resource(s), and once every stream is forbidden the integration polls at the regular interval instead; disable the Watch API under **Configure** to silence the repair issue
- Sensors and binary sensors only

## Limiting write access to namespaces

By default `full` can change things in every namespace. `rbac.writeNamespaces` restricts the namespaced control rules to the namespaces you list:

```bash
helm install ha-k8s-rbac oci://ghcr.io/tibuntu/charts/homeassistant-kubernetes-rbac \
  --namespace homeassistant --set 'rbac.writeNamespaces={media,home}'
```

Or in a values file:

```yaml
rbac:
  writeNamespaces: [media, home]
```

The value takes three forms:

- `["*"]` (default): every namespace, one cluster-wide ClusterRole. This is the behaviour before the value existed. `"*"` must stand alone: a list that mixes it with namespace names, such as `["*", "media"]`, is rejected.
- Namespace names: control is limited to those namespaces.
- `[]`: no namespaced control. `full` is then monitoring, the Watch API, events and node cordon/uncordon. On the command line pass it as `--set-json 'rbac.writeNamespaces=[]'`; `--set 'rbac.writeNamespaces={}'` is rejected by the schema (Helm turns it into a list with one empty string).

The key is required: a missing or `null` value is rejected by the chart schema, as is `mode: minimal` with named namespaces (it has no write rules to scope).

With names, the cluster-wide ClusterRole keeps every read rule plus `patch` on `nodes` (cordon/uncordon is cluster-scoped). The rules below move into a second ClusterRole, `homeassistant-kubernetes-integration-write`, which one RoleBinding of the same name binds in each listed namespace:

| Resource | Verb | Feature |
|----------|------|---------|
| `pods` | `delete` | Pod deletion |
| `pods/eviction` | `create` | `drain_node` |
| `pods/log` | `get` | Panel pod log viewer |
| `deployments`, `statefulsets`, `daemonsets` | `patch` | Rollout restart |
| `deployments/scale`, `statefulsets/scale` | `patch` | Scaling |
| `cronjobs` | `patch` | CronJob suspend/resume |
| `jobs` | `create`, `delete` | CronJob trigger, Job deletion |

The integration itself is unchanged. Outside the listed namespaces the API server answers HTTP 403. The services, the replica number entity, the CronJob switch and the panel report the error. The Deployment and StatefulSet on/off switch only logs it and returns to its previous state without raising one. Entities still exist because reading stays cluster-wide. Pod logs are readable only in the listed namespaces.

`drain_node` evicts pods only in the listed namespaces, so it fails on a node that runs other non-DaemonSet pods. The service cordons every node of the call before the first eviction, so a drain that fails on pods in unlisted namespaces leaves the node cordoned; uncordon it yourself. To grant eviction cluster-wide again, add the rule yourself:

```yaml
rbac:
  writeNamespaces: ["media"]
  extraRules:
    - apiGroups: [""]
      resources: ["pods/eviction"]
      verbs: ["create"]
```

Inside a listed namespace the token can still run code as any ServiceAccount of that namespace: rollout restart needs `patch` on the workload and CronJob trigger needs `create` on Jobs. List only namespaces where that is acceptable.

Two limits to this containment:

- It holds only if the listed namespaces enforce Pod Security at the `baseline` or `restricted` level. Without it, `patch` on a workload or `create` on Jobs can start a privileged or hostPath pod and take over the node.
- `patch` on `nodes` stays cluster-wide and is more than cordon: it also allows changing node labels and taints, and a `NoExecute` taint evicts pods in every namespace.

The listed namespaces must exist before the install. There are no plain manifests for this; with `kubectl`, render them from the chart:

```bash
helm template ha-k8s-rbac oci://ghcr.io/tibuntu/charts/homeassistant-kubernetes-rbac \
  --namespace homeassistant --set 'rbac.writeNamespaces={media,home}' | kubectl apply -f -
```

`kubectl apply` does not prune. After removing a namespace from the list, delete the RoleBinding `homeassistant-kubernetes-integration-write` in that namespace yourself, or the write access stays.

A later `helm upgrade` that passes any `--set` or `-f` without `--reset-then-reuse-values` resets every value you do not repeat to the chart default. The default for `rbac.writeNamespaces` is `["*"]`, so the allowlist is silently replaced by cluster-wide write. Keep the list in a values file that you pass on every upgrade, or always upgrade with `--reset-then-reuse-values`, and check the `Write access:` line Helm prints after the upgrade.

Upgrading with `--reuse-values` from a chart older than this value fails with `missing property 'writeNamespaces'`; use `--reset-then-reuse-values`.

## Complete Permission Matrix

When `rbac.writeNamespaces` is set to namespace names, the write verbs in the `full` column for namespaced resources apply only in those namespaces (see [Limiting write access to namespaces](#limiting-write-access-to-namespaces)).

Every verb listed is one the integration requests, and `get` appears only where a single object is fetched. The roles match integration 1.18.0 and newer (the first release that talks to the API through aiohttp only), so pair the chart with the integration release of the same version.

### Core API Group (`""`)

| Resource | Verbs | Full | Minimal | Purpose |
|----------|-------|:----:|:-------:|---------|
| **pods** | `get`, `list`, `watch`, `delete` | ✅ | `get`, `list` only | Pod count and status sensors, pod deletion; `get` is the pod detail dialog |
| **pods/eviction** | `create` | ✅ | ❌ | `drain_node` service — evicts pods through the Eviction API, so PodDisruptionBudgets are honoured |
| **pods/log** | `get` | ✅ | ❌ | Pod log snapshots in the sidebar panel (opt-in, admin-only — logs can contain secrets; drop the rule if you never want them readable) |
| **nodes** | `list`, `watch`, `patch` | ✅ | `list` only | Node sensors and binary sensors; `patch` enables cordon/uncordon |
| **namespaces** | `list` | ✅ | `list` only | Namespace discovery |
| **events** | `list`, `watch` | ✅ | ❌ | Cluster Events platform (`watch`) and the Events section of the panel's pod detail dialog (`list`). Without it (e.g. `minimal`) the dialog still shows the containers and a hint instead of events |
| **services** | `list`, `watch` | ✅ | `list` only | Services Count sensor + Network tab in the sidebar panel |

### Apps API Group (`apps`)

| Resource | Verbs | Full | Minimal | Purpose |
|----------|-------|:----:|:-------:|---------|
| **deployments** | `list`, `watch`, `patch` | ✅ | `list` only | Deployment sensors + rollout restart |
| **deployments/scale** | `patch` | ✅ | ❌ | Deployment switches, replica numbers |
| **statefulsets** | `list`, `watch`, `patch` | ✅ | `list` only | StatefulSet sensors + rollout restart |
| **statefulsets/scale** | `patch` | ✅ | ❌ | StatefulSet switches, replica numbers |
| **daemonsets** | `list`, `watch`, `patch` | ✅ | `list` only | DaemonSet sensors + rollout restart |

### Batch API Group (`batch`)

| Resource | Verbs | Full | Minimal | Purpose |
|----------|-------|:----:|:-------:|---------|
| **cronjobs** | `get`, `list`, `watch`, `patch` | ✅ | `list` only | CronJob sensors, suspend/resume switch, and triggering (`start_workload` creates a Job; `get` reads the job template when triggering) |
| **jobs** | `list`, `watch`, `create`, `delete` | ✅ | `list` only | Job sensors, CronJob triggering, and Job deletion (sidebar panel / `delete_job` service) |

### Networking API Group (`networking.k8s.io`)

| Resource | Verbs | Full | Minimal | Purpose |
|----------|-------|:----:|:-------:|---------|
| **ingresses** | `list`, `watch` | ✅ | `list` only | Ingresses count sensor + Network tab in the sidebar panel |

### Gateway API Group (`gateway.networking.k8s.io`)

| Resource | Verbs | Full | Minimal | Purpose |
|----------|-------|:----:|:-------:|---------|
| **httproutes** | `list`, `watch` | ✅ | `list` only | HTTPRoutes in the Network tab. Optional: on a cluster without the Gateway API CRDs the rule is harmless and the Network tab shows no HTTPRoutes section. Without the rule the *Missing permissions* repair issue names `httproutes`; re-apply the RBAC or disable **HTTPRoutes** under *Disable data collection for* |

### cert-manager API Group (`cert-manager.io`)

| Resource | Verbs | Full | Minimal | Purpose |
|----------|-------|:----:|:-------:|---------|
| **certificates** | `list`, `watch` | ✅ | `list` only | Certificate Problems sensor and the Certificates section of the Network tab. Optional: on a cluster without cert-manager the rule is harmless, the section does not appear and the sensor stays at 0. Without the rule the *Missing permissions* repair issue names `certificates` (the API server answers 403 even when cert-manager is not installed); re-apply the RBAC or disable **Certificates** under *Disable data collection for*. No access to Secrets is needed |

### Autoscaling API Group (`autoscaling`)

| Resource | Verbs | Full | Minimal | Purpose |
|----------|-------|:----:|:-------:|---------|
| **horizontalpodautoscalers** | `list`, `watch` | ✅ | `list` only | Detects HPA-managed Deployments/StatefulSets: `hpa_*` attributes, the panel's HPA badge, and the guard that rejects scaling them to a non-zero count. Optional: without it, HPA detection is simply off |

### Metrics API Group (`metrics.k8s.io`)

| Resource | Verbs | Full | Minimal | Purpose |
|----------|-------|:----:|:-------:|---------|
| **nodes** | `list` | ✅ | ✅ | Real-time node CPU and memory usage in the sidebar panel |
| **pods** | `list` | ✅ | ✅ | Workload CPU and memory usage sensors |

> **Note:** Requires [metrics-server](https://github.com/kubernetes-sigs/metrics-server) to be installed in your cluster. If unavailable, the integration gracefully falls back to showing capacity only.

### Non-resource endpoints

| Endpoint | Verbs | Full | Minimal | Purpose |
|----------|-------|:----:|:-------:|---------|
| **/version** | `get` | — | — | Cluster version on the panel's Overview tab and the cluster device |

> **Note:** No rule is needed — Kubernetes grants `/version` to every authenticated user through the built-in `system:public-info-viewer` ClusterRoleBinding. If a hardened cluster has removed that binding, the version is simply not shown.

## Security Considerations

### Principle of Least Privilege

1. **Start Minimal**: Begin with `mode: minimal` (`manifests/minimal/`) and move to `full` only when you need switches or the Watch API
2. **Namespace Scoping**: For multi-tenant clusters limit write access with [`rbac.writeNamespaces`](#limiting-write-access-to-namespaces), or see the namespace-scoped example below
3. **Regular Audits**: Review permissions periodically
4. **Monitor Usage**: Track which permissions are actually used

### Risk Assessment

| Permission Set | Risk Level | Capabilities |
|----------------|------------|--------------|
| **full**, all namespaces | High | Complete monitoring + control + Watch API; can run a pod under any ServiceAccount in the cluster, which is equivalent to cluster-admin |
| **full** with `rbac.writeNamespaces` set to namespace names | Medium | The same, limited to the listed namespaces, provided they enforce Pod Security (`baseline` or `restricted`); `patch` on `nodes` stays cluster-wide |
| **minimal** | Low | Read-only sensors and binary sensors only |

### Token Security

1. **Secure Storage**: Store tokens securely in Home Assistant secrets
2. **Regular Rotation**: Rotate service account tokens periodically
3. **Audit Logs**: Monitor Kubernetes audit logs for token usage
4. **Network Security**: Ensure secure communication to the API server

## In-Cluster ServiceAccount (recommended when HA runs inside the cluster)

If the Home Assistant pod runs inside the same cluster it monitors, the integration can bind to the pod's ServiceAccount directly instead of using a manually-extracted token. This is the preferred path because:

- **No token extraction step.** The pod already has the projected token mounted at `/var/run/secrets/kubernetes.io/serviceaccount/token`.
- **Automatic rotation.** Kubernetes 1.21+ rotates projected ServiceAccount tokens (commonly hourly). With **Prefer in-cluster ServiceAccount token** enabled in the config flow, the integration re-reads the token file on each request and follows the rotation seamlessly. With this setting off, the captured-at-config-time token will eventually expire and auth-fail.
- **Nothing to keep alive.** The integration authenticates with the token currently mounted in the pod. The pre-filled token stored in the entry is only a fallback, and since projected tokens are bound to their pod it stops working once the pod is replaced.
- **Same RBAC rules apply.** The permission matrix above is unchanged — bind the existing `ClusterRole` (or namespace-scoped `Role`) to the ServiceAccount that the HA pod uses.

### Pod spec

Set `serviceAccountName` on the Home Assistant pod (or Deployment / StatefulSet) to the same SA referenced by your `ClusterRoleBinding`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: homeassistant
  namespace: homeassistant
spec:
  template:
    spec:
      # Bind the integration's SA to the HA pod itself.
      serviceAccountName: homeassistant-kubernetes-integration
      # automountServiceAccountToken: true is the default and is required for
      # the projected volume to be mounted at the standard path. Do not set
      # this to false if you want in-cluster auth.
      containers:
        - name: homeassistant
          image: ghcr.io/home-assistant/home-assistant:latest
```

### Config flow

When Home Assistant detects it is running inside a cluster (the `KUBERNETES_SERVICE_HOST` env var is set **and** the projected token file is readable):

- The **Host**, **Port**, **API Token**, and **CA Certificate** fields on the *Add Integration* form are pre-filled from the pod's ServiceAccount.
- A **Prefer in-cluster ServiceAccount token** checkbox is shown and defaults to enabled. Leave it on so the integration re-reads the token file on each call and survives token rotation.
- The token entered in the form is kept only as a fallback — used if the projected volume becomes unreadable for any reason (e.g. HA was later moved out of the cluster). The pre-filled value is the current pod's bound token, which is rejected after the pod is replaced; paste a long-lived token from a `kubernetes.io/service-account-token` Secret instead if you want a fallback that keeps working.

The same checkbox is also available via the three-dot menu (**...**) → **Reconfigure** if you want to flip an existing entry between in-cluster and static-token modes without re-creating it.

### Verifying

Once the HA pod is running with the bound ServiceAccount, you can verify access using the SA's identity:

```bash
# Use the pod's SA token directly (works from any pod in the same namespace)
kubectl auth can-i list pods \
  --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# From inside the HA pod itself, hit the API server with the projected token
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
curl -sS \
  --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  -H "Authorization: Bearer $TOKEN" \
  https://kubernetes.default.svc/api/v1/namespaces
```

## Namespace-Scoped Example

To limit only write access, use the chart value [`rbac.writeNamespaces`](#limiting-write-access-to-namespaces); it is the supported way. The hand-written variant below is for when reads should be scoped as well.

If you want to restrict access to specific namespaces instead of cluster-wide, use a `Role` + `RoleBinding` per namespace and a minimal `ClusterRole` for cluster-scoped resources (nodes, namespaces):

```yaml
# Cluster-scoped access for nodes and namespace discovery.
# Drop `patch` on nodes if you do not want cordon/uncordon — nodes are
# cluster-scoped, so there is no namespaced equivalent. The drain_node service
# lists the pods of a node across all namespaces, so it needs the full
# ClusterRole; it does not work with namespace-scoped roles.
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: homeassistant-kubernetes-integration-cluster
rules:
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["list", "watch", "patch"]
- apiGroups: [""]
  resources: ["namespaces"]
  verbs: ["list"]
---
# Namespace-scoped role (repeat per monitored namespace)
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: target-namespace
  name: homeassistant-kubernetes-integration
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch", "delete"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
- apiGroups: [""]
  resources: ["events", "services"]
  verbs: ["list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "statefulsets", "daemonsets"]
  verbs: ["list", "watch", "patch"]
- apiGroups: ["apps"]
  resources: ["deployments/scale", "statefulsets/scale"]
  verbs: ["patch"]
- apiGroups: ["batch"]
  resources: ["cronjobs"]
  verbs: ["get", "list", "watch", "patch"]
- apiGroups: ["batch"]
  resources: ["jobs"]
  verbs: ["list", "watch", "create", "delete"]
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses"]
  verbs: ["list", "watch"]
- apiGroups: ["gateway.networking.k8s.io"]
  resources: ["httproutes"]
  verbs: ["list", "watch"]
- apiGroups: ["cert-manager.io"]
  resources: ["certificates"]
  verbs: ["list", "watch"]
- apiGroups: ["autoscaling"]
  resources: ["horizontalpodautoscalers"]
  verbs: ["list", "watch"]
```

## Troubleshooting RBAC Issues

> The fixes below say "Apply `manifests/full/`". With the Helm chart the equivalent is `helm upgrade ... --reset-then-reuse-values --set mode=full`.

### Common Permission Errors

#### 1. "Forbidden: User cannot list pods"

```bash
# Verify pod permissions
kubectl auth can-i list pods --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Fix: Apply manifests/minimal/ or manifests/full/
```

#### 2. "Forbidden: User cannot patch deployments/scale"

```bash
# Verify scaling permissions
kubectl auth can-i patch deployments --subresource=scale --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration -n your-namespace

# Verify node cordon/uncordon permissions (node schedulable switches)
kubectl auth can-i patch nodes --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Fix: Apply manifests/full/ — the minimal set does not grant write permissions
```

If the check passes in some namespaces and fails in others, `rbac.writeNamespaces` is limiting write access: add the namespace to the list (see [Limiting write access to namespaces](#limiting-write-access-to-namespaces)). (Use `deployments --subresource=scale`: `deployments/scale` checks a Deployment named "scale".)

#### 3. "Real-time updates not working" / Watch API failing

The **Watch API** (enabled by default; toggled via **Configure → Enable Watch API**) uses long-lived HTTP streams and requires the `watch` verb on all monitored resources. The `manifests/minimal/` set does **not** include `watch` verbs — without them each stream gets HTTP 403 on connect and retries once a minute, and a **Missing permissions** repair issue names the affected resource(s) until the watch delivers an event or stays open (it clears on its own after the rule is added). Once every stream is forbidden, the integration falls back to polling at the regular interval instead of the slow watch fallback.

```bash
# Verify watch permissions for key resources
kubectl auth can-i watch pods --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration
kubectl auth can-i watch deployments --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration
kubectl auth can-i watch nodes --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Fix: Apply manifests/full/ to grant the watch verb
```

#### 4. Node CPU/memory usage not showing in sidebar panel

The sidebar panel shows node capacity but no real-time usage data. This requires [metrics-server](https://github.com/kubernetes-sigs/metrics-server) and `metrics.k8s.io` RBAC permissions.

```bash
# Verify metrics-server is running
kubectl get pods -n kube-system -l k8s-app=metrics-server

# Verify node metrics permissions
kubectl auth can-i list nodes.metrics.k8s.io --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Fix: Apply manifests/full/ or manifests/minimal/ (both include metrics permissions)
```

#### 5. "Forbidden: User cannot list cronjobs"

```bash
# Verify CronJob permissions
kubectl auth can-i list cronjobs --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Fix: Apply manifests/minimal/ or manifests/full/
```

#### 6. "Forbidden: User cannot create jobs"

```bash
# Verify job creation permissions (needed for CronJob triggering)
kubectl auth can-i create jobs --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration -n your-namespace

# Fix: Apply manifests/full/ — the minimal set only grants list on jobs
```

If the check fails only in some namespaces, `rbac.writeNamespaces` is limiting write access: add the namespace to the list.

#### 7. "Forbidden: User cannot delete pods"

Pod deletion requires **both** Home Assistant admin role and Kubernetes RBAC permissions. The panel hides the delete button from non-admin HA users, and the WebSocket command enforces admin access as well.

```bash
# Verify pod deletion permissions
kubectl auth can-i delete pods --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration -n your-namespace

# Fix: Apply manifests/full/ — the minimal set does not grant delete permissions
```

If the check fails only in some namespaces, `rbac.writeNamespaces` is limiting write access: add the namespace to the list.

#### 8. Pod log dialog: "pod logs request failed with status 403"

The log viewer needs `get` on `pods/log`. Unlike a missing watch rule, this raises no repair issue — the error shows up in the panel's log dialog only.

```bash
# Verify pod log permissions
kubectl auth can-i get pods --subresource=log --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration -n your-namespace

# Fix: re-apply manifests/full/ (or helm upgrade --reset-then-reuse-values) — the minimal set does not grant pods/log
```

If the check fails only in some namespaces, `rbac.writeNamespaces` is limiting write access: logs are readable only in the listed namespaces.

#### 9. `drain_node`: "eviction failed with status 403"

Draining needs `create` on `pods/eviction`, which was added to the full role together with the `drain_node` service. Installs set up before that need the RBAC re-applied.

```bash
# Verify eviction permissions
kubectl auth can-i create pods --subresource=eviction --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration -n your-namespace

# Fix: re-apply manifests/full/ (or helm upgrade --reset-then-reuse-values)
```

If the check fails only in some namespaces, `rbac.writeNamespaces` is limiting write access: the pod's namespace is not in the list (see [Limiting write access to namespaces](#limiting-write-access-to-namespaces)).

### Diagnostic Commands

```bash
# Check all permissions for the service account
kubectl auth can-i --list --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration

# Test specific resource access in a namespace
kubectl auth can-i list deployments --as=system:serviceaccount:homeassistant:homeassistant-kubernetes-integration -n your-namespace

# View effective permissions
kubectl describe clusterrolebinding homeassistant-kubernetes-integration
kubectl describe clusterrole homeassistant-kubernetes-integration
```

## Best Practices

1. **Version Control**: Keep your chart values (or the RBAC manifests) in version control alongside your Home Assistant configuration
2. **Start Minimal**: Use `mode: minimal` first and upgrade to `full` only when needed
3. **Stay Current**: Run `helm upgrade` after updating the integration — new features occasionally need new verbs
4. **Testing**: Test permissions in a non-production cluster first
5. **Monitoring**: Watch for permission-denied errors in the Home Assistant logs
6. **Automation**: Manage the chart with your existing GitOps / infrastructure-as-code tooling (Flux `HelmRelease`, Argo CD, Terraform `helm_release`, …)

For setup instructions, see the [Service Account Setup Guide](SETUP.md).
