# Voice Morpher

[English README](README.md)

本地优先的语音音色转换和语音克隆工具，带 Gradio WebUI、可插拔模型后端和模型下载管理。

Voice Morpher 优先面向 Apple Silicon 本地 Demo。项目不内置模型权重，也不把应用锁死在某一个模型上，而是在 Seed-VC、CosyVoice3、Qwen3 TTS / MLX、Chatterbox、F5-TTS、OpenVoice、IndexTTS、XTTS 等开源语音模型之上提供一层轻量应用。

## 功能

- 将源音频转换成目标人物音色，并尽量保留源音频的语速、停顿和节奏。
- 根据目标人物参考音频和文本生成克隆语音。
- 在 WebUI 中下载支持的 Hugging Face 或 ModelScope 模型快照。
- 在 WebUI 中把参考音频保存成可复用音色。
- 优先使用 WebUI 内置流程，命令模板后端保留给高级自定义环境。
- 将运行数据、外部模型仓库和下载权重放在源码目录之外。

## 当前状态

这是一个 MVP。应用流程、音频预处理、Gradio 界面、音色库、模型清单、模型下载管理和后端适配已经实现。

默认的 `passthrough` 后端不依赖任何模型。它会把预处理后的源音频直接复制成输出，用于在安装真实模型前测试 UI 和流程。

## 支持的流程

| 流程 | 输入 | 输出 | 推荐后端 |
| --- | --- | --- | --- |
| 音频换音色 | 源音频 + 目标参考音频 | 转换后的音频 | `seed_vc_cli` |
| 文本克隆配音 | 目标参考音频 + 文本 | 生成语音 | `cosyvoice3_builtin`, `cosyvoice3_cli`, `qwen3_tts_cli`, `chatterbox_cli`, `f5_tts_cli`, `openvoice_cli`, `indextts_cli`, `xtts_cli` |
| 流程测试 | 源音频 + 目标参考音频 | 复制源音频 | `passthrough` |

## 支持的模型系列

| 模型系列 | 集成状态 | 说明 |
| --- | --- | --- |
| Qwen3 TTS / MLX | 下载清单 + CLI 后端 | Apple Silicon 优先候选。 |
| CosyVoice3 | 下载清单 + 内置后端 + CLI 后端 | 内置后端需要本地已有官方 CosyVoice Python 包。 |
| Chatterbox | 下载清单 + CLI 后端 | 开源 TTS 声音克隆，支持更丰富表达控制。 |
| F5-TTS | 下载清单 + CLI 后端 | 成熟 zero-shot TTS；商用前需要确认模型许可。 |
| OpenVoice V2 | 下载清单 + CLI 后端 | 轻量、MIT 许可的声音克隆候选。 |
| IndexTTS-2 | 下载清单 + CLI 后端 | 当前公开权重。IndexTTS-2.5 已有技术报告，但这里暂未配置官方可下载权重。 |
| XTTS v2 | 下载清单 + CLI 后端 | 经典多语言声音克隆模型；生产使用前需要确认许可。 |
| Seed-VC | CLI 后端 | audio-to-audio 音色转换，不是 TTS。 |

CLI 后端表示 WebUI 可以通过配置命令模板调用该模型，不表示本仓库内置第三方模型运行环境。

## 环境要求

- macOS、Linux 或 Windows
- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- 可选：Seed-VC、CosyVoice3、Qwen3 TTS / MLX、Chatterbox 各自需要的运行环境

应用本身是模型无关的，但本地运行优先考虑 Apple Silicon。

## 快速开始

```bash
uv sync
uv run python main.py
```

打开：

```text
http://127.0.0.1:8000
```

如果 `8000` 端口已被占用：

```bash
VOICE_MORPHER_PORT=8001 uv run python main.py
```

## WebUI

Gradio 界面包含：

- **音频换音色**：上传源音频和目标人物参考音频。
- **音色克隆**：把目标人物参考音频保存成可复用音色。
- **文本克隆配音**：上传目标人物参考音频并输入文本。
- **模型下载**：把配置好的 Hugging Face 或 ModelScope 模型快照下载到 `models/`。
- **模型配置**：查看 CLI 后端是否已配置。

## 模型清单

可下载模型的元数据放在：

```text
config/models.toml
```

新增或修改模型时，改这个文本配置文件即可，不需要改 Python 代码。每个条目包含界面名称、Hugging Face 仓库、本地目录名、任务类型和描述。

下载后的模型权重放在：

```text
models/
```

