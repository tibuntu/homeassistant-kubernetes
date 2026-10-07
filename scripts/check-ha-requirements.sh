#!/usr/bin/env bash
# Resolve the integration's manifest requirements against Home Assistant's
# package_constraints.txt — the pins HA enforces when it installs a custom
# integration. pytest-homeassistant-custom-component does not apply them, so
# the test suite cannot catch a requirement HA will refuse to install
# (v1.13.1: kubernetes 37 needed a newer pydantic than HA pinned).
#
# Checks the minimum version in hacs.json and the latest stable HA release.
# Needs uv and an authenticated gh (GH_TOKEN in CI).
set -euo pipefail
cd "$(dirname "$0")/.."

minimum=$(jq -r .homeassistant hacs.json)
latest=$(gh api repos/home-assistant/core/releases/latest --jq .tag_name)

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
jq -r '.requirements[]' custom_components/kubernetes/manifest.json >"$tmp/requirements.txt"

status=0
for ref in "$minimum" "$latest"; do
  curl -fsSL -o "$tmp/constraints.txt" \
    "https://raw.githubusercontent.com/home-assistant/core/$ref/homeassistant/package_constraints.txt"
  if uv pip compile -q --python-version 3.14 -c "$tmp/constraints.txt" \
    "$tmp/requirements.txt" -o "$tmp/resolved.txt"; then
    echo "OK   Home Assistant $ref"
  else
    echo "FAIL Home Assistant $ref"
    status=1
  fi
done
exit "$status"
