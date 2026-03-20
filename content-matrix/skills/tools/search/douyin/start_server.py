#!/usr/bin/env python3
"""
抖音 MCP 服务器启动脚本（支持火山引擎 + 阿里云双 ASR 引擎）

通过 monkey-patch 方式扩展 douyin-mcp-server，无需修改原始包。
读取 content-matrix/.env 中的 ASR_PROVIDER 决定使用哪个引擎：
  - volcengine: 火山引擎（字节跳动）
  - dashscope: 阿里云 DashScope（默认）
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
ENV_FILE = PROJECT_ROOT / ".env"

def load_env(path: Path):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def create_asr_factory():
    provider = os.getenv("ASR_PROVIDER", "dashscope").lower()

    if provider == "volcengine":
        sys.path.insert(0, str(Path(__file__).parent))
        from volcengine_asr import VolcengineASR

        def create_asr_instance(api_key=None, model=None):
            return VolcengineASR(
                app_id=os.getenv("VOLCENGINE_APP_ID"),
                access_token=os.getenv("VOLCENGINE_ACCESS_TOKEN"),
            )

        return create_asr_instance, provider
    else:
        from douyin_mcp_server.asr_module import QwenASR

        def create_asr_instance(api_key=None, model="qwen3-asr-flash"):
            key = api_key or os.getenv("DASHSCOPE_API_KEY")
            return QwenASR(api_key=key, model=model)

        return create_asr_instance, provider


def patch_server():
    import douyin_mcp_server.asr_module as asr_mod
    import douyin_mcp_server.server as server_mod

    factory, provider = create_asr_factory()
    asr_mod.create_asr_instance = factory
    server_mod.create_asr_instance = factory

    OrigDouyinProcessor = server_mod.DouyinProcessor
    _orig_init = OrigDouyinProcessor.__init__

    def patched_init(self, api_key="", model=None):
        self.api_key = api_key
        self.model = model or server_mod.DEFAULT_MODEL
        self.temp_dir = Path(__import__("tempfile").mkdtemp())

        if provider == "volcengine":
            try:
                self.asr = factory()
            except ValueError:
                self.asr = None
        else:
            import dashscope as ds
            if api_key:
                ds.api_key = api_key
            try:
                self.asr = factory(api_key, self.model)
            except ValueError:
                self.asr = None

    OrigDouyinProcessor.__init__ = patched_init

    import types

    orig_extract = None
    for name, tool in list(server_mod.mcp._tool_manager._tools.items()):
        if name == "extract_douyin_text":
            orig_extract = tool
            break

    async def patched_extract(share_link: str, model=None, context=None, ctx=None) -> str:
        try:
            asr = factory()
        except ValueError as e:
            raise Exception(str(e))

        processor = server_mod.DouyinProcessor("", model)
        ctx.info("正在解析抖音分享链接...")
        video_info = processor.parse_share_url(share_link)

        ctx.info(f"正在下载视频: {video_info['title']}")
        video_path = await processor.download_video(video_info, ctx)

        ctx.info("正在从视频中提取音频...")
        audio_path = processor.extract_audio(video_path)

        ctx.info(f"正在使用 {provider} ASR 识别文本...")
        result = asr.recognize_file(str(audio_path), context=context, language="zh")

        processor.cleanup_files(video_path, audio_path)

        if result["success"]:
            ctx.info("文本提取完成!")
            return result["text"] or "未识别到文本内容"
        else:
            raise Exception(f"ASR 识别失败: {result['error']}")

    if orig_extract:
        orig_extract.fn = patched_extract


def main():
    load_env(ENV_FILE)
    patch_server()

    from douyin_mcp_server.server import mcp
    mcp.run()


if __name__ == "__main__":
    main()
