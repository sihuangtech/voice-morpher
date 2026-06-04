from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from core.audio import preprocess_audio, probe_audio
from core.config import settings


PROFILE_FILE = "profile.json"
REFERENCE_FILE = "reference.wav"


@dataclass(frozen=True)
class VoiceProfile:
    key: str
    name: str
    prompt_text: str
    reference_path: Path
    created_at: str


def create_voice_profile(name: str, reference_path: str, prompt_text: str) -> VoiceProfile:
    profile_name = name.strip()
    if not profile_name:
        raise ValueError("Voice name is required")
    if not reference_path:
        raise ValueError("Reference audio is required")

    key = _slug(profile_name)
    profile_dir = settings.voice_dir / key
    profile_dir.mkdir(parents=True, exist_ok=True)

    output_reference = profile_dir / REFERENCE_FILE
    preprocess_audio(Path(reference_path), output_reference, settings.sample_rate)
    info = probe_audio(output_reference)
    created_at = datetime.now(timezone.utc).isoformat()
    metadata = {
        "key": key,
        "name": profile_name,
        "prompt_text": prompt_text.strip(),
        "reference_path": str(output_reference),
        "created_at": created_at,
        "sample_rate": info.sample_rate,
        "duration_seconds": info.duration_seconds,
    }
    (profile_dir / PROFILE_FILE).write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return VoiceProfile(
        key=key,
        name=profile_name,
        prompt_text=metadata["prompt_text"],
        reference_path=output_reference,
        created_at=created_at,
    )


def list_voice_profiles() -> list[VoiceProfile]:
    if not settings.voice_dir.exists():
        return []

    profiles = []
    for profile_file in sorted(settings.voice_dir.glob(f"*/{PROFILE_FILE}")):
        try:
            raw = json.loads(profile_file.read_text(encoding="utf-8"))
            profile = VoiceProfile(
                key=str(raw["key"]),
                name=str(raw["name"]),
                prompt_text=str(raw.get("prompt_text", "")),
                reference_path=Path(raw["reference_path"]),
                created_at=str(raw.get("created_at", "")),
            )
        except (OSError, KeyError, json.JSONDecodeError):
            continue
        if profile.reference_path.exists():
            profiles.append(profile)
    return profiles


def voice_profile_choices() -> list[tuple[str, str]]:
    return [("手动上传参考音频", "__upload__")] + [
        (profile.name, profile.key) for profile in list_voice_profiles()
    ]


def get_voice_profile(key: str) -> VoiceProfile:
    for profile in list_voice_profiles():
        if profile.key == key:
            return profile
    raise ValueError(f"Unknown voice profile: {key}")


def voice_profile_status_markdown() -> str:
    profiles = list_voice_profiles()
    if not profiles:
        return "还没有克隆音色。上传参考音频并保存后，会出现在这里。"

    rows = [
        "| 音色 | Key | 参考音频 | 创建时间 |",
        "| --- | --- | --- | --- |",
    ]
    for profile in profiles:
        rows.append(
            f"| {profile.name} | `{profile.key}` | `{profile.reference_path}` | {profile.created_at} |"
        )
    return "\n".join(rows)


def _slug(value: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "-", value).strip("-_")
    if not slug:
        raise ValueError("Voice name must contain letters, numbers, Chinese characters, '-' or '_'")
    return slug[:80]
