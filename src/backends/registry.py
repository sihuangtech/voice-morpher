from __future__ import annotations

from backends.base import BackendSpec, VoiceBackend
from backends.cli import (
    ChatterboxCliBackend,
    CosyVoice3CliBackend,
    F5TtsCliBackend,
    IndexTtsCliBackend,
    OpenVoiceCliBackend,
    PassthroughBackend,
    Qwen3TtsCliBackend,
    SeedVcCliBackend,
    XttsCliBackend,
)
from backends.cosyvoice import CosyVoice3BuiltinBackend, is_cosyvoice_ready
from core.config import settings


def get_backend(name: str | None = None) -> VoiceBackend:
    """根据后端名创建后端实例。"""

    backend_name = name or settings.backend
    factories = {
        "passthrough": lambda: PassthroughBackend(),
        "seed_vc_cli": lambda: SeedVcCliBackend(settings.seed_vc_command),
        "cosyvoice3_builtin": lambda: CosyVoice3BuiltinBackend(),
        "cosyvoice3_cli": lambda: CosyVoice3CliBackend(settings.cosyvoice3_command),
        "qwen3_tts_cli": lambda: Qwen3TtsCliBackend(settings.qwen3_tts_command),
        "chatterbox_cli": lambda: ChatterboxCliBackend(settings.chatterbox_command),
        "f5_tts_cli": lambda: F5TtsCliBackend(settings.f5_tts_command),
        "openvoice_cli": lambda: OpenVoiceCliBackend(settings.openvoice_command),
        "indextts_cli": lambda: IndexTtsCliBackend(settings.indextts_command),
        "xtts_cli": lambda: XttsCliBackend(settings.xtts_command),
    }
    try:
        return factories[backend_name]()
    except KeyError as exc:
        raise RuntimeError(f"Unknown backend: {backend_name}") from exc


def list_backends() -> list[BackendSpec]:
    """返回 WebUI 下拉框和状态页需要的后端清单。"""

    return [
        _spec(PassthroughBackend, True),
        _spec(SeedVcCliBackend, bool(settings.seed_vc_command)),
        _spec(CosyVoice3BuiltinBackend, is_cosyvoice_ready()),
        _spec(CosyVoice3CliBackend, bool(settings.cosyvoice3_command)),
        _spec(Qwen3TtsCliBackend, bool(settings.qwen3_tts_command)),
        _spec(ChatterboxCliBackend, bool(settings.chatterbox_command)),
        _spec(F5TtsCliBackend, bool(settings.f5_tts_command)),
        _spec(OpenVoiceCliBackend, bool(settings.openvoice_command)),
        _spec(IndexTtsCliBackend, bool(settings.indextts_command)),
        _spec(XttsCliBackend, bool(settings.xtts_command)),
    ]


def backend_choices(mode: str) -> list[tuple[str, str]]:
    """按任务模式生成 Gradio 下拉框选项。"""

    return [
        (f"{spec.label}{'' if spec.configured else '（未配置）'}", spec.name)
        for spec in list_backends()
        if spec.mode == mode
    ]


def _spec(backend_class: type[VoiceBackend], configured: bool) -> BackendSpec:
    return BackendSpec(
        name=backend_class.name,
        label=backend_class.label,
        mode=backend_class.mode,
        description=backend_class.description,
        configured=configured,
    )
