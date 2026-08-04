{{/* Name shared by the ServiceAccount, ClusterRole and ClusterRoleBinding. */}}
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
