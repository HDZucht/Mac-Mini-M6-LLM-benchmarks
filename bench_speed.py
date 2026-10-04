#!/usr/bin/env python3
"""Decode-speed benchmark for local LLMs served by LM Studio (OpenAI-compatible API on :8234).
Usage: bench_speed.py <model-id> <label> [runs]   -> appends one line per prompt to results.jsonl
Measured by streaming: time to first token (TTFT) and decode tok/s = (tokens - 1) / (t_end - t_first).
Reasoning is switched off with reasoning_effort=none; thinking tokens count if a model emits them anyway.
Load each model alone with a 32k context first, e.g. `lms load <model> -c 32768`.
Written by Argus (Claude Opus 5.5) for Hans-Dieter Zucht, 2026. MIT License."""
import json, sys, time, pathlib, urllib.request
URL = "http://localhost:8234/v1/chat/completions"
HERE = pathlib.Path(__file__).parent
PROMPTS = {
  "wissen_de": "Erkläre in etwa 300 Wörtern auf Deutsch, warum der Rhein bei Basel nach Norden abbiegt und welche Rolle der Oberrheingraben dabei spielt.",
  "beads_de": "Erkläre in etwa 300 Wörtern auf Deutsch, wie ein Bead-basierter Multiplex-Immunoassay Autoantikörper im Serum misst und welche Fehlerquellen es gibt.",
  "prosa_en": "In about 300 words, explain in English how the Ruhr area changed from coal and steel to a service economy.",
  "code_py": "Write a Python function that parses an ISO-8601 duration string like 'P3DT4H12M' into total seconds, with docstring and three doctests. Only code.",
  "json_extr": "Extract all antigens and diseases from this sentence as JSON {\"antigens\":[],\"diseases\":[]}: 'Autoantibodies against Ro52, La/SSB and CENP-B were elevated in Sjögren's syndrome and systemic sclerosis, while anti-MDA5 marked dermatomyositis.'",
}
def run(model, prompt):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 600,
            "temperature": 0.7, "stream": True, "reasoning_effort": "none",
            "stream_options": {"include_usage": True}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    t0 = time.time(); t1 = None; n = 0; text = ""; usage = None
    with urllib.request.urlopen(req, timeout=900) as r:
        for raw in r:
            line = raw.decode().strip()
            if not line.startswith("data:") or line.endswith("[DONE]"): continue
            d = json.loads(line[5:])
            if d.get("usage"): usage = d["usage"]
            for c in d.get("choices", []):
                delta = c.get("delta", {})
                piece = (delta.get("content") or "") + (delta.get("reasoning_content") or delta.get("reasoning") or "")
                if piece:
                    if t1 is None: t1 = time.time()
                    n += 1; text += piece
    t2 = time.time()
    toks = (usage or {}).get("completion_tokens") or n
    return {"ttft_s": round(t1 - t0, 2), "decode_tps": round((toks - 1) / (t2 - t1), 1), "tokens": toks, "chunks": n, "text": text}
if __name__ == "__main__":
    model, label = sys.argv[1], sys.argv[2]; runs = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    run(model, "Hallo")  # Warmup
    with open(HERE / "results.jsonl", "a") as f:
        for k, p in PROMPTS.items():
            for i in range(runs):
                r = run(model, p); r.update(label=label, model=model, prompt=k, run=i)
                f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
                print(f"{label:22} {k:10} #{i} TTFT {r['ttft_s']:5}s  {r['decode_tps']:6} tok/s  ({r['tokens']} tok)")
