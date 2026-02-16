#!/usr/bin/env bash
# Install Voyage GEO skills for Claude Code or OpenClaw agents
# Usage: curl -fsSL https://raw.githubusercontent.com/Onvoyage-AI/voyage-geo-agent/main/install-skills.sh | bash
set -euo pipefail

REPO="https://raw.githubusercontent.com/Onvoyage-AI/voyage-geo-agent/main"
SKILLS=(geo-setup geo-run geo-research geo-explore geo-report geo-leaderboard geo-add-provider geo-debug)

# Detect target: OpenClaw global, or Claude Code project-local
if [ -d "$HOME/.openclaw" ]; then
  SKILL_DIR="$HOME/.openclaw/skills"
else
  SKILL_DIR=".claude/skills"
fi

# Allow override via env var
SKILL_DIR="${VOYAGE_GEO_SKILL_DIR:-$SKILL_DIR}"

echo "Installing Voyage GEO skills to $SKILL_DIR ..."

for skill in "${SKILLS[@]}"; do
  mkdir -p "$SKILL_DIR/$skill"
  curl -fsSL "$REPO/.claude/skills/$skill/SKILL.md" -o "$SKILL_DIR/$skill/SKILL.md"
  echo "  + $skill"
done

echo ""
echo "Installed ${#SKILLS[@]} skills."
echo ""
echo "Commands: /geo-setup  /geo-run  /geo-research  /geo-explore"
echo "          /geo-report  /geo-leaderboard  /geo-add-provider  /geo-debug"
echo ""
echo "Requires: pip install voyage-geo"
