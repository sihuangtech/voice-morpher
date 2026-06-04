from __future__ import annotations

import shlex
import shutil
import subprocess
from pathlib import Path

from backends.base import ConversionRequest, VoiceBackend


class PassthroughBackend(VoiceBackend):
    """开发后端：不做推理，直接复制源音频，方便先验证流程。"""

    name = "passthrough"
    label = "Passthrough"
    mode = "audio_to_audio"
    description = "开发后端：直接复制源音频，用于验证上传、预处理和下载流程。"

    def convert(self, request: ConversionRequest) -> Path:
        if request.source_wav is None:
            raise RuntimeError("Passthrough backend requires source audio")
        request.output_wav.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(request.source_wav, request.output_wav)
        return request.output_wav


class CommandTemplateBackend(VoiceBackend):
    """通用 CLI 后端。

    这里不关心第三方模型怎么安装，只负责把统一占位符替换成
    本项目准备好的音频、文本和输出路径。
    """

    label = "Command Template"

    def __init__(self, command_template: str | None) -> None:
        if not command_template:
            raise RuntimeError(
                f"Set command for backend '{self.name}'. Available placeholders: "
                "{source}, {reference}, {text}, {prompt_text}, {output}"
            )
        self.command_template = command_template

    def convert(self, request: ConversionRequest) -> Path:
        request.output_wav.parent.mkdir(parents=True, exist_ok=True)
        command = self.command_template.format(
            source=shlex.quote(str(request.source_wav)) if request.source_wav else "",
            reference=shlex.quote(str(request.reference_wav)),
            text=shlex.quote(request.text or ""),
            prompt_text=shlex.quote(request.prompt_text or ""),
            output=shlex.quote(str(request.output_wav)),
        )
        completed = subprocess.run(
            command,
            shell=True,
            check=False,
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"{self.label} command failed.\n"
                f"STDOUT:\n{completed.stdout}\n"
                f"STDERR:\n{completed.stderr}"
            )
        if not request.output_wav.exists():
            raise RuntimeError(f"{self.label} command finished but did not create {request.output_wav}")
        return request.output_wav


class SeedVcCliBackend(CommandTemplateBackend):
    name = "seed_vc_cli"
    label = "Seed-VC CLI"
    mode = "audio_to_audio"
    description = "推荐主线：源音频 + 参考音频 -> 换音色，尽量保留语速、停顿和语气。"


class CosyVoice3CliBackend(CommandTemplateBackend):
    name = "cosyvoice3_cli"
    label = "CosyVoice3 CLI"
    mode = "text_to_speech"
    description = "参考音频 + 文本 -> 克隆音色生成语音，适合配音和视频翻译。"


class Qwen3TtsCliBackend(CommandTemplateBackend):
    name = "qwen3_tts_cli"
    label = "Qwen3 TTS / MLX CLI"
    mode = "text_to_speech"
    description = "Apple Silicon 友好的 TTS 克隆候选，适合 Mac 本地低门槛试验。"


class ChatterboxCliBackend(CommandTemplateBackend):
    name = "chatterbox_cli"
    label = "Chatterbox CLI"
    mode = "text_to_speech"
    description = "轻量 zero-shot TTS 克隆候选，适合文本配音分支。"


class F5TtsCliBackend(CommandTemplateBackend):
    name = "f5_tts_cli"
    label = "F5-TTS CLI"
    mode = "text_to_speech"
    description = "成熟 zero-shot TTS 克隆候选，适合研究和非商业 Demo。"


class OpenVoiceCliBackend(CommandTemplateBackend):
    name = "openvoice_cli"
    label = "OpenVoice V2 CLI"
    mode = "text_to_speech"
    description = "轻量、MIT、跨语言的开源声音克隆候选。"


class IndexTtsCliBackend(CommandTemplateBackend):
    name = "indextts_cli"
    label = "IndexTTS CLI"
    mode = "text_to_speech"
    description = "中文和情绪表达能力强的 zero-shot TTS 克隆候选。"


class XttsCliBackend(CommandTemplateBackend):
    name = "xtts_cli"
    label = "XTTS v2 CLI"
    mode = "text_to_speech"
    description = "经典多语言 voice cloning TTS 候选，许可需按使用场景确认。"
