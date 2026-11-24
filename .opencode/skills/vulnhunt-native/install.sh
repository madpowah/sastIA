#!/usr/bin/env bash
# Install vulnhunt-native into the OpenCode skills directory.
#
#   ./install.sh          # symlink (recommended for iteration)
#   ./install.sh --copy   # copy
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="${OPENCODE_SKILLS_DIR:-$HOME/.config/opencode/skills}"
DEST="${DEST_DIR}/vulnhunt-native"
MODE="${1:-symlink}"

mkdir -p "$DEST_DIR"

if [ "$MODE" = "--copy" ]; then
  rm -rf "$DEST"
  cp -a "$SCRIPT_DIR" "$DEST"
  echo "Copied $SCRIPT_DIR -> $DEST"
else
  rm -rf "$DEST"
  ln -s "$SCRIPT_DIR" "$DEST"
  echo "Symlinked $DEST -> $SCRIPT_DIR"
fi

echo
echo "Available as: /vulnhunt-native"
echo "SKILL.md: $DEST/SKILL.md"
