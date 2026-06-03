from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from huggingface_hub import snapshot_download

from config import settings


@dataclass(frozen=True)
class ModelDownload:
    key: str
    label: str
    provider: str
    repo_id: str
    local_name: str
    task: str
    description: str

    @property
    def local_dir(self) -> Path:
        return settings.models_dir / self.local_name


def download_choices() -> list[tuple[str, str]]:
    return [(model.label, model.key) for model in load_model_catalog()]


def model_status_markdown() -> str:
    settings.models_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        "| Model | Task | Repository | Local path | Status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for model in load_model_catalog():
        rows.append(
            "| {label} | {task} | `{repo}` | `{path}` | {status} |".format(
                label=model.label,
                task=model.task,
                repo=model.repo_id,
                path=model.local_dir,
                status="Downloaded" if is_downloaded(model.key) else "Missing",
            )
        )
    return "\n".join(rows)


def download_model(model_key: str, use_hf_mirror: bool) -> str:
    model = _get_model(model_key)
    model.local_dir.parent.mkdir(parents=True, exist_ok=True)

    old_endpoint = os.environ.get("HF_ENDPOINT")
    if use_hf_mirror:
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

    try:
        local_path = snapshot_download(
            repo_id=model.repo_id,
            local_dir=str(model.local_dir),
        )
    finally:
        if use_hf_mirror:
            if old_endpoint is None:
                os.environ.pop("HF_ENDPOINT", None)
            else:
                os.environ["HF_ENDPOINT"] = old_endpoint

    return f"Downloaded `{model.label}` to `{local_path}`."


def is_downloaded(model_key: str) -> bool:
    model = _get_model(model_key)
    return model.local_dir.exists() and any(model.local_dir.iterdir())


def load_model_catalog() -> list[ModelDownload]:
    catalog_path = settings.model_catalog_path
    if not catalog_path.exists():
        raise FileNotFoundError(f"Model catalog not found: {catalog_path}")

    with catalog_path.open("rb") as file:
        raw_catalog = tomllib.load(file)

    raw_models = raw_catalog.get("models", [])
    if not isinstance(raw_models, list):
        raise ValueError("Model catalog must define a 'models' list")

    return [_parse_model(raw_model) for raw_model in raw_models]


def _parse_model(raw_model: dict[str, Any]) -> ModelDownload:
    required_fields = {
        "key",
        "label",
        "provider",
        "repo_id",
        "local_name",
        "task",
        "description",
    }
    missing = sorted(required_fields - raw_model.keys())
    if missing:
        raise ValueError(f"Model catalog entry is missing fields: {', '.join(missing)}")

    return ModelDownload(
        key=str(raw_model["key"]),
        label=str(raw_model["label"]),
        provider=str(raw_model["provider"]),
        repo_id=str(raw_model["repo_id"]),
        local_name=str(raw_model["local_name"]),
        task=str(raw_model["task"]),
        description=str(raw_model["description"]),
    )


def _get_model(model_key: str) -> ModelDownload:
    for model in load_model_catalog():
        if model.key == model_key:
            return model
    raise ValueError(f"Unknown model: {model_key}")
