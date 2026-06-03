# Voice Morpher

[中文文档](README.zh.md)

Local-first voice conversion and voice cloning toolkit with a Gradio WebUI, pluggable model backends, and model download management.

Voice Morpher is built for local demos on Apple Silicon first. It does not bundle model weights or lock the app to one model. Instead, it provides a small application layer around open-source speech models such as Seed-VC, CosyVoice3, Qwen3 TTS / MLX, and Chatterbox.

## What It Does

- Convert source audio into a target speaker's timbre while preserving source rhythm and pauses as much as possible.
- Generate cloned speech from text and a target speaker reference audio.
- Download supported Hugging Face model snapshots from the WebUI.
- Configure model backends through command templates instead of changing application code.
- Keep runtime data, external model repos, and downloaded weights outside the source tree.

## Current Status

This is an MVP. The application flow, audio preprocessing, Gradio interface, model catalog, and CLI backend adapters are implemented. Real model inference depends on installing the target model projects separately and wiring their commands through environment variables.

The default `passthrough` backend is intentionally model-free. It copies the preprocessed source audio to the output so the UI and pipeline can be tested before installing any model.

## Supported Workflows

| Workflow | Input | Output | Recommended backend |
| --- | --- | --- | --- |
| Voice conversion | Source audio + target reference audio | Converted audio | `seed_vc_cli` |
| TTS voice cloning | Target reference audio + text | Generated speech | `cosyvoice3_cli`, `qwen3_tts_cli`, `chatterbox_cli` |
| Pipeline test | Source audio + target reference audio | Copied source audio | `passthrough` |

## Requirements

- macOS, Linux, or Windows
- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Optional model-specific runtimes for Seed-VC, CosyVoice3, Qwen3 TTS / MLX, or Chatterbox

Apple Silicon is the primary local target, but the app itself is model-agnostic.

## Quick Start

```bash
uv sync
uv run python main.py
```

Open:

```text
http://127.0.0.1:8000
```

If port `8000` is already in use:

```bash
VOICE_MORPHER_PORT=8001 uv run python main.py
```

## WebUI

The Gradio interface includes:

- **Audio Voice Conversion**: upload source audio and target reference audio.
- **Text Voice Cloning**: upload target reference audio and enter text.
- **Model Download**: download configured Hugging Face snapshots into `models/`.
- **Model Configuration**: inspect configured and missing CLI backends.

## Model Catalog

Downloadable model metadata is stored in:

```text
config/models.toml
```

Add or edit entries there instead of editing Python code. Each entry defines the display label, Hugging Face repo, local directory name, task, and description.

Downloaded weights are stored under:

```text
models/
```

`models/` is ignored by git.

## Backend Configuration

Copy the example env file if you prefer file-based configuration:

```bash
cp .env.example .env
```

Command templates support these placeholders:

- `{source}`: preprocessed source audio path.
- `{reference}`: preprocessed target speaker reference audio path.
- `{text}`: input text for TTS voice cloning.
- `{output}`: output wav path that the backend command must create.

### Seed-VC

Install and test Seed-VC separately first, then configure:

```bash
VOICE_MORPHER_SEED_VC_COMMAND='python inference.py --source {source} --target {reference} --output {output}' \
uv run python main.py
```

Seed-VC may require a wrapper if its CLI writes to an output directory instead of a single wav file.

### CosyVoice3

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

## Project Layout

```text
.
├── config/
│   └── models.toml
├── docs/
│   └── TECHNICAL_DESIGN.md
├── src/
│   ├── audio.py
│   ├── backends.py
│   ├── cli.py
│   ├── config.py
│   ├── jobs.py
│   ├── model_downloads.py
│   └── web.py
├── tests/
├── .env.example
├── README.md
└── README.zh.md
```

## Development

```bash
uv run ruff check
uv run pytest
```

## Roadmap

- Add wrappers for common Seed-VC output layouts.
- Add install helpers for external model repositories.
- Add background jobs and progress reporting for long downloads and inference.
- Add model-specific validation for required local files.
- Add long-audio slicing, silence handling, and vocal separation.
- Add ASR + TTS workflow for video translation.

## Safety

Only use voices you own or are authorized to process. This project does not include consent verification, watermarking, or misuse detection. Add those controls before any public or commercial deployment.

## License

No license has been selected yet. Add a license before publishing this repository publicly.

## Technical Design

See [docs/TECHNICAL_DESIGN.md](docs/TECHNICAL_DESIGN.md).
