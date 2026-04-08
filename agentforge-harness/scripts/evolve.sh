#!/usr/bin/env bash
# harness-evolve.sh — Analyze feedback log and propose skill improvements
# Usage: bash .claude/skills/harness-engineering/scripts/evolve.sh

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FEEDBACK_LOG="$SKILL_DIR/feedback.jsonl"

if [ ! -f "$FEEDBACK_LOG" ]; then
  echo "No feedback log found at $FEEDBACK_LOG"
  echo "The skill hasn't recorded any failures yet."
  echo "Failures are logged when you run /harness-feedback"
  exit 0
fi

TOTAL=$(wc -l < "$FEEDBACK_LOG")
echo "=== Harness Engineering Skill: Evolution Report ==="
echo ""
echo "Total feedback entries: $TOTAL"
echo ""

echo "--- Failure categories ---"
if command -v jq &>/dev/null; then
  jq -r '.category // "uncategorized"' "$FEEDBACK_LOG" | sort | uniq -c | sort -rn
  echo ""
  echo "--- Recent entries (last 5) ---"
  tail -5 "$FEEDBACK_LOG" | jq -r '"[\(.date)] \(.category): \(.description)"'
else
  echo "(install jq for detailed analysis)"
  echo ""
  echo "--- Raw entries (last 5) ---"
  tail -5 "$FEEDBACK_LOG"
fi

echo ""
echo "To apply improvements, ask Claude Code:"
echo "  'Read the feedback log and update the harness-engineering skill'"
