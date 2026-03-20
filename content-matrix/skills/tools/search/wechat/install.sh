#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== 安装微信公众号工具 ==="

# 1. miku_ai（公众号搜索）
echo ""
echo "📦 [1/2] 安装 miku_ai（公众号搜索）..."
if python3 -c "import miku_ai" 2>/dev/null; then
  echo "✅ miku_ai 已安装"
else
  pip install miku-ai 2>/dev/null || pip3 install miku-ai 2>/dev/null || {
    echo "⚠️ pip 安装失败，尝试 pipx..."
    pipx install miku-ai 2>/dev/null || echo "❌ 安装失败。请手动运行: pip install miku-ai"
  }
fi

# 2. wechat-article-for-ai（公众号阅读，基于 Camoufox）
echo ""
echo "📦 [2/2] 安装 wechat-article-for-ai（公众号阅读）..."
WECHAT_DIR="$SCRIPT_DIR/wechat-article-for-ai"
if [ -d "$WECHAT_DIR" ]; then
  cd "$WECHAT_DIR"
  pip install -r requirements.txt 2>/dev/null || pip3 install -r requirements.txt 2>/dev/null || {
    echo "❌ 依赖安装失败。请手动运行: cd $WECHAT_DIR && pip install -r requirements.txt"
  }
  echo "✅ wechat-article-for-ai 依赖已安装"
  echo "   首次运行时会自动下载 Camoufox 浏览器"
else
  echo "❌ 未找到 wechat-article-for-ai 目录: $WECHAT_DIR"
fi

echo ""
echo "=== 安装完成 ==="
echo "  搜索: python3 -c \"from miku_ai import get_wexin_article; ...\""
echo "  阅读: python3 $WECHAT_DIR/main.py \"https://mp.weixin.qq.com/s/xxx\""
