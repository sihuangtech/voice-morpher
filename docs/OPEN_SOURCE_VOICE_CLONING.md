# 开源语音克隆项目调研

本文档整理适合接入 Voice Morpher 的主流开源语音克隆、TTS 克隆和音色转换项目。这里的“语音克隆”分两类：

- **TTS 声音克隆**：参考音频 + 文本 -> 用参考音色生成新语音。
- **Voice Conversion 音色转换**：源音频 + 目标参考音频 -> 尽量保留源音频内容、节奏和语气，只换目标音色。

## 快速结论

| 项目 | 类型 | 适合程度 | Mac 本地友好度 | 许可/商用风险 | 本项目建议 |
| --- | --- | --- | --- | --- | --- |
| Qwen3 TTS / MLX | TTS 克隆 | 高 | 高 | 需按模型页确认 | Apple Silicon 优先候选 |
| CosyVoice3 | TTS 克隆 | 高 | 中 | Apache-2.0 模型页优先确认 | 中文/多语言高质量候选 |
| Chatterbox | TTS 克隆 | 高 | 中 | MIT | 产品功能候选 |
| OpenVoice V2 | TTS 克隆 | 中高 | 中 | MIT | 轻量商用友好兜底 |
| F5-TTS | TTS 克隆 | 中高 | 中 | 预训练权重 CC-BY-NC | 非商业 Demo / 对比 |
| IndexTTS-2 | TTS 克隆 | 中高 | 中低 | 需重点确认 | 中文表达候选 |
| XTTS v2 | TTS 克隆 | 中 | 中 | Coqui Public Model License | 经典对照，不建议默认商用 |
| Fish Speech / Fish Audio S2 | TTS 克隆 | 高 | 中低 | 需确认具体权重 | 后续高质量候选 |
| Seed-VC | 音色转换 | 高 | 中 | 需确认权重许可 | audio-to-audio 主线 |

## 推荐接入顺序

1. **Qwen3 TTS / MLX**  
   优先服务 Mac M 系列用户。适合把“音色克隆”做成开箱即用体验。

2. **CosyVoice3**  
   适合中文、多语言、高质量 zero-shot TTS 克隆。集成复杂度比 Qwen3/MLX 高，但质量值得保留。

3. **Chatterbox**  
   MIT 许可，产品功能友好，适合做 TTS 克隆候选。

4. **OpenVoice V2**  
   轻量、MIT、跨语言，适合作为商用友好兜底模型。

5. **F5-TTS / IndexTTS-2 / XTTS v2 / Fish Speech**  
   可进入下载清单和 CLI 后端，但默认使用前需要明确许可、硬件和安装路径。

## 项目说明

### Qwen3 TTS / MLX

**定位**：Apple Silicon 友好的 TTS 声音克隆方案。

**特点**：

- MLX 生态对 Mac M1/M2/M3/M4 更友好。
- 支持使用参考音频和参考文本做 voice cloning。
- 适合本项目的“音色克隆 + 文本配音”流程。

**风险**：

- 不同 MLX 转换仓库和模型权重的许可、参数规模、API 可能不同。
- 需要为本项目选择一个稳定运行时作为内置后端。

**接入建议**：

- 在 `config/models.toml` 保留 0.6B 和 1.7B 8-bit 两档。
- 后续优先实现 `qwen3_tts_builtin`。

来源：

- <https://github.com/Blaizzy/mlx-audio>
- <https://github.com/odiak/Qwen3-TTS-MLX>
- <https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16>

### CosyVoice3

**定位**：FunAudioLLM / Alibaba 系列的高质量 multilingual zero-shot TTS。

**特点**：

- 适合中文、多语言和较自然的 TTS 克隆。
- CosyVoice3 论文强调面向 in-the-wild speech generation 的扩展和后训练。
- 模型卡提供 `FunAudioLLM/Fun-CosyVoice3-0.5B-2512`。

**风险**：

- 官方仓库依赖较重，直接内置比 CLI 调用更复杂。
- Mac 本地可跑性要逐机实测。

**接入建议**：

- 保留 `cosyvoice3_builtin` 和 `cosyvoice3_cli`。
- WebUI 音色库保存 `reference.wav + prompt_text`，推理时传给 CosyVoice。

来源：

- <https://github.com/FunAudioLLM/CosyVoice>
- <https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512>
- <https://arxiv.org/abs/2505.17589>

### Chatterbox

**定位**：Resemble AI 开源 TTS / voice cloning 项目。

**特点**：

- MIT 许可。
- 面向 zero-shot voice cloning 和更丰富的表达控制。
- 社区关注度较高，适合产品化探索。

**风险**：

- Mac 本地最优运行路径需要单独验证。
- 与本项目的统一音色库格式需要 wrapper 或内置适配。

**接入建议**：

- 保留下载项和 `chatterbox_cli`。
- 后续可增加 `chatterbox_builtin`。

来源：

- <https://github.com/resemble-ai/chatterbox>
- <https://www.resemble.ai/chatterbox/>

### OpenVoice V2

**定位**：轻量、MIT、跨语言 instant voice cloning。

**特点**：

