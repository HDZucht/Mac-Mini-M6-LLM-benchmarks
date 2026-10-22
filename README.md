---
name: Mac-Mini-M6-LLM-benchmarks
version: 1.0.1
license: MIT
author: Argus (Claude Opus 5.5) for Hans-Dieter Zucht
measured_on: Mac mini M6 (Mac18,5), 32 GB, macOS 27.0.1, October 2026
---

# Local LLM speed on a Mac mini M6 (32 GB)

How fast do local language models run on Apple's Mac mini M6 with 32 GB? Decode speed of 16 models in LM Studio, measured by Argus (Claude Opus 5.5) for Hans-Dieter Zucht on 3–4 October 2026, with the raw data and the script. **Update 22 October 2026:** a head-to-head of the two Qwen workhorse models on Splash and Kapitsa, in real-world tasks (next section).

## Update 22 October 2026: head-to-head of the Qwen workhorse models, Splash vs Kapitsa

Head-to-head benchmarking of the two Qwen models we use most, **Qwen3.6-35B-A3B** (mixture of experts, 3B active) and **Qwen3.8-27B** (dense), on the two fastest Apple-silicon frameworks we know of: **[Splash](https://github.com/incoai/splash)** (incoai, DFlash2 speculative decoding) and **[Kapitsa](https://github.com/nace-ai/kapitsa)** (Nace AI, KFlash tree speculative decoding over the same DFlash2 drafters). Same Mac mini M6, same prompts, same scripts.

**Why.** Kapitsa reports the fastest decode in 21 of 24 model and Mac pairs, measured on M1 Pro, M4 Pro, M5 Pro and M5 Max. The Mac mini M6 is the base chip with 12 GPU cores, and our use is scientific work rather than coding agents. Raw speed is one part of it; what counts is the time and the quality of the work a model does: extracting facts from a paper, finding and citing literature with a search tool, answering exam questions.

**Method.**

| Test | What it measures | Settings | Script |
|---|---|---|---|
| Speed | decode tok/s and time to first token on the five prompts of the October table | reasoning off, `max_tokens` 600, temperature 0.7, 3 runs per prompt, median | [`bench_tempo.py`](splash-vs-kapitsa-2026-10-22/bench_tempo.py) |
| Extraction | entities extracted from three in-house biomedical documents (two conference abstracts, one paper on autoantibody panels) into a strict JSON schema; share of list entries that appear verbatim in the source | temperature 0, `json_schema` strict, reasoning off | aggregates in [`data/`](splash-vs-kapitsa-2026-10-22/data/extraction_summary_2026-10-22.json); the documents stay private |
| PubMed agent | five questions with a real PubMed search tool: two citations, one PMID, one invented paper (correct answer: cannot be found), the three newest anti-Ro52 papers in interstitial lung disease; returned PMIDs checked against PubMed | thinking on, temperature 0.6, up to 8 tool rounds | [`bench_tools.py`](splash-vs-kapitsa-2026-10-22/bench_tools.py) |

- **Splash:** the ready-made packages `incoai/Qwen3.6-35B-A3B-Splash` and `incoai/Qwen3.8-27B-Splash` in LM Studio's Splash backend. Speed from the 3 October runs (table below), extraction of the 35B on 15 October, of the 27B on 22 October, PubMed agent of the 27B on 4 October.
- **Kapitsa:** version 0.2.4 (Homebrew `nace-ai/tap/kapitsa`), the catalog builds `35b` and `27b` (MLX affine 4-bit, group 64, each with its MTP head and DFlash2 drafter), 32,768-token context, one model per server. Measured on 22 October 2026, 01:50–04:37, LM Studio idle.

**Results** (bold = better of the pair):

| | 35B, Splash | 35B, Kapitsa | 27B, Splash | 27B, Kapitsa |
|---|---|---|---|---|
| **Decode tok/s** prose DE (Rhine) | 51.5 | **69.3** | **15.3** | 13.5 |
| prose DE (assay) | 59.0 | **75.3** | **17.2** | 14.7 |
| prose EN | 69.6 | **84.1** | **20.2** | 18.2 |
| code | 135.9 | **160.1** | **45.2** | 38.2 |
| JSON | **234.1** | 219.8 | **67.7** | 51.2 |
| Time to first token, median | **0.12 s** | 0.13 s | **0.29 s** | 0.66 s |
| **Extraction** seconds per document | **5.8** | 6.1 | 19.8 | **17.7** |
| entities per document | **40.3** | 33.3 | 32.7 | **58.7** |
| verbatim in source | 88.8 % | **90.2 %** | 87.5 % | **90.9 %** |
| **PubMed agent** time for 5 questions | ¹ | 141 s | **261 s** | 305 s |
| solved of 5 | ¹ | 3.5 | 4 | 4 |

¹ The Splash run of the 35B on 15 October used an LM Studio preset with structured output and thinking off, so the model hardly called the tool. It is left out.

**Conclusion.**

- **Qwen3.6-35B-A3B: Kapitsa writes faster.** Prose and code run 18–35 % faster than with Splash; JSON is 6 % slower. Extraction takes the same time per document (6 s), and the Splash package extracts more entities (40 vs 33).
- **Qwen3.8-27B: Splash writes faster, Kapitsa works better.** Splash decodes 11–32 % faster. Kapitsa's MLX 4-bit build extracts 58.7 entities per document against 32.7 from the Splash package, at the same share of verbatim entries, and finishes each document 2 s sooner. Both builds are MLX affine 4-bit with group size 64, but engine and package differ at once, so this test leaves open whether the broader extraction comes from Kapitsa or from the package.
- **Time per task depends on the model's search behaviour as much as on tok/s.** In the PubMed test the faster engine needed more time when the model searched longer (35B on Kapitsa: 8 rounds for one citation).
- **For this Mac:** Kapitsa with the 35B for fast answers, Kapitsa with the 27B for extraction. Splash stays the choice for the highest decode speed on the 27B.

**Also measured** (details in [`splash-vs-kapitsa-2026-10-22/`](splash-vs-kapitsa-2026-10-22/)):

- **Swift 1.5** (UkisAI's Qwen3.8-27B fine-tune for shorter thinking, `ukisai/Swift-1.5-Qwen3.8-27B-GGUF` Q4_K_M, imported into Kapitsa with the base drafter) against the base model with thinking on, on 40 MMLU-Pro questions (biology, chemistry, health, math, 10 each, seed 1729) and five tasks with checkable answers ([`bench_genau.py`](splash-vs-kapitsa-2026-10-22/bench_genau.py), [`bench_denken.py`](splash-vs-kapitsa-2026-10-22/bench_denken.py)):

  | Qwen3.8-27B variant on Kapitsa | MMLU-Pro correct | tokens per answer, mean | cut off at 8,000 tokens |
  |---|---|---|---|
  | base, default thinking level | 31/40 | 2,448 | 6 |
  | base, `reasoning_effort: low` | **34/40** | **1,204** | 1 |
  | Swift 1.5 | 30/40 | 1,242 | 5 |

  Swift thinks 49 % shorter than the base at its default level, as UkisAI states. The base model with `reasoning_effort: low` thinks as short and answered 34 instead of 30 questions correctly (exact McNemar p = 0.22, so within the noise of 40 questions). All three solved the five tasks 10 of 10. Swift decoded slower than the base on Kapitsa (11–14 tok/s prose), because the borrowed drafter is accepted less often and the import leaves room for 2 slots only.
- **Nemotron 3.5 Bolt 74B-A9B** (NVIDIA's 24 GB build) runs on Kapitsa on this Mac only with `--slots 1`; with the default 3 slots the second request fails with `insufficient memory`. 30–38 tok/s prose, 66 code, 87 JSON; extraction 34.7 entities per document at 81 % verbatim, 22.8 s per document.

**Limits.** One machine, three runs per speed cell, three documents for extraction, five questions for the agent test, 40 for MMLU-Pro. The Splash numbers are 1–19 days older than the Kapitsa numbers and come from LM Studio's Splash backend of early October. Raw data: [`splash-vs-kapitsa-2026-10-22/data/`](splash-vs-kapitsa-2026-10-22/data/) (the speed file holds the generated texts).

These runs heated the voltage regulators of the Mac mini to 95 °C at minimum fan speed. The fan controller that came out of it lives in its own repository: [Mac-mini-M6-fan-control-LLM](https://github.com/HDZucht/Mac-mini-M6-fan-control-LLM).

## Why these benchmarks

> I hope these results help others pick a suitable local model. The test set is shaped by my professional interest: I am a scientist in medical biomarker research, so the prompts are mostly scientific (an immunoassay explanation, antigen and disease extraction to JSON, explanations in German and English). I was looking for a model that is useful for scientific paper work, not only for coding requests.
>
> Please keep in mind how answers were judged. The tables on this page measure **speed**. Where correctness was assessed (the JSON check, the AREX-2 runs), Claude Code compared the answers automatically against fixed reference answers and accepted or rejected them; I did not grade every answer by hand. **Code quality was not a focus** of these tests: the code prompt measures speed only.
>
> — Hans-Dieter Zucht

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

## Recommendation

**Use Splash where it exists.** On this Mac mini M6 the Splash engine (speculative decoding with DFlash2 drafts) gave the highest speed for code and JSON on every model we could compare, and lifted the dense Qwen3.8-27B from 11–19 to 15–68 tok/s. For German prose on the Qwen3.6-35B-A3B mixture-of-experts model the MLX build was faster (63 vs. 52–59 tok/s).

**Splash also speeds up fine-tunes of the same base.** It recognises a model by its architecture, so the Qwen3.8-27B draft accelerated BAAI's AREX-2 (a Qwen3.8 fine-tune) from 7–8 to 22–37 tok/s, and the Qwen3.6 draft makes **Ornith 1.5** 1.4× faster on prose and 2–2.7× on code and JSON than its GGUF. Highly recommended for Ornith; whether the Splash build answers in the same depth as the GGUF has not been measured here.

**How to get there:** Qwen3.8-27B and Qwen3.6-35B-A3B have ready-made Splash packages that LM Studio loads directly. A fine-tune such as AREX-2 runs at full speed today with the standalone server (`splash serve --model <owner/repo-GGUF>:<quant>`). Inside LM Studio it needs its own Splash package (MLX 4-bit target plus the matching draft). Claude Code can build either setup; see [`CLAUDE.md`](CLAUDE.md).

## Limits

One machine, one session per model, three runs per cell; prose quality was not scored in this table. Speeds depend on LM Studio and runtime versions of October 2026. `data/speed_2026-10-03.jsonl` holds 240 runs (16 models × 5 prompts × 3) and one error line for a model removed before it was measured. The AREX-2 figures come from separate agent runs and are not in that file.

## Reproduce

```bash
lms load <model-id> -c 32768          # one model at a time
python3 bench_speed.py <model-id> <label> 3
```

Fan control during long runs: see [Mac-mini-M6-fan-control-LLM](https://github.com/HDZucht/Mac-mini-M6-fan-control-LLM). Provided as is, without warranty (MIT License).
