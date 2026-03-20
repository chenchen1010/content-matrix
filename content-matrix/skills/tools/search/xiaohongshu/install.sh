#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$SCRIPT_DIR/bin"
mkdir -p "$INSTALL_DIR"

echo "=== 安装小红书 MCP 工具 ==="

# 检测系统架构
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
case "$ARCH" in
  arm64|aarch64) ARCH="arm64" ;;
  x86_64)        ARCH="amd64" ;;
  *)             echo "❌ 不支持的架构: $ARCH"; exit 1 ;;
esac

RELEASE_BASE="https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download"
TARBALL="xiaohongshu-mcp-${OS}-${ARCH}.tar.gz"

if [ -f "$INSTALL_DIR/xiaohongshu-mcp" ]; then
  echo "✅ 已安装，跳过下载。删除 $INSTALL_DIR/xiaohongshu-mcp 可强制重装。"
else
  echo "📥 下载 $TARBALL ..."
  curl -L "$RELEASE_BASE/$TARBALL" -o "/tmp/$TARBALL"
  tar xzf "/tmp/$TARBALL" -C "$INSTALL_DIR"
  chmod +x "$INSTALL_DIR/xiaohongshu-mcp" "$INSTALL_DIR/xiaohongshu-login" 2>/dev/null
  rm -f "/tmp/$TARBALL"
  echo "✅ 安装完成 → $INSTALL_DIR/"
fi

echo ""
echo "下一步："
echo "  1. 登录：$INSTALL_DIR/xiaohongshu-login"
echo "  2. 启动：$INSTALL_DIR/xiaohongshu-mcp"
echo "  3. 服务地址：http://localhost:18060/mcp"
