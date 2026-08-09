#!/usr/bin/env bash
# harness-evolve.sh — Analyze feedback log and propose skill improvements
# Usage: bash .claude/skills/harness-engineering/scripts/evolve.sh

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERIES_ENTRY_DIR="$(cd "$SKILL_DIR/../agentforge" && pwd)"
FEEDBACK_LOG="${AGENTFORGE_FEEDBACK_LOG:-$SERIES_ENTRY_DIR/scripts/feedback.jsonl}"

if [ ! -f "$FEEDBACK_LOG" ]; then
  echo "No feedback log found at $FEEDBACK_LOG"
  echo "The skill hasn't recorded any failures yet."
  echo "Create entries through an authorized feedback collector or append validated JSONL to the configured path."
  exit 0
fi

if [ ! -s "$FEEDBACK_LOG" ]; then
  echo "Feedback log exists but has no entries: $FEEDBACK_LOG"
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
echo "Next step: review repeated evidence, propose a diff, run the relevant benchmark, and obtain authorization before updating the skill."
