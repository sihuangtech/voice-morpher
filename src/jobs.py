from __future__ import annotations

import shutil
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from audio import preprocess_audio, probe_audio
from backends import ConversionRequest, get_backend
from config import settings
from voice_profiles import get_voice_profile


@dataclass
class JobResult:
    job_id: str
    status: str
    source_duration_seconds: float
    reference_duration_seconds: float
    output_path: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_audio_to_audio(source_path: str, reference_path: str, backend_name: str) -> JobResult:
    job_id = uuid.uuid4().hex
    job_path = settings.job_dir / job_id
    raw_path = job_path / "raw"
    work_path = job_path / "work"
    raw_path.mkdir(parents=True, exist_ok=True)
    work_path.mkdir(parents=True, exist_ok=True)

    raw_source = _copy_local_audio(Path(source_path), raw_path / f"source{Path(source_path).suffix}")
    raw_reference = _copy_local_audio(
        Path(reference_path), raw_path / f"reference{Path(reference_path).suffix}"
    )
    return _run_audio_to_audio_paths(raw_source, raw_reference, backend_name, job_id, job_path, work_path)


def run_text_to_speech(
    reference_path: str | None,
    text: str,
    prompt_text: str,
    backend_name: str,
    voice_profile_key: str = "__upload__",
) -> JobResult:
    job_id = uuid.uuid4().hex
    job_path = settings.job_dir / job_id
    raw_path = job_path / "raw"
    work_path = job_path / "work"
    raw_path.mkdir(parents=True, exist_ok=True)
    work_path.mkdir(parents=True, exist_ok=True)

    try:
        if voice_profile_key != "__upload__":
            profile = get_voice_profile(voice_profile_key)
            reference_source = profile.reference_path
            prompt_text = profile.prompt_text
        elif reference_path:
            reference_source = Path(reference_path)
        else:
            raise ValueError("Reference audio or cloned voice profile is required")

        raw_reference = _copy_local_audio(
            reference_source, raw_path / f"reference{reference_source.suffix}"
        )
        if not text.strip():
            raise ValueError("Text is required")
        _validate_audio(raw_reference)

        reference_wav = work_path / "reference.wav"
        reference_info = preprocess_audio(raw_reference, reference_wav, settings.sample_rate)

        output_wav = job_path / "output.wav"
        get_backend(backend_name).convert(
            ConversionRequest(
                output_wav=output_wav,
                reference_wav=reference_wav,
                text=text.strip(),
                prompt_text=prompt_text.strip(),
            )
        )
        return JobResult(
            job_id=job_id,
            status="completed",
            source_duration_seconds=0,
            reference_duration_seconds=reference_info.duration_seconds,
            output_path=str(output_wav),
        )
    except Exception as exc:
        return _failed(job_id, exc)


def get_output_path(job_id: str) -> Path:
    if not job_id.isalnum():
        raise ValueError("Invalid job id")
    output_path = settings.job_dir / job_id / "output.wav"
    if not output_path.exists():
        raise FileNotFoundError(output_path)
    return output_path


def _run_audio_to_audio_paths(
    source_path: Path,
    reference_path: Path,
    backend_name: str | None,
    job_id: str,
    job_path: Path,
    work_path: Path,
) -> JobResult:
    try:
        _validate_audio(source_path)
        _validate_audio(reference_path)

        source_wav = work_path / "source.wav"
        reference_wav = work_path / "reference.wav"
        source_info = preprocess_audio(source_path, source_wav, settings.sample_rate)
        reference_info = preprocess_audio(reference_path, reference_wav, settings.sample_rate)

        output_wav = job_path / "output.wav"
        get_backend(backend_name).convert(
            ConversionRequest(
                output_wav=output_wav,
                source_wav=source_wav,
                reference_wav=reference_wav,
            )
        )
        return JobResult(
            job_id=job_id,
            status="completed",
            source_duration_seconds=source_info.duration_seconds,
            reference_duration_seconds=reference_info.duration_seconds,
            output_path=str(output_wav),
        )
    except Exception as exc:
        return _failed(job_id, exc)


def _failed(job_id: str, exc: Exception) -> JobResult:
    return JobResult(
        job_id=job_id,
        status="failed",
        source_duration_seconds=0,
        reference_duration_seconds=0,
        error=str(exc),
    )


def _copy_local_audio(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return destination


def _validate_audio(path: Path) -> None:
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if path.stat().st_size > max_bytes:
        raise ValueError(f"{path.name} exceeds {settings.max_upload_mb} MB")
    info = probe_audio(path)
    if info.duration_seconds > settings.max_audio_seconds:
        raise ValueError(f"{path.name} exceeds {settings.max_audio_seconds} seconds")
