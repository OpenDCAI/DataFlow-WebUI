#!/usr/bin/env bash
# =============================================================================
# check_updates.sh — DataFlow 仓库变更感知脚本
#
# 功能：
#   1. 检测本地仓库是否有新算子文件（相对于上一次 commit）
#   2. 列出所有已注册算子名，与 knowledge_base.md 中的记录对比
#   3. 通过 GitHub CLI 感知上游 OpenDCAI/DataFlow 是否有涉及算子的新 PR/Issue
#
# 使用方式：
#   cd /path/to/DataFlow  # 先 cd 到 DataFlow 仓库根目录
#   bash /path/to/DataFlow-Skills/dataflow-dev/scripts/check_updates.sh
#
# 前提：
#   - Python 3.10+，DataFlow 已安装（pip install open-dataflow）
#   - 可选：gh CLI 已认证（gh auth login），用于感知上游变更
# =============================================================================

set -euo pipefail

REPO_ROOT="${1:-$(pwd)}"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KB_FILE="${SKILL_DIR}/context/knowledge_base.md"
UPSTREAM_REPO="OpenDCAI/DataFlow"

echo "========================================"
echo "DataFlow 知识库变更感知脚本"
echo "仓库路径：${REPO_ROOT}"
echo "========================================"
echo ""

# ─── 检查是否在 git 仓库中 ─────────────────────────────────────────────────
if ! git -C "${REPO_ROOT}" rev-parse --is-inside-work-tree &>/dev/null; then
    echo "❌ 错误：${REPO_ROOT} 不是 git 仓库，请先 cd 到 DataFlow 仓库根目录"
    exit 1
fi

# =============================================================================
# Part 1：本地变更检测
# =============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "【Part 1】本地仓库最近提交信息"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "▶ 当前分支："
git -C "${REPO_ROOT}" branch --show-current

echo ""
echo "▶ 最近 5 条提交："
git -C "${REPO_ROOT}" log --oneline -5

echo ""
echo "▶ 最近一次提交变更的文件："
git -C "${REPO_ROOT}" diff --name-only HEAD~1 HEAD 2>/dev/null || echo "（无法对比，可能是首次提交）"

# =============================================================================
# Part 2：新算子文件检测（检测 diff-filter=A：新增文件）
# =============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "【Part 2】最近新增的算子文件（30 次提交内）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

NEW_OPERATOR_FILES=$(
    git -C "${REPO_ROOT}" log --oneline --diff-filter=A \
        --format="%H %s" \
        -- 'dataflow/operators/**/*.py' \
        2>/dev/null \
        | head -30 \
    || true
)

if [[ -z "${NEW_OPERATOR_FILES}" ]]; then
    echo "✅ 未检测到新增算子文件（30 次提交内）"
else
    echo "⚠️  检测到以下新增算子文件，可能需要更新知识库："
    echo ""

    # 列出新增的具体文件
    git -C "${REPO_ROOT}" log --oneline --diff-filter=A \
        --name-only --format="" \
        -- 'dataflow/operators/**/*.py' \
        2>/dev/null \
        | grep -E '\.py$' \
        | grep -v '__init__' \
        | sort -u \
        | head -30 \
    || true
fi

# =============================================================================
# Part 3：列出所有已注册算子名
# =============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "【Part 3】当前注册的所有算子名"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

REGISTERED_OPERATORS=$(
    python3 -c "
import sys
sys.path.insert(0, '${REPO_ROOT}')
try:
    from dataflow.utils.registry import OPERATOR_REGISTRY
    names = sorted(OPERATOR_REGISTRY.get_obj_map().keys())
    for n in names:
        print(n)
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null || true
)

if [[ -z "${REGISTERED_OPERATORS}" ]]; then
    echo "⚠️  无法加载 OPERATOR_REGISTRY（确保 DataFlow 已安装且 Python 路径正确）"
else
    OPERATOR_COUNT=$(echo "${REGISTERED_OPERATORS}" | wc -l | tr -d ' ')
    echo "共注册 ${OPERATOR_COUNT} 个算子："
    echo ""
    echo "${REGISTERED_OPERATORS}"
fi

# =============================================================================
# Part 4：对比 knowledge_base.md 中未记录的算子
# =============================================================================
if [[ -n "${REGISTERED_OPERATORS}" && -f "${KB_FILE}" ]]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "【Part 4】未在 knowledge_base.md 中出现的算子"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    MISSING=()
    while IFS= read -r op_name; do
        if ! grep -q "${op_name}" "${KB_FILE}" 2>/dev/null; then
            MISSING+=("${op_name}")
        fi
    done <<< "${REGISTERED_OPERATORS}"

    if [[ ${#MISSING[@]} -eq 0 ]]; then
        echo "✅ 所有注册算子均已记录在 knowledge_base.md 中"
    else
        echo "⚠️  以下算子未在 knowledge_base.md 中找到记录，建议补充："
        echo ""
        for op in "${MISSING[@]}"; do
            echo "  - ${op}"
        done
    fi
fi

# =============================================================================
# Part 5：GitHub CLI 感知上游变更（需要 gh 已认证）
# =============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "【Part 5】上游 ${UPSTREAM_REPO} 变更感知（需要 gh auth login）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if ! command -v gh &>/dev/null; then
    echo "⏭  gh CLI 未安装，跳过上游感知"
    echo "   安装方式：https://cli.github.com/"
elif ! gh auth status &>/dev/null 2>&1; then
    echo "⏭  gh CLI 未认证，跳过上游感知"
    echo "   认证方式：gh auth login"
else
    echo "▶ 上游最近 10 条合并 PR（涉及 operators/ 路径的优先关注）："
    echo ""
    gh pr list \
        --repo "${UPSTREAM_REPO}" \
        --state merged \
        --limit 10 \
        --json number,title,mergedAt,files \
        --jq '.[] | "  #\(.number) [\(.mergedAt[:10])] \(.title)"' \
        2>/dev/null || echo "  （无法获取 PR 列表）"

    echo ""
    echo "▶ 上游最近 10 条 Open Issues："
    echo ""
    gh issue list \
        --repo "${UPSTREAM_REPO}" \
        --state open \
        --limit 10 \
        --json number,title,createdAt \
        --jq '.[] | "  #\(.number) [\(.createdAt[:10])] \(.title)"' \
        2>/dev/null || echo "  （无法获取 Issue 列表）"
fi

# =============================================================================
# 总结
# =============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "【建议操作】"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "若发现需要更新知识库，请："
echo "  1. 读取新算子文件，提取：类名、__init__ 参数、run() 参数、get_desc() 说明"
echo "  2. 在 context/knowledge_base.md §八 对应模块下补充算子条目"
echo "  3. 在 context/dev_notes.md §七「版本变更记录」中追加条目"
echo "  4. 提交说明：docs: sync knowledge_base with new operators from <PR/commit>"
echo ""
echo "========================================"
echo "脚本执行完毕"
echo "========================================"
