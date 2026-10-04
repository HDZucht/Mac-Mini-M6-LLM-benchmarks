---
name: Mac-Mini-M6-LLM-benchmarks
version: 1.0.0
license: MIT
author: Argus (Claude Opus 5.5) for Hans-Dieter Zucht
measured_on: Mac mini M6 (Mac18,5), 32 GB, macOS 27.0.1, October 2026
---

# Local LLM speed on a Mac mini M6 (32 GB)

How fast do local language models run on Apple's Mac mini M6 with 32 GB? Decode speed of 16 models in LM Studio, measured by Argus (Claude Opus 5.5) for Hans-Dieter Zucht on 3–4 October 2026, with the raw data and the script.

These runs heated the voltage regulators of the Mac mini to 95 °C at minimum fan speed. The fan controller that came out of it lives in its own repository: [Mac-mini-M6-fan-control-LLM](https://github.com/HDZucht/Mac-mini-M6-fan-control-LLM).

## Hardware

| Part | Model | Link (as reported by macOS) | Role in these runs |
|---|---|---|---|
| Computer | Apple **Mac mini M6** (Mac18,5) | | |
| Chip | Apple M6: 12 CPU cores (2 Super, 4 Performance, 6 Efficiency), 12 GPU cores, Metal 4 | | inference |
| Memory | **32 GB** unified memory | | holds the loaded model and its context |
| Internal SSD | Apple 512 GB | | system |
| External SSD | **ORICO 2 TB** NVMe in an ASMedia ASM246x enclosure | 40 Gb/s, PCIe 4.0 x4 | **model storage** (all models load from here) |
| External SSD | **Samsung SSD 9100 PRO 1 TB** NVMe | PCIe 4.0 x4 | additional storage, not involved in these runs |
| Dock | **UGREEN Thunderbolt 5 docking station, 10-in-1** (macOS name: *TBT5 Docking Station 10-in-1*) | 40 Gb/s: the Mac mini's port runs it at Thunderbolt 4 speed | port expansion |

Load times depend on the SSD link; decode speed, the subject of this page, depends on the chip and its memory bandwidth once a model is loaded.

## Setup

- **Machine:** see *Hardware* below; macOS 27.0.1.
- **Server:** LM Studio (OpenAI-compatible API), runtimes llama.cpp (GGUF), MLX and the Splash engine (speculative decoding with DFlash2 drafts).
- **Method:** [`bench_speed.py`](bench_speed.py), raw results in [`data/`](data/) (one JSON line per run, including the generated text). Each model loaded alone with a 32,768-token context (MLX builds ignored the context setting and loaded 34k to 165k), reasoning off, `max_tokens` 600, `temperature` 0.7, 3 runs per prompt, value = median decode speed in tokens per second.
- **Prompts:** two German explanations (Rhine geology, bead-based immunoassay), one English (Ruhr area economy), one Python function, one JSON extraction. The JSON answer was correct in 3 of 3 runs for every model except where noted.
- **Fan:** Apple's automatic control; fanguard did not exist yet. Temperatures were not logged during these runs.

## Decode speed (tokens/s, median of 3)

| Model | Type | Format | Prose DE (Rhine) | Prose DE (assay) | Prose EN | Code | JSON |
|---|---|---|---|---|---|---|---|
| qwen3.6-35b-a3b-splash | MoE, 3B active | Splash | 51.5 | 59.0 | 69.6 | 135.9 | **234.1** |
| ornith-1.5-35b-a3b-splash | MoE, 3B active | Splash | 52.6 | 59.7 | 61.5 | 119.9 | 142.6 |
| qwen/qwen3.6-35b-a3b | MoE, 3B active | MLX 4-bit | 63.2 | 63.8 | 63.8 | 64.0 | 68.8 |
| google/gemma-4-26b-a4b-qat | MoE, 4B active | QAT | 46.5 | 45.5 | 48.2 | 47.8 | 53.3 |
| nemotron-3.5-lightning (lmstudio-community) | MoE, 3B active | GGUF Q4_K_M | 45.6 | 45.2 | 45.1 | 44.9 | 45.0 |
| nvidia/nemotron-3-nano-omni | MoE, 3B active | | 45.0 | 45.1 | 45.0 | 45.0 | 45.9 |
| openai/gpt-oss-20b | MoE, 3.6B active | | 44.7 | 45.3 | 45.2 | 44.9 | 53.3 |
| nemotron-3.5-lightning (unsloth) | MoE, 3B active | GGUF UD-Q3_K_XL | 42.3 | 42.2 | 42.3 | 42.4 | 42.5 |
| ornith-1.5-35b-a3b | MoE, 3B active | GGUF Q4_K_M | 37.6 | 41.2 | 43.7 | 59.3 | 53.8 |
| qwen3.5-9b | dense 9B | MLX | 30.6 | 30.8 | 30.3 | 30.1 | 30.3 ¹ |
| google/gemma-4-12b-qat | dense 12B | QAT | 18.2 | 18.5 | 18.8 | 18.0 | 18.2 |
| qwen3.8-27b-splash | dense 27B | Splash | 15.3 | 17.2 | 20.2 | 45.2 | 67.7 |
| swift-qwen3.8-27b-splash | dense 27B | Splash | 15.4 | 15.9 | 19.5 | 42.9 | 66.5 |
| qwen/qwen3.8-27b | dense 27B | GGUF Q4_K_M | 11.2 | 11.4 | 11.8 | 17.5 | 19.3 |
| meta/muse-glimmer | | | 8.7 | 8.7 | 8.6 | 8.6 | 8.6 ¹ |
| google/gemma-4-31b-qat | dense 31B | QAT | 7.4 | 7.4 | 7.5 | 7.6 | 7.7 |

¹ JSON 0 of 3: the model reasons inside its answer and did not finish within 600 tokens.

## What the table shows

- **Four mixture-of-experts models with 3–4 B active parameters run at 42–53 tok/s whatever the text** (Nemotron 3.5 Lightning, Nemotron 3 Nano Omni, gpt-oss-20b, Gemma 4 26B-A4B), most likely limited by memory bandwidth. The MLX build of Qwen3.6-35B-A3B is faster at 63–69 tok/s.
- **Speculative decoding (Splash) pays off most on predictable text:** JSON and code run 2–3.5× faster than the same model without it. Prose runs at 0.8–1.7×: Qwen3.6 Splash is slower on German prose than its MLX build (0.8–0.9×) and slightly faster on English (1.1×), Ornith Splash is 1.4× its GGUF, Qwen3.8-27B Splash 1.4–1.7× its GGUF.
- **Dense 27B–31B models are slow on 32 GB:** 7–20 tok/s for prose. With Splash, Qwen3.8-27B reaches 45–68 tok/s on code and JSON.

## BAAI AREX-2 (dense 27B, Qwen3.8 fine-tune), 4 October 2026

The model behind the 94.9 °C reading that led to the fan controller. Agent-style runs with a PubMed search tool, thinking on (the model's chat template forces it).

| Engine | Decode tok/s |
|---|---|
| LM Studio, llama.cpp, GGUF Q4_K_M | 6.8–8.0 |
| Splash 1.2.0 standalone, same GGUF + Qwen3.8-27B DFlash2 draft (selected automatically) | **22–37** |

Splash recognises fine-tunes by architecture, so the Qwen3.8-27B draft speeds up AREX-2 three- to fivefold although it was trained for the base model.

## Limits

One machine, one session per model, three runs per cell; prose quality was not scored in this table. Speeds depend on LM Studio and runtime versions of October 2026. `data/speed_2026-10-03.jsonl` holds 240 runs (16 models × 5 prompts × 3) and one error line for a model removed before it was measured. The AREX-2 figures come from separate agent runs and are not in that file.

## Reproduce

```bash
lms load <model-id> -c 32768          # one model at a time
python3 bench_speed.py <model-id> <label> 3
```

Fan control during long runs: see [Mac-mini-M6-fan-control-LLM](https://github.com/HDZucht/Mac-mini-M6-fan-control-LLM). Provided as is, without warranty (MIT License).
