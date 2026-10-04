# CLAUDE.md — instructions for Claude Code

This repository holds speed measurements of local LLMs on a Mac mini M6 (32 GB): `README.md` (tables and findings), `bench_speed.py` (the measuring script), `data/` (raw JSON lines).

## Re-running or extending the benchmark

1. LM Studio must serve its OpenAI-compatible API on `localhost:8234` (the script's `URL`); adjust it if the user's port differs. Ask the user to start the server, do not install anything unasked.
2. Load **one model at a time** with a 32k context: `lms unload --all && lms load <model-id> -c 32768 -y`. Check the loaded context with `lms ps`; MLX builds may ignore `-c`, note the real value.
3. `python3 bench_speed.py <model-id> <label> 3` appends to `results.jsonl`. Reasoning is switched off via `reasoning_effort: "none"`; if a model still emits thinking, those tokens count and the note in the README (¹) applies.
4. Report the median decode tok/s per prompt, as in the README table. Keep the existing rows; add new ones with the date.
5. Long runs heat the machine. If the user has the fan controller from [Mac-mini-M6-fan-control-LLM](https://github.com/HDZucht/Mac-mini-M6-fan-control-LLM) installed, suggest `echo 100 > /Users/Shared/mac-fan-guard/mode` for the run and `echo curve > …` afterwards, and log temperatures if you change the method.

## Setting up Splash for a fine-tune

Splash ([incoai/splash](https://github.com/incoai/splash)) pairs a target model with a DFlash2 draft by **architecture**, not by name. Families in Splash 1.2.0 (`install/families.py`): dense Qwen3.8-27B-shaped models (Qwen3.5-27B, Qwen3.6-27B and Qwen3.8-27B share the shape) with the draft `incoai/Qwen3.8-27B-DFlash2`, and Qwen3.6/3.5-35B-A3B-shaped mixture-of-experts models with `incoai/Qwen3.6-35B-A3B-DFlash2`. Fine-tunes of these load; the further a fine-tune drifts from the base, the fewer draft tokens are accepted.

**Path A, standalone server (works with a GGUF, no build):**

1. Requirements: Apple M3 or newer, macOS 26.4+, Homebrew. Ask before installing: `brew install incoai/tap/splash`.
2. Optional: keep downloads on a large disk, `export HF_HUB_CACHE=/Volumes/<disk>/hf-cache`.
3. Unload LM Studio first (`lms unload --all`); two 27B models do not fit in 32 GB.
4. `splash serve --model <owner>/<repo-GGUF>:<quant> --language-only --max-context 32K --max-memory 26G`
   Supported GGUF types: Q2_K to Q8_0, IQ formats, MXFP4; **not** BF16 or UD-Q8_K_XL. RoPE scaling (YaRN) is rejected.
5. Check the log line `Installing … as Qwen3.8-27B (gguf); draft incoai/Qwen3.8-27B-DFlash2` (or the 35B family) and wait for `Ready`. If no family matches, Splash says so before downloading weights; stop there.
6. Measure with `bench_speed.py` after setting `URL = "http://127.0.0.1:8000/v1/chat/completions"`, and compare with the same GGUF in LM Studio.

**Path B, a Splash package that LM Studio loads (more work, ask first):**

LM Studio's Splash backend loads only packed Splash packages (`manifest.json`, `target/`, `draft/`, `tokenizer/`, `vision/`), such as `incoai/Qwen3.8-27B-Splash` or the community build `ezoushen/ornith-1.5-35b-a3b-splash`, whose `manifest.json` names the converter it used. Steps: download the fine-tune in BF16, convert to MLX affine 4-bit with group size 64 (`mlx_lm.convert -q --q-bits 4 --q-group-size 64`), then pack target and draft with Splash's converter of the matching release. Check first that the current Splash release still produces the package format LM Studio's backend expects; this has changed between releases. Expect a 50+ GB download and one to two hours.

Licences: check that both the fine-tune and the draft allow redistribution before anyone uploads a package.

## Writing results

State what was measured, on which machine, with which runtime versions. Mark interpretations as such. Do not compare against numbers from other machines without saying so.
