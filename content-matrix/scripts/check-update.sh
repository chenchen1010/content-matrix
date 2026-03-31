#!/usr/bin/env bash
# ─────────────────────────────────────────────
# content-matrix 更新检查器
# 对比本地 VERSION 和主仓库 VERSION，输出检查结果
# ─────────────────────────────────────────────
set -euo pipefail

UPSTREAM_REPO="chenchen1010/content-matrix"
UPSTREAM_BRANCH="main"
RAW_BASE="https://raw.githubusercontent.com/${UPSTREAM_REPO}/${UPSTREAM_BRANCH}"

# 项目根目录（脚本在 content-matrix/scripts/ 下）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

CACHE_DIR="${PROJECT_ROOT}/.gstack"
CACHE_FILE="${CACHE_DIR}/last-update-check"
CACHE_TTL=3600  # 1 小时缓存

# ── 读取本地版本 ──
LOCAL_VERSION_FILE="${PROJECT_ROOT}/VERSION"
if [[ ! -f "$LOCAL_VERSION_FILE" ]]; then
  echo "ERROR: 找不到 VERSION 文件" >&2
  exit 1
fi
LOCAL_VERSION="$(tr -d '[:space:]' < "$LOCAL_VERSION_FILE")"

# ── 检查缓存 ──
mkdir -p "$CACHE_DIR"
if [[ -f "$CACHE_FILE" ]]; then
  CACHE_AGE=$(( $(date +%s) - $(stat -f %m "$CACHE_FILE" 2>/dev/null || stat -c %Y "$CACHE_FILE" 2>/dev/null) ))
  if [[ $CACHE_AGE -lt $CACHE_TTL ]]; then
    cat "$CACHE_FILE"
    exit 0
  fi
fi

# ── 获取远程版本 ──
REMOTE_VERSION=$(curl -sf --connect-timeout 5 --max-time 10 \
  "${RAW_BASE}/VERSION" 2>/dev/null | tr -d '[:space:]' || true)

if [[ -z "$REMOTE_VERSION" ]]; then
  # 网络不通，静默跳过
  echo "UP_TO_DATE" > "$CACHE_FILE"
  echo "UP_TO_DATE"
  exit 0
fi

# ── 对比版本 ──
if [[ "$LOCAL_VERSION" == "$REMOTE_VERSION" ]]; then
  echo "UP_TO_DATE" > "$CACHE_FILE"
  echo "UP_TO_DATE"
else
  # 获取远程 CHANGELOG 的最新一节作为更新摘要
  CHANGELOG_SUMMARY=$(curl -sf --connect-timeout 5 --max-time 10 \
    "${RAW_BASE}/CHANGELOG.md" 2>/dev/null | awk '
    /^## / { if (found) exit; found=1; next }
    found { print }
  ' | head -20 || true)

  RESULT="UPGRADE_AVAILABLE ${LOCAL_VERSION} ${REMOTE_VERSION}
${CHANGELOG_SUMMARY}"
  echo "$RESULT" > "$CACHE_FILE"
  echo "$RESULT"
fi
