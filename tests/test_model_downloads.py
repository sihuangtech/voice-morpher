from __future__ import annotations

from model_downloads import load_model_catalog


def test_model_catalog_loads_from_toml():
    models = load_model_catalog()

    assert models
    assert {model.key for model in models} >= {
        "cosyvoice3",
        "qwen3_tts_06b_mlx",
        "qwen3_tts_17b_mlx_8bit",
    }
    assert next(model for model in models if model.key == "cosyvoice3").modelscope_id
