# Voice Morpher

[中文文档](README.zh.md)

Voice Morpher is a local-first voice conversion and voice cloning MVP for Apple Silicon. It is designed around two related workflows:

- Audio-to-audio voice conversion: source audio + target speaker reference audio -> converted audio that keeps the source rhythm, pauses, and expression as much as possible.
- Text-to-speech voice cloning: target speaker reference audio + text -> generated speech in the target speaker's voice.

The app uses a Gradio WebUI and pluggable CLI model backends, so users can choose different open-source models without rewriting the application code.

## Backends

- `passthrough`: Development backend. It copies the preprocessed source audio to the output so the upload, preprocessing, and playback flow can be tested without a model.
- `seed_vc_cli`: Audio-to-audio voice conversion through an external Seed-VC command.
- `cosyvoice3_cli`: Text-to-speech voice cloning through an external CosyVoice3 command.
- `qwen3_tts_cli`: Apple Silicon-friendly TTS cloning through an external Qwen3 TTS / MLX command.
- `chatterbox_cli`: Lightweight TTS cloning through an external Chatterbox command.

## Install

```bash
uv sync
```

## Run

```bash
uv run voice-morpher
```

Open:

```text
http://127.0.0.1:8000
```

If port `8000` is already in use:

```bash
VOICE_MORPHER_PORT=8001 uv run voice-morpher
```

## Configure Seed-VC

Install and test Seed-VC separately first. Then configure the command template:

```bash
VOICE_MORPHER_SEED_VC_COMMAND='python inference.py --source {source} --target {reference} --output {output}' \
uv run voice-morpher
```

`{source}`, `{reference}`, and `{output}` are replaced with preprocessed wav file paths by this app.

## Configure TTS Cloning Models

CosyVoice3, Qwen3 TTS / MLX, and Chatterbox are TTS backends for:

```text
reference audio + text -> cloned speech
```

Example command templates:

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

Supported placeholders:

- `{source}`: Preprocessed source audio. Used by audio-to-audio backends.
- `{reference}`: Preprocessed target speaker reference audio.
- `{text}`: Input text for TTS cloning.
- `{output}`: Output wav path that the model command must create.

## Configuration File

Copy `.env.example` to `.env` and edit it if you prefer file-based configuration:

```bash
cp .env.example .env
```

## Test

```bash
uv run pytest
uv run ruff check
```

## Technical Design

See [docs/TECHNICAL_DESIGN.md](docs/TECHNICAL_DESIGN.md).
