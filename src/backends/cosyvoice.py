from __future__ import annotations

import sys
from pathlib import Path

import soundfile as sf

from backends.base import ConversionRequest, VoiceBackend
from core.config import settings


class CosyVoice3BuiltinBackend(VoiceBackend):
    """直接调用 CosyVoice Python API 的内置后端。"""

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


_COSYVOICE_MODEL = None


def is_cosyvoice_ready() -> bool:
    """检查内置后端所需的仓库和权重是否存在。"""

    return settings.cosyvoice_repo_dir.exists() and settings.cosyvoice3_model_dir.exists()


def _assert_cosyvoice_ready() -> None:
    if not settings.cosyvoice_repo_dir.exists():
        raise RuntimeError(
            f"CosyVoice repo not found: {settings.cosyvoice_repo_dir}. "
            "Install the official CosyVoice repo under external/CosyVoice."
        )
    if not settings.cosyvoice3_model_dir.exists():
        raise RuntimeError(
            f"CosyVoice3 model not found: {settings.cosyvoice3_model_dir}. "
            "Download it from the WebUI Model Download tab first."
        )


def _load_cosyvoice_model():
    """懒加载 CosyVoice 模型，避免启动 WebUI 时就占用大量内存。"""

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
