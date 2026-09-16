#!/usr/bin/env bash
# Called by Renovate postUpgradeTasks when kubernetes/kubernetes is bumped.
# Updates the supported Kubernetes version range in docs.
# Usage: scripts/update-k8s-support-range.sh <new-version>
#   e.g. scripts/update-k8s-support-range.sh 1.38.0
set -euo pipefail

NEW_VERSION="${1:?Usage: $0 <new-version>}"
MINOR=$(echo "$NEW_VERSION" | cut -d. -f2)
LATEST="1.${MINOR}"
PREV="1.$((MINOR - 1))"
OLDEST="1.$((MINOR - 2))"

RANGE="${OLDEST} – ${LATEST}"

# README.md — table row: "| Kubernetes | **1.35 – 1.37** ..."
sed -i "s/| Kubernetes | \*\*[0-9.]* – [0-9.]*\*\*/| Kubernetes | **${RANGE}**/" README.md

# docs/SETUP.md — prose: "**Kubernetes 1.35 – 1.37**"
sed -i "s/\*\*Kubernetes [0-9.]* – [0-9.]*\*\*/**Kubernetes ${RANGE}**/" docs/SETUP.md
