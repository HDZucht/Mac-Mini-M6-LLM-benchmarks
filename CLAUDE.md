# CLAUDE.md — instructions for Claude Code

This repository holds speed measurements of local LLMs on a Mac mini M6 (32 GB): `README.md` (tables and findings), `bench_speed.py` (the measuring script), `data/` (raw JSON lines).

## Re-running or extending the benchmark

1. LM Studio must serve its OpenAI-compatible API on `localhost:8234` (the script's `URL`); adjust it if the user's port differs. Ask the user to start the server, do not install anything unasked.
2. Load **one model at a time** with a 32k context: `lms unload --all && lms load <model-id> -c 32768 -y`. Check the loaded context with `lms ps`; MLX builds may ignore `-c`, note the real value.
3. `python3 bench_speed.py <model-id> <label> 3` appends to `results.jsonl`. Reasoning is switched off via `reasoning_effort: "none"`; if a model still emits thinking, those tokens count and the note in the README (¹) applies.
4. Report the median decode tok/s per prompt, as in the README table. Keep the existing rows; add new ones with the date.
5. Long runs heat the machine. If the user has the fan controller from [Mac-mini-M6-fan-control-LLM](https://github.com/HDZucht/Mac-mini-M6-fan-control-LLM) installed, suggest `echo 100 > /Users/Shared/mac-fan-guard/mode` for the run and `echo curve > …` afterwards, and log temperatures if you change the method.

## Writing results

State what was measured, on which machine, with which runtime versions. Mark interpretations as such. Do not compare against numbers from other machines without saying so.
