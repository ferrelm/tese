#!/bin/bash
# Create a clean tar.xz archive of the project, excluding dumps and editor/OS cruft
# Usage: ./scripts/create_clean_tar.sh
set -euo pipefail

# Always run from the project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"


# Version label: current git commit, or "nogit" outside a repository
VERSION=$(git -C "$PROJECT_ROOT" describe --always --dirty 2>/dev/null || echo nogit)

DUMPS_DIR="$PROJECT_ROOT/dumps"
mkdir -p "$DUMPS_DIR"

# Detect project name from project root directory
PROJECT_NAME=$(basename "$PROJECT_ROOT")

# Compose archive name using detected project name (xz compression)
ARCHIVE_NAME="$DUMPS_DIR/${PROJECT_NAME}-clean-${VERSION}-$(date +%Y%m%d%H%M).tar.xz"

# Exclude patterns
EXCLUDES=(
  --exclude='./dumps'
  --exclude='./scripts/output'
  --exclude='**/.git'
  --exclude='**/.idea'
  --exclude='**/.vscode'
  --exclude='**/.DS_Store'
  --exclude='**/Thumbs.db'
  --exclude='**/tmp'
  --exclude='*.log'
)

tar -cJf "$ARCHIVE_NAME" "${EXCLUDES[@]}" .

echo "Created $ARCHIVE_NAME"
