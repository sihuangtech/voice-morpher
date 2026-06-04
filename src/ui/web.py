from __future__ import annotations

import gradio as gr

from backends import backend_choices
from core.config import settings
from services.model_downloads import download_choices, download_source_choices, model_status_markdown
from services.voice_profiles import voice_profile_choices, voice_profile_status_markdown
from ui.handlers import (
    clone_voice_profile,
    convert_audio,
    download_selected_model,
    model_config_markdown,
    refresh_voice_profile_dropdown,
    synthesize_text,
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
    """构建 Gradio WebUI。这里只放布局，业务逻辑放在 web_handlers.py。"""

    with gr.Blocks(title="Voice Morpher") as demo:
        gr.Markdown("# Voice Morpher\n\n本地 AI 音色转换与语音克隆工具。")
        with gr.Tabs():
            _audio_conversion_tab()
            _tts_clone_tab()
            _voice_profile_tab()
            _model_download_tab()
            with gr.Tab("模型配置"):
                gr.Markdown(model_config_markdown())
    return demo


def _audio_conversion_tab() -> None:
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


def _tts_clone_tab() -> None:
    with gr.Tab("文本克隆配音"):
        gr.Markdown("选择已克隆音色，或手动上传参考音频并输入文本。")
        voice_profile = gr.Dropdown(
            label="已克隆音色",
            choices=voice_profile_choices(),
            value="__upload__",
            interactive=True,
        )
        refresh_voices = gr.Button("刷新音色列表")
        tts_reference = gr.Audio(label="目标人物参考音频", type="filepath")
        tts_prompt_text = gr.Textbox(label="参考音频文本", lines=3)
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
        refresh_voices.click(fn=refresh_voice_profile_dropdown, inputs=[], outputs=[voice_profile])


def _voice_profile_tab() -> None:
    with gr.Tab("音色克隆"):
        gr.Markdown("把目标人物参考音频保存成可复用音色。")
        clone_name = gr.Textbox(label="音色名称", placeholder="例如：旁白男声 / 客服女声 / Alice")
        clone_reference = gr.Audio(label="目标人物参考音频", type="filepath")
        clone_prompt_text = gr.Textbox(label="参考音频文本", lines=4)
        clone_button = gr.Button("保存音色", variant="primary")
        clone_status = gr.Markdown(voice_profile_status_markdown())
        clone_button.click(
            fn=clone_voice_profile,
            inputs=[clone_name, clone_reference, clone_prompt_text],
            outputs=[clone_status],
        )


def _model_download_tab() -> None:
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
        refresh_button.click(fn=model_status_markdown, inputs=[], outputs=[download_status])


def main() -> None:
    app = build_app()
    app.launch(server_name=settings.host, server_port=settings.port, css=CSS)
