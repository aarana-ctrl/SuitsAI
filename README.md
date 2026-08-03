<div align="center">

# ⚖️ Suits AI

**Legal intelligence, tailored to your situation.**

Clear, cited answers on immigration, tax, and everyday legal questions —
in plain English. *Legal information & news, not legal advice.*

A product of **DaarLabs**.

</div>

---

## Overview

**Suits AI** is an AI-powered legal information assistant. People — especially
immigrants, international students, and anyone who can't afford a lawyer for
every question — describe their situation and get a plain-English answer grounded
in current statutes, regulations, and case law, with the sources cited and an
"accurate as of" date attached.

It is deliberately a **generalist**: broad coverage across the questions people
actually face (immigration, taxes, traffic, housing, small claims, employment,
consumer, legal news), deepening in each area over time.

> [!IMPORTANT]
> Suits AI provides **legal information and news for general educational
> purposes** — it does **not** provide legal advice, does not practice law, and
> is not a law firm. Using it does not create an attorney–client relationship.
> It targets **~95% accuracy**, which means roughly **1 in 20 answers may be
> wrong**. Always verify anything important with primary sources or a licensed
> attorney before acting.

## Why "~95%," and why that's the point

We do **not** claim 100%. Independent research (Stanford RegLab / HAI, 2025)
found even leading commercial legal-research AIs hallucinate on a meaningful
share of queries. So Suits AI is built for **calibrated honesty over false
confidence**: every answer is **grounded** (backed by a retrieved source),
**cited**, **dated**, and **auditable**, and the system **escalates**
high-stakes questions to a human attorney instead of guessing.

## Features

- 🔎 **Grounded, cited answers** — retrieval-augmented generation over primary
  legal sources; every claim links to a source you can open.
- 🗓️ **Always dated** — each answer is stamped "accurate as of {date}"; the
  corpus is refreshed on a regular internet-scan schedule (re-index, not re-train).
- 🧭 **Honest limits** — confidence signals and clear "see a licensed attorney"
  escalation for high-stakes matters (criminal, deadlines, immigration status).
- 🧵 **Broad practice areas** — immigration, tax, traffic, housing, small claims,
  employment, consumer, and legal news.
- 🎨 **Monochrome-luxury UI** — editorial serif, cinematic hero, fully responsive,
  with **light & dark modes** (persisted, respects system preference).
- 🔐 **Privacy-first** — comprehensive Privacy Policy + Terms; no secrets in the
  repo; liability disclaimers throughout.

## Tech stack

| Layer | Choice |
|---|---|
| **Frontend** | Static HTML/CSS/JS (multi-page), zero build step |
| **Fonts / type** | Cormorant Garamond (serif display), Jost (sans), Allura (script) |
| **Theming** | CSS custom properties + `data-theme`, `localStorage` persistence |
| **Hosting** | Vercel (static) |
| **Retrieval / "model"** | Frontier LLM via API + RAG (retrieval over the corpus) |
| **Vector store** | Postgres + `pgvector` (hybrid vector + keyword search) |
| **Embeddings** | Managed embeddings API (swappable) |
| **Data pipeline** | Python (stdlib ingest), scheduled scans (GitHub Actions / Vercel Cron) |
| **Free sources** | eCFR (Title 8 immigration, Title 26 tax), CourtListener case law, govinfo, USCIS, IRS |

> The AI is intentionally **not trained on the law**. It **retrieves** the law at
> query time, which is how answers stay current and every claim gets a citation.

## Repository structure

```
SuitsAI/
├── web/                        # The website (deploy this on Vercel)
│   ├── index.html              # Home (cinematic hero + floating hammer)
│   ├── practice.html           # Practice areas
│   ├── process.html            # How it works
│   ├── accuracy.html           # Accuracy & honesty
│   ├── chat.html               # Chat interface (front-end shell)
│   ├── privacy.html            # Privacy Policy
│   ├── disclaimer.html         # Disclaimer & Terms of Use
│   ├── styles.css              # Design system (light + dark)
│   ├── theme.js                # Light/dark theme (persisted)
│   ├── components.js           # Shared nav + footer + routing + mobile menu
│   └── vercel.json             # Vercel config (headers, routing)
├── data-pipeline/              # Legal corpus ingestion (RAG)
│   ├── ingest.py               # Pull + chunk free sources -> corpus.jsonl
│   ├── embed.py                # Embed + load into Postgres/pgvector
│   ├── requirements.txt
│   └── README.md
├── STRATEGY_AND_ARCHITECTURE.md  # Product strategy, architecture, roadmap
└── README.md                   # You are here
```

## Run locally

**Website** (no build step):
```bash
cd web
python3 -m http.server 5173
# open http://localhost:5173
```

**Data pipeline**:
```bash
cd data-pipeline
python3 ingest.py                 # -> corpus/corpus.jsonl (stdlib only)
pip install -r requirements.txt
export DATABASE_URL=postgres://localhost/suitsai
export OPENAI_API_KEY=...
python3 embed.py                  # embed + load into pgvector
```
See `data-pipeline/README.md` for sources, scheduling (regular scans), and notes.

## Deploy (Vercel)

Static site, no framework build.

- **Dashboard:** import this repo → set **Root Directory = `web`** →
  **Framework Preset = Other** → Deploy.
- **CLI:**
  ```bash
  cd web
  vercel --prod
  ```

## Routing & pages

The site is multi-page: each top-nav item (Home, Practice, Process, Accuracy)
is its own HTML page, so browser **history / back-forward works natively**, and
subpages include a **← Back** control. Nav and footer are injected from a single
source (`components.js`) so links stay consistent everywhere. `vercel.json` uses
explicit `.html` routing to avoid clean-URL redirect surprises.

## Roadmap (short)

1. Wire `chat.html` to a real `/api/ask` RAG endpoint over the corpus.
2. Expand the corpus (govinfo US Code, USCIS Policy Manual, IRS pubs, per-state).
3. Build the evaluation harness (citation validity, escalation recall, sycophancy).
4. Add auth + a user "situation profile"; migrate to Next.js.
5. Later phases: assisted tax prep, document assembly, lawyer referral.

See **`STRATEGY_AND_ARCHITECTURE.md`** for the full plan.

## Legal

Templates in `privacy.html` and `disclaimer.html` are starting points, **not
legal advice**, and disclaimers alone do not eliminate all risk (including
unauthorized-practice-of-law exposure). **Have a licensed attorney review and
finalize them before launch.** Replace placeholder emails and bracketed
governing-law fields first.

---

<div align="center">
<sub>© 2026 DaarLabs. Suits AI is not affiliated with, endorsed by, or connected to the television program “Suits” or its rights holders.</sub>
</div>
