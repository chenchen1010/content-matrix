#!/bin/bash
# 抖音登录助手 — 打开浏览器，登录成功后自动保存 Cookie 并关窗口（同小红书）
# 用法：./douyin-login.sh  或  bash douyin-login.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOOLS_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 确保 playwright 可用（从 skills/tools 的 node_modules）
cd "$TOOLS_DIR"
if [ ! -d "node_modules/playwright" ] && [ ! -d "node_modules/@playwright/test" ]; then
  echo "📦 安装 Playwright..."
  npm install playwright --no-save 2>/dev/null || npm install
fi

# 从 tools 目录运行，确保能解析到 playwright
cd "$TOOLS_DIR"
node "$SCRIPT_DIR/douyin-login.mjs"
