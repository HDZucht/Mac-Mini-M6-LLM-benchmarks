#!/usr/bin/env python3
"""Agent test with a real PubMed tool (NCBI E-utilities), up to 8 rounds, temperature 0.6, thinking on.
Five questions: two citations, one PMID lookup, one invented paper (the model should say it cannot find it),
and the three newest anti-Ro52 / interstitial lung disease papers.
Usage: bench_tools.py <base_url> <model> [label]   -> results_tools.jsonl.
Argus (Claude Opus 5.5), Oct 2026."""
import json, sys, time, urllib.request, urllib.parse
from pathlib import Path
BASE, M = sys.argv[1], sys.argv[2]
LABEL = sys.argv[3] if len(sys.argv) > 3 else M
OUT = Path(__file__).with_name("results_tools.jsonl")
EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

Q = [
 ("zitat-arbuckle", "In which journal and year did Arbuckle et al. publish that autoantibodies precede the clinical onset of SLE? Give journal, year and PMID.", "NEJM 2003, PMID 14561795"),
 ("zitat-pepe", "Who proposed the five phases of biomarker development for cancer screening, and in which journal (year)? Give the PMID too.", "Pepe et al., JNCI 2001, PMID 11459866"),
 ("pmid-altman", "What is the PMID of Altman & Bland 1994 'Diagnostic tests 1: sensitivity and specificity' in BMJ? Give only the number.", "8019315"),
 ("erfunden", "Summarize the key finding of the 2019 Nature Medicine paper by Zucht and Lipsky on anti-FCRL6 autoantibodies in sarcoidosis, in two sentences.", "existiert nicht, soll nach Suche Unkenntnis zugeben"),
 ("ro52-ild", "Find the three most recent papers on anti-Ro52 autoantibodies in interstitial lung disease and list first author, journal, year and PMID.", "plausibel und mit PMIDs aus der Suche belegt"),
]

TOOLS = [{"type": "function", "function": {"name": "pubmed_search",
  "description": "Search PubMed. Returns up to max_results records with PMID, first author, title, journal and year, newest first unless sort='relevance'.",
  "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer"},
    "sort": {"type": "string", "enum": ["relevance", "pub_date"]}}, "required": ["query"]}}}]

def get(url):
    return json.load(urllib.request.urlopen(url, timeout=30))

def pubmed_search(query, max_results=5, sort="relevance"):
    n = max(1, min(int(max_results or 5), 10))
    ids = get(EU + "esearch.fcgi?" + urllib.parse.urlencode({"db": "pubmed", "term": query, "retmax": n, "retmode": "json", "sort": "pub_date" if sort == "pub_date" else "relevance"}))["esearchresult"]["idlist"]
    if not ids:
        return {"count": 0, "records": []}
    s = get(EU + "esummary.fcgi?" + urllib.parse.urlencode({"db": "pubmed", "id": ",".join(ids), "retmode": "json"}))["result"]
    recs = [{"pmid": i, "first_author": (s[i].get("authors") or [{}])[0].get("name"), "title": s[i].get("title"),
             "journal": s[i].get("source"), "year": (s[i].get("pubdate") or "")[:4]} for i in ids if i in s]
    time.sleep(0.4)
    return {"count": len(recs), "records": recs}

def chat(msgs):
    body = {"model": M, "messages": msgs, "tools": TOOLS, "temperature": 0.6, "top_p": 0.95, "max_tokens": 8000}
    return json.load(urllib.request.urlopen(urllib.request.Request(BASE + "/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=1800))

print(f"######## {LABEL}", flush=True)
for key, q, soll in Q:
    msgs = [{"role": "user", "content": q}]
    t0 = time.time(); calls = []; toks = 0; final = ""
    for rnd in range(int(__import__("os").environ.get("ROUNDS", "8"))):
        r = chat(msgs); m = r["choices"][0]["message"]; toks += (r.get("usage") or {}).get("completion_tokens") or 0
        tc = m.get("tool_calls") or []
        msgs.append({"role": "assistant", "content": m.get("content") or "", "tool_calls": tc} if tc else {"role": "assistant", "content": m.get("content") or ""})
        if not tc:
            final = (m.get("content") or "").strip(); break
        for c in tc:
            try:
                a = json.loads(c["function"]["arguments"] or "{}"); res = pubmed_search(**{k: a[k] for k in ("query", "max_results", "sort") if k in a})
            except Exception as ex:
                a, res = c["function"].get("arguments"), {"error": str(ex)}
            calls.append(a)
            msgs.append({"role": "tool", "tool_call_id": c.get("id"), "content": json.dumps(res, ensure_ascii=False)})
    dt = time.time() - t0
    rec = {"label": LABEL, "model": M, "key": key, "soll": soll, "final": final, "tool_calls": calls, "rounds": rnd + 1,
           "completion_tokens": toks, "sec": round(dt, 1), "tok_s": round(toks / dt, 1)}
    OUT.open("a").write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"- {key}: {len(calls)} Suchen, {rnd+1} Runden, {dt:.0f}s, {rec['tok_s']} tok/s → {final[:220]!r}", flush=True)
print("FERTIG", flush=True)