`models/` 已加入 `.gitignore`。

例如 CosyVoice3 会下载到：

```text
models/Fun-CosyVoice3-0.5B-2512/
```

WebUI 中可以选择下载源。Hugging Face 对所有已配置模型可用；ModelScope 只有在模型条目里配置了 `modelscope_id` 时可用。

内置 CosyVoice3 后端仍然会检查本地是否存在官方 CosyVoice 仓库：

```text
external/CosyVoice/
models/Fun-CosyVoice3-0.5B-2512/
```

本项目不再负责克隆仓库。要使用内置 CosyVoice3 后端，请你手动安装官方 CosyVoice 仓库。

## 后端配置

如果你更喜欢用配置文件，可以复制：

```bash
cp .env.example .env
```

命令模板支持这些占位符：

- `{source}`：预处理后的源音频路径。
- `{reference}`：预处理后的目标人物参考音频路径。
- `{text}`：文本克隆配音输入文本。
- `{output}`：后端命令必须生成的 wav 输出路径。

### Seed-VC

先单独安装并测试 Seed-VC，然后配置：

```bash
VOICE_MORPHER_SEED_VC_COMMAND='python inference.py --source {source} --target {reference} --output {output}' \
uv run python main.py
```

如果 Seed-VC 的 CLI 输出目录而不是单个 wav 文件，后续需要加一个 wrapper 适配。

### CosyVoice3

推荐的应用流程：

1. 在 **音色克隆** 中保存一个音色。
2. 在 **模型下载** 中下载 CosyVoice3 模型。
3. 手动把官方 CosyVoice 仓库安装到 `external/CosyVoice`。
4. 打开 **文本克隆配音**，选择保存好的音色，并选择 `CosyVoice3 Built-in`。

命令模板后端仍然保留，适合自定义环境：

```bash
VOICE_MORPHER_COSYVOICE3_COMMAND='python cosyvoice3_infer.py --prompt-audio {reference} --text {text} --output {output}' \
uv run python main.py
```

### Qwen3 TTS / MLX

```bash
VOICE_MORPHER_QWEN3_TTS_COMMAND='python qwen3_tts.py --reference {reference} --text {text} --output {output}' \
uv run python main.py
```

### Chatterbox

```bash
VOICE_MORPHER_CHATTERBOX_COMMAND='python chatterbox_tts.py --reference {reference} --text {text} --output {output}' \
uv run python main.py
```

### F5-TTS

```bash
VOICE_MORPHER_F5_TTS_COMMAND='f5-tts_infer-cli --ref_audio {reference} --ref_text {prompt_text} --gen_text {text} --output_file {output}' \
uv run python main.py
```

### OpenVoice V2

```bash
VOICE_MORPHER_OPENVOICE_COMMAND='python openvoice_infer.py --reference {reference} --text {text} --output {output}' \
uv run python main.py
```

### IndexTTS

```bash
VOICE_MORPHER_INDEXTTS_COMMAND='python indextts_infer.py --reference {reference} --text {text} --output {output}' \
uv run python main.py
```

### XTTS v2

```bash
VOICE_MORPHER_XTTS_COMMAND='python xtts_infer.py --speaker_wav {reference} --text {text} --output {output}' \
uv run python main.py
```

## 项目结构

```text
.
├── config/
│   └── models.toml
├── docs/
│   └── TECHNICAL_DESIGN.md
├── src/
│   ├── backends/
│   ├── core/
│   ├── services/
│   └── ui/
├── tests/
├── .env.example
├── README.md
└── README.zh.md
```

## 开发

```bash
uv run ruff check
uv run pytest
```

## 路线图

- 为常见 Seed-VC 输出目录结构增加 wrapper。
- 增加外部模型仓库安装助手。
- 为长时间下载和推理增加后台任务与进度显示。
- 增加模型本地文件校验。
- 增加长音频切片、静音处理和人声分离。
- 增加 ASR + TTS 视频翻译流程。

## 安全说明

请只处理你拥有或已获得授权的声音。本项目目前不包含授权校验、水印或滥用检测。公开发布或商业化前，需要补齐这些控制。

## 许可证

当前还未选择许可证。公开发布仓库前请先添加 license。

## 技术设计

见 [docs/TECHNICAL_DESIGN.md](docs/TECHNICAL_DESIGN.md)。

开源语音克隆模型调研见 [docs/OPEN_SOURCE_VOICE_CLONING.md](docs/OPEN_SOURCE_VOICE_CLONING.md)。
