from __future__ import annotations

from pathlib import Path

import gradio as gr

from backends import list_backends
from services.jobs import run_audio_to_audio, run_text_to_speech
from services.model_downloads import (
    download_choices,
    download_model,
    model_status_markdown,
    selected_model_markdown,
)
from services.voice_profiles import (
    create_voice_profile,
    voice_profile_choices,
    voice_profile_status_markdown,
)


def convert_audio(source_path: str | None, reference_path: str | None, backend_name: str):
    """音频换音色按钮回调。"""

    if not source_path or not reference_path:
        return None, "请上传源音频和目标人物参考音频。"
    result = run_audio_to_audio(source_path, reference_path, backend_name)
    if result.status != "completed" or not result.output_path:
        return None, f"转换失败：{result.error}"
    return result.output_path, _success_message(result.job_id, result.output_path)


def synthesize_text(
    voice_profile_key: str,
    reference_path: str | None,
    prompt_text: str,
    text: str,
    backend_name: str,
):
    """文本克隆配音按钮回调。"""

    if voice_profile_key == "__upload__" and not reference_path:
        return None, "请选择已克隆音色，或上传目标人物参考音频。"
    result = run_text_to_speech(
        reference_path,
        text,
        prompt_text,
        backend_name,
        voice_profile_key,
    )
    if result.status != "completed" or not result.output_path:
        return None, f"生成失败：{result.error}"
    return result.output_path, _success_message(result.job_id, result.output_path)


def clone_voice_profile(name: str, reference_path: str | None, prompt_text: str) -> str:
    """把一段参考音频保存为可复用音色。"""

    try:
        if not reference_path:
            raise ValueError("请上传目标人物参考音频。")
        profile = create_voice_profile(name, reference_path, prompt_text)
    except Exception as exc:
        return f"保存失败：{exc}\n\n{voice_profile_status_markdown()}"
    return f"已保存音色 `{profile.name}`。\n\n{voice_profile_status_markdown()}"


def refresh_voice_profile_dropdown():
    """刷新音色下拉框。"""

    return gr.update(choices=voice_profile_choices(), value="__upload__")


def download_selected_model(model_key: str, source: str, use_hf_mirror: bool) -> str:
    """模型下载按钮回调。"""

    try:
        message = download_model(model_key, source, use_hf_mirror)
    except Exception as exc:
        return f"下载失败：{exc}\n\n{model_status_markdown()}"
    return f"{message}\n\n{model_status_markdown()}"


def refresh_model_dropdown():
    """刷新模型下载下拉框。

    Gradio 下拉框选项是在页面构建时生成的；运行中修改 models.toml 后，
    需要点这个按钮才能在当前页面看到新模型。
    """

    choices = download_choices()
    value = choices[0][1] if choices else None
    return gr.update(choices=choices, value=value), selected_model_markdown(value) if value else ""


def show_selected_model(model_key: str) -> str:
    """切换模型时显示下载地址。"""

    return selected_model_markdown(model_key)


def model_config_markdown() -> str:
    """生成模型配置状态页。"""

    cards = []
    for spec in list_backends():
        status = "已配置" if spec.configured else "未配置"
        cards.append(
            f"""
<div class="model-card">
  <strong>{spec.label}</strong> <span>{status}</span><br />
  <span>模式：{spec.mode}</span><br />
  <span>{spec.description}</span>
</div>
"""
        )
    return "\n".join(cards)


def _success_message(job_id: str, output_path: str) -> str:
    return f"完成。Job ID: `{job_id}`，输出文件：`{Path(output_path)}`"
