#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== 安装抖音工具 ==="

# 1. yt-dlp（视频元数据 / 字幕下载）
if command -v yt-dlp &>/dev/null; then
  echo "✅ yt-dlp 已安装: $(yt-dlp --version)"
else
  if command -v brew &>/dev/null; then
    brew install yt-dlp
  elif command -v pip3 &>/dev/null; then
    pip3 install yt-dlp
  else
    curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
    chmod +x /usr/local/bin/yt-dlp
  fi
  echo "✅ yt-dlp 安装完成"
fi

# 2. douyin_mcp（抖音搜索 MCP，需 Python 3.14+）
if [ -d "$SCRIPT_DIR/douyin_mcp" ]; then
  bash "$SCRIPT_DIR/douyin_mcp/install.sh"
fi
