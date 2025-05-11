#!/usr/bin/env bash
set -euo pipefail

# 1. fetch tags
git fetch --tags

# 2. find the most recent tagged commit (empty if no tags)
LATEST_COMMIT=$(git rev-list --tags --max-count=1)

if [[ -z "$LATEST_COMMIT" ]]; then
  # no tags → seed 0.1.0
  PREFIX=""
  MAJOR=0
  MINOR=1
  PATCH=0
  OLD_TAG="<none>"
else
  # describe that commit to get the tag name
  LATEST_TAG=$(git describe --tags "$LATEST_COMMIT")
  OLD_TAG="$LATEST_TAG"

  # strip optional leading “v”
  if [[ "$LATEST_TAG" == v* ]]; then
    PREFIX="v"
    VERSION="${LATEST_TAG#v}"
  else
    PREFIX=""
    VERSION="$LATEST_TAG"
  fi

  # split into components and bump patch
  IFS='.' read -r MAJOR MINOR PATCH <<< "$VERSION"
  PATCH=$((PATCH + 1))
fi

# 3. assemble new tag
NEW_TAG="${PREFIX}${MAJOR}.${MINOR}.${PATCH}"

# 4. create & push
git tag -a "$NEW_TAG" -m "Release $NEW_TAG"
git push origin "$NEW_TAG"

echo "➜ bumped $OLD_TAG → $NEW_TAG"
