from __future__ import annotations

# 兼容聚合模块：业务代码统一从这里导入后端能力。
# 具体实现已拆到 backend_base / backend_cli / backend_cosyvoice / backend_registry。

from backends.base import BackendSpec, ConversionRequest, VoiceBackend
from backends.registry import backend_choices, get_backend, list_backends

__all__ = [
    "BackendSpec",
    "ConversionRequest",
    "VoiceBackend",
    "backend_choices",
    "get_backend",
    "list_backends",
]
