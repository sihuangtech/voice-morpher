from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VOICE_MORPHER_", env_file=".env")

    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False
    backend: str = "passthrough"
    seed_vc_command: str | None = None
    cosyvoice3_command: str | None = None
    qwen3_tts_command: str | None = None
    chatterbox_command: str | None = None

    data_dir: Path = Field(default=Path("data"))
    max_upload_mb: int = 100
    max_audio_seconds: int = 600
    sample_rate: int = 24_000

    @property
    def job_dir(self) -> Path:
        return self.data_dir / "jobs"


settings = Settings()
