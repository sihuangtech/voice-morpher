from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BackendSpec:
    """WebUI 展示用的后端元数据。"""

    name: str
    label: str
    mode: str
    description: str
    configured: bool


@dataclass(frozen=True)
class ConversionRequest:
    """所有后端统一接收的推理请求。

    audio-to-audio 后端会使用 source_wav + reference_wav。
    text-to-speech 后端会使用 reference_wav + text + prompt_text。
    """

    output_wav: Path
    reference_wav: Path
    source_wav: Path | None = None
    text: str | None = None
    prompt_text: str | None = None


class VoiceBackend:
    """模型后端基类。实际后端只需要实现 convert。"""

    name = "base"
    label = "Base"
    mode = "audio_to_audio"
    description = ""

    def convert(self, request: ConversionRequest) -> Path:
        raise NotImplementedError
