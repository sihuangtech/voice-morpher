from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf


SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac"}


@dataclass(frozen=True)
class AudioInfo:
    path: Path
    sample_rate: int
    duration_seconds: float
    channels: int


def assert_supported_audio(path: Path) -> None:
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Unsupported audio format '{path.suffix}'. Supported: {supported}")


def probe_audio(path: Path) -> AudioInfo:
    assert_supported_audio(path)
    info = sf.info(path)
    return AudioInfo(
        path=path,
        sample_rate=info.samplerate,
        duration_seconds=float(info.duration),
        channels=info.channels,
    )


def preprocess_audio(input_path: Path, output_path: Path, sample_rate: int) -> AudioInfo:
    assert_supported_audio(input_path)
    audio, _ = librosa.load(input_path, sr=sample_rate, mono=True)
    audio = _peak_normalize(audio)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output_path, audio, sample_rate, subtype="PCM_16")
    return probe_audio(output_path)


def _peak_normalize(audio: np.ndarray) -> np.ndarray:
    if audio.size == 0:
        return audio
    peak = float(np.max(np.abs(audio)))
    if peak <= 1e-8:
        return audio
    return (audio / peak * 0.95).astype(np.float32)