- OpenVoice README 明确 V1/V2 使用 MIT license。
- 支持 tone color cloning、多语言和跨语言克隆。
- 推理相对轻量，适合作为商用友好兜底。

**风险**：

- 自然度和最新大型 TTS 模型相比可能不是第一梯队。
- 需要确认具体安装依赖在 Mac 上的稳定性。

**接入建议**：

- 保留 `openvoice_cli`。
- 如果用户更重视许可和轻量部署，可优先尝试。

来源：

- <https://github.com/myshell-ai/OpenVoice>
- <https://arxiv.org/abs/2312.01479>

### F5-TTS

**定位**：成熟的 flow matching TTS 克隆项目。

**特点**：

- 社区成熟，有 CLI、Gradio 和大量示例。
- zero-shot TTS 效果好，适合对比和非商业 Demo。
- 官方代码 MIT。

**风险**：

- 官方 README 说明预训练模型因训练数据原因是 CC-BY-NC，商用风险高。

**接入建议**：

- 保留 `f5_tts_cli`。
- README 和 UI 中提示商用前检查许可。

来源：

- <https://github.com/SWivid/F5-TTS>
- <https://arxiv.org/abs/2410.06885>

### IndexTTS / IndexTTS-2

**定位**：中文和情绪表达能力较强的 zero-shot TTS。

**特点**：

- IndexTTS 论文强调自然度、zero-shot voice cloning 和推理效率。
- IndexTTS-2 进一步强调情绪控制和时长控制，适合配音、视频同步、游戏音频。

**风险**：

- 许可和商用边界需要重点确认。
- Mac 本地低门槛程度不如 MLX 路线明确。

**接入建议**：

- 保留 `indextts_cli` 和模型清单项。
- 不作为默认后端，等许可证和运行路径确认后再升优先级。

来源：

- <https://github.com/index-tts/index-tts>
- <https://arxiv.org/abs/2502.05512>
- <https://arxiv.org/abs/2506.21619>

### XTTS v2

**定位**：经典多语言 TTS voice cloning 模型。

**特点**：

- 支持短参考音频的多语言 voice cloning。
- 生态成熟，很多项目用它做 baseline。

**风险**：

- Coqui Public Model License 需要仔细阅读；生产和商用前必须确认限制。
- 质量和效率可能不如新一代模型。

**接入建议**：

- 保留 `xtts_cli` 用于兼容和对照。
- 不建议作为默认商用方案。

来源：

- <https://huggingface.co/coqui/XTTS-v2>

### Fish Speech / Fish Audio S2

**定位**：高质量、多语言、情绪表达 TTS 系列。

**特点**：

- Fish Speech 论文和项目强调多语言、自然度和 voice cloning。
- Fish Audio S2 技术报告提到开源模型权重、微调代码和流式推理引擎。

**风险**：

- 模型规模、推理要求和许可需要按具体版本确认。
- 对 Mac 本地 32GB 内存机器不一定是第一阶段最省心选择。

**接入建议**：

- 作为后续高质量路线候选。
- 等稳定模型 ID、Mac 路径、许可确认后加入 `config/models.toml`。

来源：

- <https://github.com/fishaudio/fish-speech>
- <https://arxiv.org/abs/2411.01156>
- <https://arxiv.org/abs/2603.08823>

### Seed-VC

**定位**：zero-shot voice conversion / singing voice conversion。

**特点**：

- 更适合“已有源音频直接换成目标音色”。
- 与 TTS 克隆不同，它的输入是 source audio + target reference audio。
- 项目提供小模型和离线 VC 模型，适合作为 audio-to-audio 主线。

**风险**：

- 输出路径、依赖、Mac 性能需要实测。
- 与 TTS 音色库的关系要讲清楚：它不是“参考音频 + 文本”的 TTS。

**接入建议**：

- 保留 `seed_vc_cli`。
- 后续写 wrapper 统一输出单个 wav。

来源：

- <https://github.com/Plachtaa/seed-vc>

## 对 Voice Morpher 的产品建议

### WebUI 信息架构

建议保持四个主 Tab：

1. **音色克隆**：保存 reference audio + prompt text，形成可复用 voice profile。
2. **文本克隆配音**：选择 voice profile + 输入文本 + 选择 TTS 后端。
3. **音频换音色**：source audio + target reference audio，调用 Seed-VC 等 VC 后端。
4. **模型下载**：从 `config/models.toml` 管理 Hugging Face / ModelScope 权重。

### 技术优先级

1. 优先做 `qwen3_tts_builtin`，服务 Apple Silicon。
2. 稳定 `cosyvoice3_builtin`，作为高质量中文/多语言后端。
3. 增加 `chatterbox_builtin` 或 wrapper。
4. CLI 方式支持 F5-TTS、OpenVoice、IndexTTS、XTTS。
5. Seed-VC 单独作为 audio-to-audio 后端。

### 许可策略

- MIT / Apache-2.0：优先作为默认候选。
- CC-BY-NC / 自定义模型许可：只作为 Demo 或研究候选，不默认商用。
- 每个模型版本都应在 `config/models.toml` 增加 `license` 字段，后续 WebUI 显示许可风险。
