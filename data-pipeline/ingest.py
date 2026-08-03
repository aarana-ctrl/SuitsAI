#!/usr/bin/env python3
"""
Suits AI — Legal corpus ingestion pipeline (starter)
====================================================

Pulls PRIMARY legal sources from FREE / OPEN endpoints, normalizes them,
chunks them by logical unit (a CFR section, a case), attaches metadata with
an *effective / as-of date*, and writes a JSONL corpus ready for embedding.

Free sources wired here:
  1. eCFR  (Electronic Code of Federal Regulations) — public API, NO auth.
       - Title 8  = Aliens & Nationality (immigration)
       - Title 26 = Internal Revenue (tax)
  2. CourtListener / Free Law Project — case law. API token optional
       (set COURTLISTENER_TOKEN); bulk downloads are the better path at scale.

Design notes:
  * "as_of" date is stamped on every chunk so the app can display
    "accurate as of <date>" and never cite repealed law.
  * Chunk = one CFR section (structure carries legal meaning).
  * Output = corpus/corpus.jsonl  (one JSON object per line).

This is a STARTER. Expand sources per the roadmap (USCIS Policy Manual,
IRS pubs, govinfo US Code, state statutes). Respect each source's terms
and rate limits — for CourtListener use bulk data, not live crawling.
"""

from __future__ import annotations
import os, re, json, time, hashlib, datetime, pathlib, sys
import xml.etree.ElementTree as ET
import urllib.request, urllib.error, urllib.parse

OUT_DIR = pathlib.Path(__file__).parent / "corpus"
OUT_DIR.mkdir(exist_ok=True)
CORPUS = OUT_DIR / "corpus.jsonl"

USER_AGENT = "SuitsAI-DaarLabs/0.1 (legal-info research; contact: data@daarlabs.com)"
TODAY = datetime.date.today().isoformat()

# ---- sources to pull (extend freely) ---------------------------------------
ECFR_TARGETS = [
    # (title, part, domain, human label)
    (8,  "214", "immigration", "Nonimmigrant classes (F, H, etc.)"),
    (8,  "245", "immigration", "Adjustment of status to permanent resident"),
    (26, "1",   "tax",         "Income tax (selected)"),
]

# ---------------------------------------------------------------------------
def _get(url: str, headers: dict | None = None, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()

def _chunk_id(*parts: str) -> str:
    return hashlib.sha1("::".join(parts).encode()).hexdigest()[:16]

def _write(records: list[dict], fh) -> int:
    for rec in records:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return len(records)

# ---- eCFR ------------------------------------------------------------------
def fetch_ecfr(title: int, part: str, domain: str, label: str) -> list[dict]:
    """Fetch one eCFR part as XML and split into per-section chunks."""
    url = (f"https://www.ecfr.gov/api/versioner/v1/full/{TODAY}/"
           f"title-{title}.xml?part={part}")
    print(f"  [eCFR] Title {title} Part {part} … ", end="", flush=True)
    try:
        raw = _get(url)
    except urllib.error.HTTPError as e:
        # eCFR sometimes needs the latest issue date; fall back gracefully.
        print(f"HTTP {e.code} (try an earlier as-of date)"); return []
    except Exception as e:
        print(f"error: {e}"); return []

    root = ET.fromstring(raw)
    records = []
    # Sections are DIV8 elements with TYPE="SECTION".
    for sec in root.iter("DIV8"):
        if sec.get("TYPE") != "SECTION":
            continue
        cite = sec.get("N", "").strip()               # e.g. "214.2"
        head = _clean("".join(sec.find("HEAD").itertext())) if sec.find("HEAD") is not None else ""
        body = _clean(" ".join(p for p in sec.itertext()))
        if not body:
            continue
        records.append({
            "id": _chunk_id("ecfr", str(title), cite),
            "text": body,
            "metadata": {
                "source_type": "regulation",
                "corpus": "eCFR",
                "jurisdiction": "US-federal",
                "domain": domain,
                "title": f"{title} CFR",
                "citation": f"{title} CFR § {cite}",
                "heading": head,
                "url": f"https://www.ecfr.gov/current/title-{title}/section-{cite}",
                "as_of": TODAY,
                "effective_date": TODAY,
            },
        })
    print(f"{len(records)} sections")
    return records

# ---- CourtListener (optional; needs token or use bulk data) ----------------
def fetch_courtlistener(query: str, domain: str, limit: int = 20) -> list[dict]:
    token = os.environ.get("COURTLISTENER_TOKEN")
    if not token:
        print("  [CourtListener] skipped (set COURTLISTENER_TOKEN to enable)")
        return []
    url = ("https://www.courtlistener.com/api/rest/v4/search/?"
           + urllib.parse.urlencode({"q": query, "type": "o", "order_by": "score desc"}))
    print(f"  [CourtListener] '{query}' … ", end="", flush=True)
    try:
        raw = _get(url, headers={"Authorization": f"Token {token}"})
    except Exception as e:
        print(f"error: {e}"); return []
    data = json.loads(raw)
    records = []
    for r in data.get("results", [])[:limit]:
        text = _clean(r.get("snippet") or r.get("caseName") or "")
        if not text:
            continue
        records.append({
            "id": _chunk_id("cl", str(r.get("id"))),
            "text": text,
            "metadata": {
                "source_type": "case_law",
                "corpus": "CourtListener",
                "jurisdiction": r.get("court") or "US",
                "domain": domain,
                "citation": r.get("citation") or r.get("caseName"),
                "heading": r.get("caseName"),
                "url": "https://www.courtlistener.com" + (r.get("absolute_url") or ""),
                "date_filed": r.get("dateFiled"),
                "as_of": TODAY,
            },
        })
    print(f"{len(records)} opinions")
    return records

# ---- main ------------------------------------------------------------------
def main() -> None:
    print(f"Suits AI ingestion — as of {TODAY}\nWriting -> {CORPUS}\n")
    total = 0
    with CORPUS.open("w", encoding="utf-8") as fh:
        print("eCFR (regulations):")
        for title, part, domain, label in ECFR_TARGETS:
            total += _write(fetch_ecfr(title, part, domain, label), fh)
            time.sleep(1)  # be polite

        print("\nCourtListener (case law):")
        for q, dom in [("F-1 student unauthorized employment", "immigration"),
                       ("resident alien tax substantial presence", "tax")]:
            total += _write(fetch_courtlistener(q, dom), fh)
            time.sleep(1)

    print(f"\nDone. {total} chunks -> {CORPUS}")
    if total:
        print("Next: run embed.py to vectorize into Postgres/pgvector.")

if __name__ == "__main__":
    sys.exit(main())
