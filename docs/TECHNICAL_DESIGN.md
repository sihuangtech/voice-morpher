# 本地 AI 音色转换工具技术设计

## 任务判断

本项目的核心输入输出是“源音频 + 目标人物参考音频 -> 保留源音频内容、节奏、停顿和语气，同时替换音色”。这本质上优先属于 voice conversion，而不是传统 TTS。

如果输入是文字并生成目标音色语音，才更适合 zero-shot voice cloning TTS。如果是视频翻译，推荐拆成 ASR/字幕/翻译/TTS/对齐/混音流程，而不是直接做整段音频转换。

## 候选路线

| 路线 | 适合场景 | 优点 | 风险 |
| --- | --- | --- | --- |
| zero-shot voice conversion | 已有音频换音色 | 最能保留源音频节奏、停顿、语气 | 依赖具体 VC 模型，Mac 兼容性需实测 |
| zero-shot voice cloning TTS | 文本配音、视频翻译 | 文本可控、批量生成方便 | 源音频原始语气和节奏会丢失一部分 |
| ASR + TTS | 翻译、字幕配音 | 内容可编辑，可做多语言 | 需要时间戳对齐和韵律重建 |
| 人声分离 + VC | 带背景音乐或环境声的音频 | 可保留背景并替换人声 | 流程更复杂，分离伪影会影响质量 |
| 混合方案 | 长音频、视频、产品化 | 可按片段选择 VC 或 TTS | 工程复杂度最高 |

## MVP 推荐

MVP 推荐使用 zero-shot voice conversion。当前工程把后端做成可插拔：

1. `passthrough`：开发后端，用于跑通上传、预处理、任务目录和下载。
2. `seed_vc_cli`：真实 VC 后端，通过外部 Seed-VC 命令接入。

Seed-VC 当前公开描述支持 zero-shot voice conversion 和 1-30 秒参考音频，模型规模有适合离线转换的轻量版本；它比 ASR + TTS 更贴近“保留源音频节奏和语气”的目标。OpenVoice 和 CosyVoice 更偏 TTS/声音克隆，适合后续文字配音和视频翻译模块。

参考：

- Seed-VC: <https://github.com/Plachtaa/seed-vc>
- OpenVoice: <https://github.com/myshell-ai/OpenVoice>
- CosyVoice: <https://github.com/FunAudioLLM/CosyVoice>

## Apple Silicon 判断

Apple M2 Max 32GB 适合先跑轻量或中等规模模型。工程上应优先选择：

- 支持 CPU 推理，MPS 可选；
- 模型权重小于数 GB；
- 可以独立 CLI 调用；
- 输入输出 wav 明确；
- 不强依赖 CUDA 自定义算子。

效果很好但强依赖 CUDA 或特定 Linux 环境的项目，不适合作为本地 Mac MVP 的第一选择。

## 当前工程流程

1. 用户上传源音频和目标参考音频。
2. 服务校验格式、大小、时长。
3. 使用 `librosa`/`soundfile` 转为 mono 24 kHz wav，并做峰值归一化。
4. 调用配置的转换后端。
5. 保存 `data/jobs/<job_id>/output.wav`。
6. 前端播放并下载结果。

## 后续产品化计划

1. 接入 Seed-VC 本地仓库和权重，完成 Mac CPU/MPS 实测。
2. 增加人声分离、降噪、静音切片和长音频分段。
3. 增加任务队列和进度查询。
4. 增加 ASR 字幕和 CosyVoice/OpenVoice TTS 分支。
5. 增加授权确认、参考音频质量检测和水印/审计记录。
