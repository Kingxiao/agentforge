#!/usr/bin/env bash
# pin-action.sh — 将 workflow 文件中的 GitHub Action 引用从 tag 替换为 commit hash
# 防供应链攻击：tag 可以被强推覆盖，commit hash 不可变
#
# 用法:
#   ./pin-action.sh .github/workflows/claude-review.yml
#   ./pin-action.sh .github/workflows/     # 处理整个目录
#
# 依赖: gh CLI (已登录), git
# 示例输出:
#   Pinning anthropics/claude-code-action@v1
#   → resolved to abc1234def5678...
#   Updated: uses: anthropics/claude-code-action@abc1234  # v1

set -euo pipefail

TARGET="${1:-.github/workflows}"

if ! command -v gh &>/dev/null; then
    echo "Error: gh CLI not found. Install with: pacman -S github-cli" >&2
    exit 1
fi

pin_action() {
    local action_ref="$1"   # e.g. anthropics/claude-code-action@v1
    local repo tag
    repo="${action_ref%@*}"  # anthropics/claude-code-action
    tag="${action_ref#*@}"   # v1

    # 跳过已经是 hash 的引用（40位 hex）
    if [[ "$tag" =~ ^[0-9a-f]{40}$ ]]; then
        echo "  Already pinned: $action_ref"
        return
    fi

    echo "Pinning $action_ref"
    local hash
    hash=$(gh api "repos/${repo}/commits/${tag}" --jq '.sha' 2>/dev/null || \
           echo "")

    if [[ -z "$hash" ]]; then
        echo "  WARNING: Could not resolve $action_ref, skipping" >&2
        return
    fi

    echo "  → ${hash}"

    # 替换文件中所有出现的该 action 引用
    if [[ -f "$CURRENT_FILE" ]]; then
        local tmp_file line
        tmp_file=$(mktemp "${CURRENT_FILE}.tmp.XXXXXX")
        while IFS= read -r line || [[ -n "$line" ]]; do
            printf '%s\n' "${line/"uses: ${action_ref}"/"uses: ${repo}@${hash}  # ${tag}"}"
        done < "$CURRENT_FILE" > "$tmp_file"
        mv "$tmp_file" "$CURRENT_FILE"
        echo "  Updated in $CURRENT_FILE"
    fi
}

process_file() {
    local file="$1"
    CURRENT_FILE="$file"
    echo "Processing: $file"

    # 提取所有 uses: owner/repo@ref 引用
    sed -nE 's/^[[:space:]]*-[[:space:]]*uses:[[:space:]]*([^[:space:]#]+).*/\1/p' "$file" | sort -u | while read -r action_ref; do
        pin_action "$action_ref"
    done
}

export -f pin_action
export -f process_file

if [[ -f "$TARGET" ]]; then
    process_file "$TARGET"
elif [[ -d "$TARGET" ]]; then
    find "$TARGET" \( -name "*.yml" -o -name "*.yaml" \) -type f | while read -r f; do
        process_file "$f"
    done
else
    echo "Error: $TARGET is not a file or directory" >&2
    exit 1
fi

echo ""
echo "Done. Review changes with: git diff .github/workflows/"
echo "Commit with: git add .github/workflows/ && git commit -m 'ci: pin GitHub Actions to commit hashes'"
