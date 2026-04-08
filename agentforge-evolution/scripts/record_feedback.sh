#!/usr/bin/env bash
# record_feedback.sh — 向 evolution_log.jsonl 写入一条反馈记录
# 用法: ./record_feedback.sh <category> <description> [fix_applied]
#
# category 可选值: prompt | tool | context | memory | security | harness | perf | other
# 示例:
#   ./record_feedback.sh prompt "review prompt 建议修改文件但未附说明，用户需要人工判断" ""
#   ./record_feedback.sh harness "Stop hook 误触发导致构建循环" "加 stop_hook_active 检测"

set -euo pipefail

CATEGORY="${1:-other}"
DESCRIPTION="${2:-}"
FIX_APPLIED="${3:-}"
LOG_FILE="${EVOLUTION_LOG:-evolution_log.jsonl}"
AGENT_NAME="${AGENT_NAME:-$(basename $(pwd))}"

if [[ -z "$DESCRIPTION" ]]; then
    echo "Usage: $0 <category> <description> [fix_applied]" >&2
    exit 1
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# 构建 JSON 行（不依赖 jq，用 printf 安全转义）
escape_json() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\t'/\\t}"
    printf '%s' "$s"
}

DESC_ESC=$(escape_json "$DESCRIPTION")
FIX_ESC=$(escape_json "$FIX_APPLIED")
CAT_ESC=$(escape_json "$CATEGORY")
AGENT_ESC=$(escape_json "$AGENT_NAME")

printf '{"timestamp":"%s","agent":"%s","category":"%s","description":"%s","fix_applied":"%s","decision":"PENDING"}\n' \
    "$TIMESTAMP" "$AGENT_ESC" "$CAT_ESC" "$DESC_ESC" "$FIX_ESC" >> "$LOG_FILE"

echo "Logged to $LOG_FILE:"
tail -1 "$LOG_FILE"
