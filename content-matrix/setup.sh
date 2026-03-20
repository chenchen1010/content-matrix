#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOOLS_DIR="$SCRIPT_DIR/skills/tools"

echo "╔══════════════════════════════════════════╗"
echo "║   Content Matrix 工具包 — 一键安装       ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# === 搜索工具 ===
echo "━━━ [1/4] 小红书搜索工具 ━━━"
bash "$TOOLS_DIR/search/xiaohongshu/install.sh"
echo ""

echo "━━━ [2/4] 抖音搜索工具 ━━━"
bash "$TOOLS_DIR/search/douyin/install.sh"
echo ""

echo "━━━ [3/4] 微信搜索工具 ━━━"
bash "$TOOLS_DIR/search/wechat/install.sh"
echo ""

# === 发布工具 ===
echo "━━━ [4/4] 发布工具（Stagehand） ━━━"
if [ -f "$TOOLS_DIR/package.json" ]; then
  cd "$TOOLS_DIR"
  if command -v npm &>/dev/null; then
    npm install
    echo "✅ Stagehand + dotenv 已安装"
  else
    echo "❌ npm 未找到。请安装 Node.js >= 18，然后运行: cd skills/tools && npm install"
  fi
  cd "$SCRIPT_DIR"
else
  echo "⚠️ 未找到 skills/tools/package.json"
fi
echo ""

# === MCP 注册 ===
echo "━━━ 注册 MCP 服务 ━━━"
CURSOR_MCP="$SCRIPT_DIR/.cursor/mcp.json"
mkdir -p "$SCRIPT_DIR/.cursor"
mkdir -p "$SCRIPT_DIR/config"

if [ -f "$CURSOR_MCP" ]; then
  echo "⚠️ .cursor/mcp.json 已存在，跳过。如需更新请手动合并。"
else
  cat > "$CURSOR_MCP" << 'MCPEOF'
{
  "mcpServers": {
    "xiaohongshu": {
      "url": "http://localhost:18060/mcp",
      "description": "小红书 MCP 服务（搜索/详情/发布）"
    }
  }
}
MCPEOF
  echo "✅ 已创建 .cursor/mcp.json"
fi

# 抖音 MCP（mcporter）
if command -v mcporter &>/dev/null; then
  # douyin_search（抖音搜索）
  if ! mcporter config get douyin_search &>/dev/null; then
    mcporter config add douyin_search \
      --command "uv" \
      --arg "run" \
      --arg "--directory=$SCRIPT_DIR/skills/tools/search/douyin/douyin_mcp" \
      --arg "python" \
      --arg "main.py" \
      --transport stdio \
      --scope project 2>/dev/null && echo "✅ 已注册 douyin_search（抖音搜索）"
  fi
  # douyin（视频解析 + ASR，火山引擎/阿里云）
  if ! mcporter config get douyin &>/dev/null; then
    mcporter config add douyin \
      --command "python3" \
      --arg "$SCRIPT_DIR/skills/tools/search/douyin/start_server.py" \
      --transport stdio \
      --scope project 2>/dev/null && echo "✅ 已注册 douyin（视频解析+ASR）"
  fi
fi

# === .env ===
if [ ! -f "$SCRIPT_DIR/.env" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
  cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
  echo "✅ 已创建 .env（请编辑填入 API Key）"
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║              安装完成！                  ║"
echo "╠══════════════════════════════════════════╣"
echo "║                                          ║"
echo "║  前置依赖（需自行安装）：                ║"
echo "║    brew install yakitrak/brew/obsidian   ║"
echo "║    npm install -g mcporter               ║"
echo "║                                          ║"
echo "║  接下来：                                ║"
echo "║  1. 编辑 .env 填入 API Key              ║"
echo "║  2. 启动小红书 MCP 服务                  ║"
echo "║  3. 初始化 Obsidian 知识库               ║"
echo "║  4. 对 AI 说「帮我做一套内容」           ║"
echo "║                                          ║"
echo "╚══════════════════════════════════════════╝"
