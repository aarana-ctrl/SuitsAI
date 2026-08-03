# Suits AI — Data Pipeline

Builds the legal knowledge base that Suits AI retrieves from (RAG). We do **not**
train a model on the law — we keep a live, dated, citable corpus and let a
frontier LLM read from it at query time. Re-scan to stay current; don't re-train.

## Flow
```
ingest.py  ──►  corpus/corpus.jsonl  ──►  embed.py  ──►  Postgres + pgvector  ──►  /api/ask (RAG)
 (free            (chunked, dated,          (vectors +
  sources)         cited chunks)             keyword index)
```

## Sources (start free & open, expand later)
| Source | What | Auth | Status |
|---|---|---|---|
| **eCFR** | Federal regulations — Title 8 (immigration), Title 26 (tax) | none | wired ✅ |
| **CourtListener / Free Law Project** | 9M+ case-law opinions, 2,000+ courts | token (free) or **bulk** | wired (optional) |
| govinfo.gov | US Code, CFR bulk XML (authoritative) | free API key | TODO |
| USCIS Policy Manual + form instructions | immigration guidance | scrape | TODO |
| IRS pubs / form instructions | tax guidance | scrape | TODO |
| State statutes / traffic & parking codes | civil, per-state | varies | TODO (expand by state) |

## Run
```bash
cd data-pipeline
python3 ingest.py                     # -> corpus/corpus.jsonl  (stdlib only)
export COURTLISTENER_TOKEN=...         # optional, enables case law
pip install -r requirements.txt
export DATABASE_URL=postgres://localhost/suitsai
export OPENAI_API_KEY=...
python3 embed.py                       # embed + load into pgvector
```

> **Note:** `ingest.py` needs outbound access to `ecfr.gov` /
> `courtlistener.com`. Some sandboxes block these — run it on your own machine
> or CI, where it reaches the live APIs. Endpoint verified:
> `GET /api/versioner/v1/full/{date}/title-{n}.xml?part={part}`.

## Regular scans (keep it current → powers the "accurate as of {date}" stamp)
Schedule `ingest.py` + `embed.py` to re-run on a cadence. Two easy options:

**GitHub Actions** — `.github/workflows/scan.yml`:
```yaml
on:
  schedule: [{ cron: "0 8 * * 1" }]   # every Monday 08:00 UTC
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r data-pipeline/requirements.txt
      - run: python data-pipeline/ingest.py && python data-pipeline/embed.py
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          COURTLISTENER_TOKEN: ${{ secrets.COURTLISTENER_TOKEN }}
```
**Vercel Cron** — hit an `/api/scan` route on a schedule (see `vercel.json` cron).

Each chunk stores an `as_of` date, so the app can always tell users how fresh
the underlying law is — and never cite repealed sections.

## Corpus chunk shape
```json
{
  "id": "a1b2c3…",
  "text": "full section text …",
  "metadata": {
    "source_type": "regulation",
    "corpus": "eCFR",
    "jurisdiction": "US-federal",
    "domain": "immigration",
    "citation": "8 CFR § 214.2",
    "heading": "Special requirements for admission…",
    "url": "https://www.ecfr.gov/current/title-8/section-214.2",
    "as_of": "2026-08-02",
    "effective_date": "2026-08-02"
  }
}
```
