# Voice Morpher

[English README](README.md)

Voice Morpher 是一个本地优先的 AI 音色转换和语音克隆 MVP，优先考虑 Apple Silicon 本地运行。它支持两类相关但不同的流程：

- 音频换音色：源音频 + 目标人物参考音频 -> 尽量保留源音频的语速、停顿、节奏和表达方式，同时转换成目标音色。
- 文本克隆配音：目标人物参考音频 + 文本 -> 生成目标人物音色的语音。

项目使用 Gradio WebUI 和可插拔 CLI 模型后端，用户可以选择不同开源模型，而不需要改业务代码。

## 后端

- `passthrough`：开发后端，直接输出预处理后的源音频，用于验证上传、预处理和播放流程。
- `seed_vc_cli`：通过外部 Seed-VC 命令接入 audio-to-audio 音色转换。
- `cosyvoice3_cli`：通过外部 CosyVoice3 命令接入文本克隆配音。
- `qwen3_tts_cli`：通过外部 Qwen3 TTS / MLX 命令接入 Apple Silicon 友好的 TTS 克隆。
- `chatterbox_cli`：通过外部 Chatterbox 命令接入轻量 TTS 克隆。

## 安装

```bash
uv sync
```

## 启动

```bash
uv run voice-morpher
```

打开：

```text
http://127.0.0.1:8000
```

如果 `8000` 端口已被占用：

```bash
VOICE_MORPHER_PORT=8001 uv run voice-morpher
```

## 接入 Seed-VC

先在本机单独安装并验证 Seed-VC。然后配置命令模板：

```bash
VOICE_MORPHER_SEED_VC_COMMAND='python inference.py --source {source} --target {reference} --output {output}' \
uv run voice-morpher
```

`{source}`、`{reference}`、`{output}` 会由本项目自动替换成预处理后的 wav 路径。

## 接入 TTS 克隆模型

CosyVoice3、Qwen3 TTS / MLX、Chatterbox 属于 TTS 后端：

```text
参考音频 + 文本 -> 目标音色语音
```

命令模板示例：

```bash
VOICE_MORPHER_COSYVOICE3_COMMAND='python cosyvoice3_infer.py --prompt-audio {reference} --text {text} --output {output}' \
uv run voice-morpher
```

```bash
VOICE_MORPHER_QWEN3_TTS_COMMAND='python qwen3_tts.py --reference {reference} --text {text} --output {output}' \
uv run voice-morpher
```

```bash
VOICE_MORPHER_CHATTERBOX_COMMAND='python chatterbox_tts.py --reference {reference} --text {text} --output {output}' \
uv run voice-morpher
```

命令模板支持这些占位符：

- `{source}`：预处理后的源音频，仅 audio-to-audio 后端使用。
- `{reference}`：预处理后的目标人物参考音频。
- `{text}`：文本克隆配音输入文本。
- `{output}`：模型必须写出的 wav 文件路径。

## 配置文件

如果你更喜欢文件配置，可以复制 `.env.example`：

```bash
cp .env.example .env
```

## 测试

```bash
uv run pytest
uv run ruff check
```

## 技术设计

见 [docs/TECHNICAL_DESIGN.md](docs/TECHNICAL_DESIGN.md)。
