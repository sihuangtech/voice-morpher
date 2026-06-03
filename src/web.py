from __future__ import annotations

from pathlib import Path

import gradio as gr

from backends import backend_choices, list_backends
from config import settings
from jobs import run_audio_to_audio, run_text_to_speech
from model_downloads import (
    download_choices,
    download_model,
    download_source_choices,
    model_status_markdown,
)
from voice_profiles import (
    create_voice_profile,
    voice_profile_choices,
    voice_profile_status_markdown,
)


CSS = """
.model-card {
  border: 1px solid #e5e5e0;
  border-radius: 8px;
  padding: 12px 14px;
  background: #fff;
  margin: 8px 0;
}
.model-card strong { color: #1d1d1f; }
.model-card span { color: #666; }
"""


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Voice Morpher") as demo:
        gr.Markdown(
            """
# Voice Morpher

本地 AI 音色转换与语音克隆工具。模型通过 CLI 后端接入，用户可以按任务选择不同模型。
"""
        )

        with gr.Tabs():
            with gr.Tab("音频换音色"):
                gr.Markdown("适合 Seed-VC：上传源音频和目标参考音频，尽量保留源音频节奏、停顿和语气。")
                with gr.Row():
                    source_audio = gr.Audio(label="源音频", type="filepath")
                    reference_audio = gr.Audio(label="目标人物参考音频", type="filepath")
                audio_backend = gr.Dropdown(
                    label="转换模型",
                    choices=backend_choices("audio_to_audio"),
                    value="passthrough",
                    interactive=True,
                )
                convert_button = gr.Button("开始音色转换", variant="primary")
                audio_output = gr.Audio(label="输出音频", type="filepath")
                audio_status = gr.Markdown()

                convert_button.click(
                    fn=convert_audio,
                    inputs=[source_audio, reference_audio, audio_backend],
                    outputs=[audio_output, audio_status],
                )

            with gr.Tab("文本克隆配音"):
                gr.Markdown("选择已克隆音色，或手动上传参考音频并输入文本。")
                voice_profile = gr.Dropdown(
                    label="已克隆音色",
                    choices=voice_profile_choices(),
                    value="__upload__",
                    interactive=True,
                )
                refresh_voices_for_tts = gr.Button("刷新音色列表")
                tts_reference = gr.Audio(label="目标人物参考音频", type="filepath")
                tts_prompt_text = gr.Textbox(
                    label="参考音频文本",
                    lines=3,
                    placeholder="参考音频里说了什么。CosyVoice3 克隆建议填写；不知道可先留空。",
                )
                tts_text = gr.Textbox(label="要生成的文本", lines=5)
                tts_backend = gr.Dropdown(
                    label="TTS 模型",
                    choices=backend_choices("text_to_speech"),
                    value="cosyvoice3_builtin",
                    interactive=True,
                )
                tts_button = gr.Button("开始生成", variant="primary")
                tts_output = gr.Audio(label="输出音频", type="filepath")
                tts_status = gr.Markdown()

                tts_button.click(
                    fn=synthesize_text,
                    inputs=[voice_profile, tts_reference, tts_prompt_text, tts_text, tts_backend],
                    outputs=[tts_output, tts_status],
                )
                refresh_voices_for_tts.click(
                    fn=refresh_voice_profile_dropdown,
                    inputs=[],
                    outputs=[voice_profile],
                )

            with gr.Tab("音色克隆"):
                gr.Markdown("把目标人物参考音频保存成可复用音色。保存后可在“文本克隆配音”里直接选择。")
                clone_name = gr.Textbox(label="音色名称", placeholder="例如：旁白男声 / 客服女声 / Alice")
                clone_reference = gr.Audio(label="目标人物参考音频", type="filepath")
                clone_prompt_text = gr.Textbox(
                    label="参考音频文本",
                    lines=4,
                    placeholder="参考音频里说的原文。CosyVoice3 推荐填写，音色相似度和稳定性会更好。",
                )
                clone_button = gr.Button("保存音色", variant="primary")
                clone_status = gr.Markdown(voice_profile_status_markdown())

                clone_button.click(
                    fn=clone_voice_profile,
                    inputs=[clone_name, clone_reference, clone_prompt_text],
                    outputs=[clone_status],
                )

            with gr.Tab("模型下载"):
                gr.Markdown("下载模型权重到本地 `models/` 目录。")
                model_choice = gr.Dropdown(
                    label="模型",
                    choices=download_choices(),
                    value="cosyvoice3",
                    interactive=True,
                )
                download_source = gr.Dropdown(
                    label="下载源",
                    choices=download_source_choices(),
                    value="huggingface",
                    interactive=True,
                )
                use_hf_mirror = gr.Checkbox(label="使用 hf-mirror.com", value=False)
                download_button = gr.Button("下载模型", variant="primary")
                refresh_button = gr.Button("刷新状态")
                download_status = gr.Markdown(model_status_markdown())

                download_button.click(
                    fn=download_selected_model,
                    inputs=[model_choice, download_source, use_hf_mirror],
                    outputs=[download_status],
                )
                refresh_button.click(
                    fn=model_status_markdown,
                    inputs=[],
                    outputs=[download_status],
                )

            with gr.Tab("模型配置"):
                gr.Markdown(_model_status_markdown())

    return demo


def convert_audio(source_path: str | None, reference_path: str | None, backend_name: str):
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
    try:
        if not reference_path:
            raise ValueError("请上传目标人物参考音频。")
        profile = create_voice_profile(name, reference_path, prompt_text)
    except Exception as exc:
        return f"保存失败：{exc}\n\n{voice_profile_status_markdown()}"
    return f"已保存音色 `{profile.name}`。\n\n{voice_profile_status_markdown()}"


def refresh_voice_profile_dropdown():
    return gr.update(choices=voice_profile_choices(), value="__upload__")


def download_selected_model(model_key: str, source: str, use_hf_mirror: bool) -> str:
    try:
        message = download_model(model_key, source, use_hf_mirror)
    except Exception as exc:
        return f"下载失败：{exc}\n\n{model_status_markdown()}"
    return f"{message}\n\n{model_status_markdown()}"


def _success_message(job_id: str, output_path: str) -> str:
    return f"完成。Job ID: `{job_id}`，输出文件：`{Path(output_path)}`"


def _model_status_markdown() -> str:
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


def main() -> None:
    app = build_app()
    app.launch(
        server_name=settings.host,
        server_port=settings.port,
        css=CSS,
    )
