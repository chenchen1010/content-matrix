"""
火山引擎（字节跳动）语音识别模块

使用 大模型流式语音识别API (bigmodel_nostream 流式输入模式)
文档: https://www.volcengine.com/docs/6561/1354869
"""

import os
import json
import uuid
import struct
import gzip
import tempfile
from pathlib import Path
from typing import Optional, Union

import websocket
import requests


class VolcengineASR:
    """火山引擎 ASR 识别器"""

    ENDPOINT_NOSTREAM = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_nostream"
    RESOURCE_ID = "volc.bigasr.sauc.duration"

    def __init__(self, app_id: Optional[str] = None, access_token: Optional[str] = None):
        self.app_id = app_id or os.getenv("VOLCENGINE_APP_ID")
        self.access_token = access_token or os.getenv("VOLCENGINE_ACCESS_TOKEN")
        if not self.app_id or not self.access_token:
            raise ValueError(
                "火山引擎 ASR 需要 VOLCENGINE_APP_ID 和 VOLCENGINE_ACCESS_TOKEN，"
                "请在 .env 中设置"
            )

    def _build_header(self, msg_type: int, flags: int, serial: int, compression: int) -> bytes:
        byte0 = (0x1 << 4) | 0x1
        byte1 = (msg_type << 4) | flags
        byte2 = (serial << 4) | compression
        byte3 = 0x00
        return bytes([byte0, byte1, byte2, byte3])

    def _send_frame(self, ws, msg_type, flags, serial, compression, payload_bytes):
        if compression == 0x1:
            payload_bytes = gzip.compress(payload_bytes)
        header = self._build_header(msg_type, flags, serial, compression)
        size = struct.pack(">I", len(payload_bytes))
        ws.send(header + size + payload_bytes, opcode=0x2)

    def _parse_response(self, data: bytes) -> dict:
        if not isinstance(data, bytes) or len(data) < 4:
            return {}
        header = data[:4]
        msg_type = (header[1] >> 4) & 0xF
        compression = header[2] & 0xF

        if msg_type == 0xF:
            err_code = struct.unpack(">I", data[4:8])[0]
            err_size = struct.unpack(">I", data[8:12])[0]
            err_msg = data[12 : 12 + err_size].decode("utf-8", errors="replace")
            return {"error": f"服务端错误 {err_code}: {err_msg}"}

        if msg_type == 0x9:
            seq = struct.unpack(">I", data[4:8])[0]
            payload_size = struct.unpack(">I", data[8:12])[0]
            payload_data = data[12 : 12 + payload_size]
            if compression == 0x1:
                payload_data = gzip.decompress(payload_data)
            return json.loads(payload_data)

        return {}

    def recognize_audio(
        self,
        audio_input: Union[str, Path],
        context: Optional[str] = None,
        language: Optional[str] = None,
        enable_lid: bool = True,
        enable_itn: bool = False,
    ) -> dict:
        try:
            audio_path = str(audio_input)
            if audio_path.startswith("file://"):
                audio_path = audio_path[7:]

            if not os.path.exists(audio_path):
                return {"success": False, "error": f"文件不存在: {audio_path}", "text": "", "language": None}

            with open(audio_path, "rb") as f:
                audio_data = f.read()

            ext = Path(audio_path).suffix.lower().lstrip(".")
            fmt_map = {"pcm": "pcm", "wav": "wav", "ogg": "ogg", "mp3": "mp3"}
            fmt = fmt_map.get(ext, "wav")

            connect_id = str(uuid.uuid4())

            ws = websocket.create_connection(
                self.ENDPOINT_NOSTREAM,
                header=[
                    f"X-Api-App-Key: {self.app_id}",
                    f"X-Api-Access-Key: {self.access_token}",
                    f"X-Api-Resource-Id: {self.RESOURCE_ID}",
                    f"X-Api-Connect-Id: {connect_id}",
                ],
                timeout=60,
            )

            try:
                req_payload = {
                    "user": {"uid": "content-matrix"},
                    "audio": {"format": fmt, "rate": 16000, "bits": 16, "channel": 1},
                    "request": {
                        "model_name": "bigmodel",
                        "enable_itn": enable_itn,
                        "enable_punc": True,
                        "result_type": "full",
                    },
                }
                if language:
                    req_payload["audio"]["language"] = language

                req_bytes = json.dumps(req_payload).encode("utf-8")
                self._send_frame(ws, 0x1, 0x0, 0x1, 0x1, req_bytes)

                ack = ws.recv()
                ack_parsed = self._parse_response(ack)
                if "error" in ack_parsed:
                    return {"success": False, "error": ack_parsed["error"], "text": "", "language": None}

                chunk_size = 3200
                last_result = {}
                offset = 0
                while offset < len(audio_data):
                    end = min(offset + chunk_size, len(audio_data))
                    chunk = audio_data[offset:end]
                    is_last = end >= len(audio_data)
                    flags = 0x2 if is_last else 0x0
                    self._send_frame(ws, 0x2, flags, 0x0, 0x1, chunk)

                    resp = ws.recv()
                    parsed = self._parse_response(resp)
                    if "error" in parsed:
                        return {"success": False, "error": parsed["error"], "text": "", "language": None}
                    if parsed:
                        last_result = parsed

                    offset = end

                text = ""
                if "result" in last_result:
                    text = last_result["result"].get("text", "")

                return {"success": True, "text": text, "language": None}

            finally:
                ws.close()

        except Exception as e:
            return {"success": False, "error": str(e), "text": "", "language": None}

    def recognize_file(
        self,
        file_path: Union[str, Path],
        context: Optional[str] = None,
        language: Optional[str] = None,
        enable_lid: bool = True,
        enable_itn: bool = False,
    ) -> dict:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        if not file_path.exists():
            return {"success": False, "error": f"文件不存在: {file_path}", "text": "", "language": None}
        return self.recognize_audio(file_path, context, language, enable_lid, enable_itn)

    def recognize_url(
        self,
        audio_url: str,
        context: Optional[str] = None,
        language: Optional[str] = None,
        enable_lid: bool = True,
        enable_itn: bool = False,
    ) -> dict:
        try:
            resp = requests.get(audio_url, timeout=120)
            resp.raise_for_status()
            suffix = ".mp3"
            if "wav" in audio_url:
                suffix = ".wav"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(resp.content)
                tmp_path = f.name
            result = self.recognize_file(tmp_path, context, language, enable_lid, enable_itn)
            os.unlink(tmp_path)
            return result
        except Exception as e:
            return {"success": False, "error": str(e), "text": "", "language": None}
