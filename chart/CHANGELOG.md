# Changelog

Changes to the `homeassistant-kubernetes-rbac` Helm chart. The chart is versioned independently of the integration; `appVersion` in `Chart.yaml` names the oldest integration release it supports.

## 2.0.1

### Fixed

- **A missing `mode` or `rbac` is rejected.** `--set mode=null` used to render without an error and `--set rbac=null` failed with a template nil-pointer error; `values.schema.json` now requires both keys and rejects them with a clear message.
- **Unknown `rbac.*` keys are rejected.** A typo such as `rbac.writeNamespace` (singular) used to be ignored, so `rbac.writeNamespaces` kept its cluster-wide default `["*"]`. The schema now rejects any key under `rbac` other than `create`, `writeNamespaces` and `extraRules`.
- The `values.yaml` comment no longer calls the Watch API experimental.

## 2.0.0

The chart version no longer follows the integration version. Chart versions up to 1.18.0 carried the integration's version number.

### Breaking

- **Both roles grant only the verbs the integration requests.** Removed: `update` everywhere, `get` except on `pods`, `cronjobs` and `pods/log`, the resources `replicasets`, `statefulsets/status` and `cronjobs/status`, `create` and `delete` on `cronjobs`, and the `extensions` API group. The [permission matrix](https://tibuntu.github.io/homeassistant-kubernetes/RBAC/#complete-permission-matrix) lists what remains. Needs integration 1.18.0 or newer. If you use the ServiceAccount token for anything else, check that it does not rely on a removed verb.
- **`rbac.writeNamespaces` is a required value.** `helm upgrade --reuse-values` from an earlier chart version fails with `missing property 'writeNamespaces'`; upgrade with `--reset-then-reuse-values`.

### Added

- **`rbac.writeNamespaces`** limits where `mode: full` may change resources: `["*"]` (the default, cluster-wide as before), a list of namespaces, or `[]`. See [Limiting write access to namespaces](https://tibuntu.github.io/homeassistant-kubernetes/RBAC/#limiting-write-access-to-namespaces).
