{{/* Name shared by the ServiceAccount, ClusterRole and ClusterRoleBinding, and
     the prefix of the <name>-write ClusterRole and its RoleBindings. */}}
{{- define "rbac.name" -}}
{{ default "homeassistant-kubernetes-integration" .Values.nameOverride }}
{{- end -}}

{{/*
ponytail: deliberately no helm.sh/chart or app.kubernetes.io/version label.
manifests/ is rendered from this chart and committed, so the labels must stay
version-stable — otherwise every release would churn those files.
*/}}
{{- define "rbac.labels" -}}
app.kubernetes.io/name: {{ include "rbac.name" . }}
app.kubernetes.io/component: rbac
{{- end -}}

{{/*
mode=full rules that change namespaced resources (plus pods/log), defined once:
bound cluster-wide when rbac.writeNamespaces is ["*"], otherwise per listed
namespace.
*/}}
{{- define "rbac.writeRules" -}}
# Pod deletion from the sidebar panel
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["delete"]
# drain_node service — evict pods through the Eviction API (honours PDBs)
- apiGroups: [""]
  resources: ["pods/eviction"]
  verbs: ["create"]
# Pod log snapshots in the sidebar panel (opt-in "enable_pod_logs" option).
# Logs can contain secrets.
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
# Rollout restart
- apiGroups: ["apps"]
  resources: ["deployments", "statefulsets", "daemonsets"]
  verbs: ["patch"]
# Scaling (switches, replica numbers)
- apiGroups: ["apps"]
  resources: ["deployments/scale", "statefulsets/scale"]
  verbs: ["patch"]
# CronJob suspend/resume
- apiGroups: ["batch"]
  resources: ["cronjobs"]
  verbs: ["patch"]
# CronJob triggering (creates a Job) and Job deletion
- apiGroups: ["batch"]
  resources: ["jobs"]
  verbs: ["create", "delete"]
{{- end -}}
