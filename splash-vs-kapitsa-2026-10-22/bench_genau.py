#!/usr/bin/env python3
"""Accuracy with thinking on: MMLU-Pro (TIGER-Lab, 10 options), 10 questions each from biology, chemistry, health and math,
fixed seed 1729 (rows sorted by question_id, then sampled), the same 40 questions for every model (paired comparison).
temperature 0.6, top_p 0.95, max_tokens 8000, 3 requests in parallel. EFFORT=low sets reasoning_effort.
Needs the MMLU-Pro test parquet (path in PQ) and duckdb.
Usage: bench_genau.py <model-id> <label>   -> one line per question in genau.jsonl, summary on stdout.
Argus (Claude Opus 5.5), Oct 2026."""
import json, os, random, re, sys, time, urllib.request, pathlib, duckdb
from concurrent.futures import ThreadPoolExecutor
BASE = os.environ.get("BENCH_BASE", "http://127.0.0.1:8010/v1")
PQ = "/Volumes/ORICO/Lokal_LLM/datasets/mmlu-pro/test.parquet"
OUT = pathlib.Path(__file__).with_name("genau.jsonl")
N = int(os.environ.get("N_PER_CAT", "10")); CATS = ["biology", "chemistry", "health", "math"]; LET = "ABCDEFGHIJ"

def items():
    rnd = random.Random(1729); out = []
    for c in CATS:
        rows = duckdb.sql(f"select question_id, question, options, answer, category from '{PQ}' where category='{c}' order by question_id").fetchall()
        out += rnd.sample(rows, N)
    return out

def ask(model, it):
    qid, q, opts, ans, cat = it
    o = "\n".join(f"{LET[i]}. {x}" for i, x in enumerate(opts))
    p = ("The following is a multiple choice question. Think it through, then finish your response with exactly: The answer is (X).\n\n"
         f"Question: {q}\nOptions:\n{o}\n")
    body = {"model": model, "messages": [{"role": "user", "content": p}], "temperature": 0.6, "top_p": 0.95, "max_tokens": 8000}
    if os.environ.get("EFFORT"): body["reasoning_effort"] = os.environ["EFFORT"]  # e.g. low: Qwen3.8 thinking level
    t = time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + "/chat/completions", json.dumps(body).encode(),
                                                           {"Content-Type": "application/json"}), timeout=3600) as r:
            d = json.load(r)
    except Exception as e:
        return {"qid": qid, "cat": cat, "error": str(e)[:200]}
    m = d["choices"][0]["message"]; u = d.get("usage") or {}
    content = m.get("content") or ""; reas = m.get("reasoning_content") or m.get("reasoning") or ""
    txt = re.sub(r"<think>.*?</think>", "", content, flags=re.S)
    got = (re.findall(r"answer is[:\s]*\(?([A-J])\)?", txt, flags=re.I) or [""])[-1]
    return {"qid": qid, "cat": cat, "soll": ans, "ist": got, "korrekt": got == ans, "sec": round(time.time() - t, 1),
            "completion_tokens": u.get("completion_tokens"), "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
            "reasoning_chars": len(reas) + len(content) - len(txt), "finish": d["choices"][0].get("finish_reason")}

if __name__ == "__main__":
    model, label = sys.argv[1], sys.argv[2]; its = items(); t0 = time.time()
    with ThreadPoolExecutor(3) as ex:
        res = list(ex.map(lambda it: ask(model, it), its))
    with OUT.open("a") as f:
        for r in res:
            r.update(label=label, model=model); f.write(json.dumps(r, ensure_ascii=False) + "\n")
    ok = [r for r in res if "korrekt" in r]
    tok = sorted(r["completion_tokens"] or 0 for r in ok)
    print(f"{label}: {sum(r['korrekt'] for r in ok)}/{len(its)} correct · errors {len(its)-len(ok)} · truncated "
          f"{sum(r['finish']=='length' for r in ok)} · tokens median {tok[len(tok)//2] if tok else 0} · "
          f"thinking chars mean {sum(r['reasoning_chars'] for r in ok)//max(len(ok),1)} · {round(time.time()-t0)} s", flush=True)
    for c in CATS:
        cc = [r for r in ok if r["cat"] == c]; print(f"  {c:10} {sum(r['korrekt'] for r in cc)}/{len(cc)}")
