#!/usr/bin/env bash
set -euo pipefail

# 1. fetch tags so we're up-to-date
git fetch --tags

# 2. get the latest tag name (or empty if none)
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [[ -z "$LATEST_TAG" ]]; then
  # no previous tags → start at 0.1.0
  MAJOR=0; MINOR=1; PATCH=0
  OLD_TAG="<none>"
else
  OLD_TAG="$LATEST_TAG"
  # strip leading 'v' if present
  VERSION="${LATEST_TAG#v}"
  IFS='.' read -r MAJOR MINOR PATCH <<< "$VERSION"
  PATCH=$((PATCH + 1))
fi

# 3. always prefix with 'v'
NEW_TAG="v${MAJOR}.${MINOR}.${PATCH}"

# 4. create and push
git tag -a "$NEW_TAG" -m "Release $NEW_TAG"
git push origin "$NEW_TAG"

echo "➜ bumped ${OLD_TAG} → ${NEW_TAG}"
