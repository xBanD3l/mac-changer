#!/usr/bin/env bash
# Print the next vMAJOR.MINOR.PATCH tag.
# Usage:
#   next_version_tag.sh              # uses `git tag --list`
#   next_version_tag.sh v1.2 v1.2.4  # uses the given tags (for tests)
set -euo pipefail

if [ "$#" -gt 0 ]; then
  tags=$(printf '%s\n' "$@")
else
  tags=$(git tag --list 'v*' || true)
fi

latest_tag=$(printf '%s\n' "$tags" | { grep -E '^v[0-9]+(\.[0-9]+)*$' || true; } | sort -V | tail -n 1)

if [ -z "$latest_tag" ]; then
  echo "v1.0.0"
  exit 0
fi

version=${latest_tag#v}
# Pad missing .minor/.patch, and absorb leftover fields in `extra`.
# Without `extra`, `read` would put "4.0.0" into `patch` for tag v1.2.4.
IFS='.' read -r major minor patch extra <<< "${version}.0.0"
major=${major:-0}
minor=${minor:-0}
patch=${patch:-0}
patch=$((patch + 1))
new_tag="v${major}.${minor}.${patch}"

while printf '%s\n' "$tags" | grep -qx "$new_tag"; do
  patch=$((patch + 1))
  new_tag="v${major}.${minor}.${patch}"
done

echo "$new_tag"
