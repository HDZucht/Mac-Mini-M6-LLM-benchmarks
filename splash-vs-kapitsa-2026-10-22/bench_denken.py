#!/usr/bin/env python3
"""Thinking length with thinking on: five tasks with checkable answers (lab throughput, primes 100-150, ordering,
positive predictive value, letter count), 2 runs each, temperature 0.6, max_tokens 8000. Records tokens, thinking
characters, time and correctness. EFFORT=low sets reasoning_effort. Prompts are in German, as used in the run.
Usage: bench_denken.py <model-id> <label>   -> denken.jsonl.
Argus (Claude Opus 5.5), Oct 2026."""
import json, os, re, sys, time, urllib.request, pathlib
BASE = os.environ.get("BENCH_BASE", "http://127.0.0.1:8010/v1")
OUT = pathlib.Path(__file__).with_name("denken.jsonl")
TASKS = {
  "durchsatz": ("Ein Labor misst 96 Proben pro Platte, 3 Platten pro Lauf und 2 Läufe pro Tag. 5 % aller gemessenen Proben sind "
                "Wiederholungen. Wie viele neue Proben schafft es in einer Woche mit 5 Arbeitstagen? Antworte am Ende mit 'Ergebnis: <Zahl>'.",
                r"Ergebnis:\s*\**\s*2[.\s]?736\b"),
  "primzahlen": ("Wie viele Primzahlen liegen zwischen 100 und 150? Antworte am Ende mit 'Ergebnis: <Zahl>'.", r"Ergebnis:\s*\**\s*10\b"),
  "reihenfolge": ("Anna ist älter als Ben. Ben ist älter als Carla. Dora ist jünger als Carla. Wer ist die zweitjüngste Person? "
                  "Antworte am Ende mit 'Ergebnis: <Name>'.", r"Ergebnis:\s*\**\s*Carla"),
  "ppv": ("Ein Test hat 90 % Sensitivität und 95 % Spezifität, die Prävalenz ist 1 %. Wie hoch ist der positive prädiktive Wert in Prozent, "
          "auf eine Nachkommastelle? Antworte am Ende mit 'Ergebnis: <Zahl> %'.", r"Ergebnis:\s*\**\s*15[,.]4"),
  "buchstaben": ("Wie oft kommt der Buchstabe r (groß oder klein) im Wort 'Erdbeerrhabarber' vor? Antworte am Ende mit 'Ergebnis: <Zahl>'.",
                 r"Ergebnis:\s*\**\s*5\b"),
}
def ask(model, prompt):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.6, "top_p": 0.95, "max_tokens": 8000}
    if os.environ.get("EFFORT"): body["reasoning_effort"] = os.environ["EFFORT"]  # e.g. low: Qwen3.8 thinking level
    t = time.time()
    with urllib.request.urlopen(urllib.request.Request(BASE + "/chat/completions", json.dumps(body).encode(),
                                                       {"Content-Type": "application/json"}), timeout=3600) as r:
        d = json.load(r)
    m = d["choices"][0]["message"]; u = d.get("usage") or {}
    reas = m.get("reasoning_content") or m.get("reasoning") or ""
    content = m.get("content") or ""
    inline = "".join(re.findall(r"<think>.*?</think>", content, flags=re.S))
    rt = (u.get("completion_tokens_details") or {}).get("reasoning_tokens")
    return {"sec": round(time.time() - t, 1), "completion_tokens": u.get("completion_tokens"), "reasoning_tokens": rt,
            "reasoning_chars": len(reas) + len(inline), "answer_chars": len(content) - len(inline),
            "finish": d["choices"][0].get("finish_reason"), "content": re.sub(r"<think>.*?</think>", "", content, flags=re.S)[-400:]}
if __name__ == "__main__":
    model, label = sys.argv[1], sys.argv[2]
    with OUT.open("a") as f:
        for k, (p, rx) in TASKS.items():
            for i in range(2):
                try:
                    r = ask(model, p); r["korrekt"] = bool(re.search(rx, r["content"], flags=re.I))
                except Exception as e:
                    r = {"error": str(e)[:200]}
                r.update(label=label, model=model, task=k, run=i)
                f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
                print(f"{label:16} {k:12} #{i} {r.get('sec')}s tok {r.get('completion_tokens')} denk {r.get('reasoning_tokens')}/"
                      f"{r.get('reasoning_chars')}Z korrekt={r.get('korrekt')} {r.get('finish')}", flush=True)
