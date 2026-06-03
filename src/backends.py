from __future__ import annotations

import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import soundfile as sf

from config import settings


@dataclass(frozen=True)
class BackendSpec:
    name: str
    label: str
    mode: str
    description: str
    configured: bool


@dataclass(frozen=True)
class ConversionRequest:
    output_wav: Path
    reference_wav: Path
    source_wav: Path | None = None
    text: str | None = None
    prompt_text: str | None = None


class VoiceConversionBackend:
    name = "base"
    label = "Base"
    mode = "audio_to_audio"
    description = ""

    def convert(self, request: ConversionRequest) -> Path:
        raise NotImplementedError


class PassthroughBackend(VoiceConversionBackend):
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


class CommandTemplateBackend(VoiceConversionBackend):
    label = "Command Template"

    def __init__(self, command_template: str | None) -> None:
        if not command_template:
            raise RuntimeError(
                f"Set command for backend '{self.name}'. Available placeholders: "
                "{source}, {reference}, {text}, {output}"
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


class CosyVoice3BuiltinBackend(VoiceConversionBackend):
    name = "cosyvoice3_builtin"
    label = "CosyVoice3 Built-in"
    mode = "text_to_speech"
    description = "WebUI 内置 CosyVoice3 克隆后端，直接调用 CosyVoice Python API。"

    def convert(self, request: ConversionRequest) -> Path:
        if not request.text:
            raise RuntimeError("CosyVoice3 requires text")
        _assert_cosyvoice_ready()

        cosyvoice = _load_cosyvoice_model()
        prompt_text = request.prompt_text or "You are a helpful assistant.<|endofprompt|>"
        request.output_wav.parent.mkdir(parents=True, exist_ok=True)

        generator = cosyvoice.inference_zero_shot(
            request.text,
            prompt_text,
            str(request.reference_wav),
            stream=False,
        )
        first_chunk = next(generator, None)
        if not first_chunk or "tts_speech" not in first_chunk:
            raise RuntimeError("CosyVoice3 did not return speech")

        speech = first_chunk["tts_speech"].squeeze().detach().cpu().numpy()
        sample_rate = getattr(cosyvoice, "sample_rate", 24_000)
        sf.write(request.output_wav, speech, sample_rate, subtype="PCM_16")
        return request.output_wav


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


def get_backend(name: str | None = None) -> VoiceConversionBackend:
    backend_name = name or settings.backend
    if backend_name == "passthrough":
        return PassthroughBackend()
    if backend_name == "seed_vc_cli":
        return SeedVcCliBackend(settings.seed_vc_command)
    if backend_name == "cosyvoice3_cli":
        return CosyVoice3CliBackend(settings.cosyvoice3_command)
    if backend_name == "cosyvoice3_builtin":
        return CosyVoice3BuiltinBackend()
    if backend_name == "qwen3_tts_cli":
        return Qwen3TtsCliBackend(settings.qwen3_tts_command)
    if backend_name == "chatterbox_cli":
        return ChatterboxCliBackend(settings.chatterbox_command)
    raise RuntimeError(f"Unknown backend: {backend_name}")


def list_backends() -> list[BackendSpec]:
    return [
        BackendSpec(
            name="passthrough",
            label=PassthroughBackend.label,
            mode=PassthroughBackend.mode,
            description=PassthroughBackend.description,
            configured=True,
        ),
        BackendSpec(
            name="seed_vc_cli",
            label=SeedVcCliBackend.label,
            mode=SeedVcCliBackend.mode,
            description=SeedVcCliBackend.description,
            configured=bool(settings.seed_vc_command),
        ),
        BackendSpec(
            name="cosyvoice3_builtin",
            label=CosyVoice3BuiltinBackend.label,
            mode=CosyVoice3BuiltinBackend.mode,
            description=CosyVoice3BuiltinBackend.description,
            configured=_is_cosyvoice_ready(),
        ),
        BackendSpec(
            name="cosyvoice3_cli",
            label=CosyVoice3CliBackend.label,
            mode=CosyVoice3CliBackend.mode,
            description=CosyVoice3CliBackend.description,
            configured=bool(settings.cosyvoice3_command),
        ),
        BackendSpec(
            name="qwen3_tts_cli",
            label=Qwen3TtsCliBackend.label,
            mode=Qwen3TtsCliBackend.mode,
            description=Qwen3TtsCliBackend.description,
            configured=bool(settings.qwen3_tts_command),
        ),
        BackendSpec(
            name="chatterbox_cli",
            label=ChatterboxCliBackend.label,
            mode=ChatterboxCliBackend.mode,
            description=ChatterboxCliBackend.description,
            configured=bool(settings.chatterbox_command),
        ),
    ]


_COSYVOICE_MODEL = None


def _assert_cosyvoice_ready() -> None:
    if not settings.cosyvoice_repo_dir.exists():
        raise RuntimeError(
            f"CosyVoice repo not found: {settings.cosyvoice_repo_dir}. "
            "Clone the official CosyVoice repo into external/CosyVoice."
        )
    if not settings.cosyvoice3_model_dir.exists():
        raise RuntimeError(
            f"CosyVoice3 model not found: {settings.cosyvoice3_model_dir}. "
            "Download it from the WebUI Model Download tab first."
        )


def _is_cosyvoice_ready() -> bool:
    return settings.cosyvoice_repo_dir.exists() and settings.cosyvoice3_model_dir.exists()


def _load_cosyvoice_model():
    global _COSYVOICE_MODEL
    if _COSYVOICE_MODEL is not None:
        return _COSYVOICE_MODEL

    _assert_cosyvoice_ready()
    repo_dir = settings.cosyvoice_repo_dir.resolve()
    matcha_dir = repo_dir / "third_party" / "Matcha-TTS"
    for path in (repo_dir, matcha_dir):
        if path.exists():
            sys.path.insert(0, str(path))

    from cosyvoice.cli.cosyvoice import AutoModel

    _COSYVOICE_MODEL = AutoModel(model_dir=str(settings.cosyvoice3_model_dir))
    return _COSYVOICE_MODEL


def backend_choices(mode: str) -> list[tuple[str, str]]:
    return [
        (f"{spec.label}{'' if spec.configured else '（未配置）'}", spec.name)
        for spec in list_backends()
        if spec.mode == mode
    ]
