#!/usr/bin/env bash
# Render the plain kubectl manifests in manifests/ from chart/.
#
# chart/ is the single source of truth for RBAC rules; manifests/{full,minimal}/
# are generated and committed so the `kubectl apply -f <raw URL>` install path
# keeps working. CI (.github/workflows/helm.yaml) fails if they drift.
#
# Usage: scripts/render-manifests.sh
set -euo pipefail

cd "$(dirname "$0")/.."

out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT

for mode in full minimal; do
  rm -f "manifests/$mode"/*.yaml
  mkdir -p "manifests/$mode"
  helm template homeassistant-kubernetes-integration chart \
    --namespace homeassistant \
    --set "mode=$mode" \
    --output-dir "$out/$mode" >/dev/null

  for f in "$out/$mode/homeassistant-kubernetes-rbac/templates"/*.yaml; do
    # Strip helm's document separator and provenance comment. The command
    # substitution also drops trailing blank lines, keeping end-of-file-fixer happy.
    printf '%s\n' "$(sed -e '1{/^---$/d;}' -e '/^# Source: /d' "$f")" \
      >"manifests/$mode/$(basename "$f")"
  done
  echo "rendered manifests/$mode/"
done
