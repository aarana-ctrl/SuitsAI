# DaarLabs Legal Assistant — Strategy & Architecture

*Working name: "Daar Legal" (placeholder). Version 0.1 — July 2026.*
*Audience: founding team. This is a living document; update it as decisions are made.*

---

## 0. TL;DR

You want an AI product that gives ordinary people — immigrants, students, workers, families — trustworthy answers to legal and tax questions, automates the paperwork, and connects them to a real lawyer when they need one. That is a genuinely valuable, buildable product.

**The one thing to internalize before writing any code:** *the goal is not 100% accuracy — it is calibrated, cited, and safe.* No legal AI on earth is 100% accurate. A 2025 Stanford study found the best commercial legal-research AI (Lexis+ AI) hallucinated on **17%** of queries and answered only **65%** correctly; Westlaw hallucinated **33%**; GPT-4 alone **43%**. These are tools built by billion-dollar companies on curated legal databases. Chasing "100%" will make you *over-promise, under-disclaim, and get sued.* Chasing "cited, honest, and knows when to say 'see a lawyer'" makes you trustworthy and defensible.

This document reframes the product around that principle and gives you a concrete architecture, an MVP you can ship in ~8–12 weeks with a small team, a data pipeline, model choices, an evaluation strategy, a compliance layer, and a phased roadmap.

---

## 0.5 v0.2 direction (updated from founder input)

Decisions locked in since v0.1, reflected in the shipped `web/` and `data-pipeline/`:

- **Product name:** **Suits AI** (after the show *Suits*). Design language = modern corporate-law luxury: deep navy/charcoal, champagne gold, editorial serif. Deploys on **Vercel**.
- **Framing:** positioned as **legal information & news for general educational purposes** — *not* "advice." This is deliberate: calling it "advice" invites UPL liability that no disclaimer removes, because UPL turns on the *activity*, not the label. The UI reads the same to users; the framing is what keeps you defensible. Lawyer referral is deferred to a later phase.
- **Accuracy target: ~95%, stressed everywhere.** Every surface states it plainly ("~95% — roughly 1 in 20 answers may be wrong"). No "100%" language anywhere. Honesty is the brand.
- **Currency:** the corpus is refreshed by **scheduled internet scans** (GitHub Actions / Vercel cron), and every answer is stamped **"accurate as of {date}"** from each chunk's `as_of` field. Re-scan, never re-train.
- **MVP posture:** **jack of all trades, master of none** — one general pipeline answering basic questions across many categories (immigration, tax, traffic/parking, housing, small claims, employment, consumer, legal news), deepening per-domain over time.
- **Liability:** comprehensive Privacy Policy + Disclaimer/Terms (`web/privacy.html`, `web/disclaimer.html`) disclaim responsibility for DaarLabs/DaarForce as hard as the law allows (as-is, no warranties, limitation of liability, indemnification). These are strong templates — **have a licensed attorney finalize them before launch.**

Everything below (§1–§13) remains the technical/strategic foundation; the items above are the concrete choices layered on top.

---

## 1. The reframe: what this product actually is

### 1.1 It is legal *information* + *automation* + *referral* — not legal *advice*

This distinction is the entire legal foundation of the company, so it matters.

- **Legal information** ("Here's what the law says, here are the rules for F-1 students and passive income, here are the primary sources") — legal, protected, valuable.
- **Legal advice** ("You specifically should do X in your situation") — in every US state this is the **practice of law**, and doing it without a licensed attorney is **Unauthorized Practice of Law (UPL)**. This is not theoretical: DoNotPay was fined by the FTC in 2024 for marketing itself as "the world's first robot lawyer," and LegalZoom has fought UPL suits for two decades.
- **Document automation** (filling forms, assembling filings from user inputs) — legal when done as a self-help tool, the way TurboTax and LegalZoom operate.
- **Lawyer referral** (matching users to licensed attorneys) — legal, and it's your monetization and your safety valve.

**Design consequence:** the product is framed everywhere as *"legal information and self-help tools, not legal advice,"* it always cites primary sources, and it routes anything high-stakes or fact-specific to a human lawyer. This framing is baked into the system prompt, the UI copy, the Terms of Service, and the model's refusal behavior — not bolted on later.

### 1.2 The honest accuracy target

Replace "100% accurate" with four measurable properties:

1. **Grounded** — every substantive claim is backed by a retrieved primary source (statute, regulation, agency guidance, case) with a citation the user can click. No citation → no claim.
2. **Calibrated** — the system expresses uncertainty and *refuses / escalates* when confidence is low or stakes are high. High recall on "this needs a lawyer" is more important than being right on the hard questions.
3. **Current** — sources are dated and versioned; the model never answers immigration/tax questions from stale training memory.
4. **Auditable** — every answer logs which sources were retrieved and what was generated, so you can review, improve, and defend it.

A product that hits these four is *safe and useful even at 70% raw accuracy*, because the other 30% is handled by "I'm not sure — here's what the sources say and here's a lawyer." A product that claims 100% and is silently wrong 30% of the time is a lawsuit.

---

## 2. Scope: how to "handle all kinds of cases" without failing

You said the MVP should handle *all kinds of cases and queries* and doesn't need to be super accurate yet. That's the right instinct for a demo, but "handle everything equally" is how legal-tech startups die. The resolution:

**One architecture, many domains, tiered depth.** Build a single general pipeline that can *accept* any question, but give it three response tiers depending on how well-supported and how risky the topic is:

- **Tier A — Deep, cited answers.** Domains where you've ingested authoritative primary sources: immigration (INA, 8 CFR, USCIS Policy Manual, USCIS pages), federal tax (IRC, IRS pubs/forms/instructions), and a starter set of common civil topics (traffic, parking, tenant basics, small claims). Here the model retrieves and cites.
- **Tier B — General information + strong escalation.** Any topic outside the ingested corpus (family law, a specific DUI in a specific county, employment disputes). The model gives careful general information, heavily caveated, and pushes toward the lawyer marketplace. It never fabricates citations.
- **Tier C — Hard stop / immediate escalation.** Criminal charges, deadlines that are imminent, anything where a wrong answer causes irreversible harm (missing a court date, a removal/deportation risk, a filing deadline). The model does *not* try to solve it; it triages and routes to a human fast.

A **router/classifier** at the front decides the tier and the domain. This lets you honestly say "it handles anything" while ensuring the risky 20% is handled by escalation, not by a confident hallucination. You expand Tier A domain-by-domain over time; the router improves as you add corpora.

---

## 3. System architecture

### 3.1 High-level flow

```
User (web/mobile)
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  APPLICATION LAYER                                           │
│  Auth · user profile/"situation" · document vault · billing │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  ORCHESTRATION LAYER  (the "brain")                         │
│                                                             │
│  1. Intake & profile builder  ── structured facts about    │
│                                   the user's situation      │
│  2. Router / triage classifier ── domain + risk tier        │
│  3. Retrieval (RAG) ── pull relevant primary sources        │
│  4. Answer generation ── grounded, cited, caveated          │
│  5. Guardrail / verifier ── check citations, UPL, risk      │
│  6. Escalation & handoff ── to lawyer marketplace           │
└─────────────────────────────────────────────────────────────┘
      │                    │                     │
      ▼                    ▼                     ▼
┌───────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ KNOWLEDGE BASE│  │ DOCUMENT ENGINE  │  │ LAWYER NETWORK   │
│ vector + kw   │  │ form fill / tax  │  │ matching / booking│
│ search over   │  │ prep / assembly  │  │ + escrow/payment  │
│ primary law   │  │                  │  │                  │
└───────────────┘  └──────────────────┘  └──────────────────┘
```

### 3.2 The pieces, concretely

**Intake & profile builder.** The single biggest driver of answer quality isn't the model — it's *knowing the user's actual situation.* A structured intake (visa type, status dates, income sources, state of residence, etc.) turns a vague question into a precise, retrievable one. Store this as a structured profile the user can edit; every query is answered *in the context of that profile.* This is also your moat: the app that knows your full immigration/tax picture gives far better answers than a blank chatbot.

**Router / triage classifier.** A cheap, fast LLM call (or a fine-tuned small classifier) that outputs `{domain, risk_tier, needs_lawyer, jurisdiction}`. Drives which corpus to retrieve from and which response tier to use. This is where "handle everything safely" lives.

**Retrieval (RAG).** Hybrid search (vector embeddings + keyword/BM25) over a chunked, metadata-rich corpus of primary legal sources. Retrieval is what separates you from "ChatGPT with a legal prompt" — and per the Stanford study, RAG is exactly what cut hallucination rates roughly in half versus a raw LLM. Details in §4.

**Answer generation.** A frontier LLM given (a) the user's profile, (b) the retrieved sources, and (c) a strict system prompt: answer *only* from provided sources, cite every claim, express uncertainty, add the not-legal-advice framing, and recommend a lawyer when appropriate.

**Guardrail / verifier.** A second pass that checks: does every citation in the answer actually appear in the retrieved set (catch fabricated cites)? Did the model give a directive it shouldn't (UPL)? Is this a Tier C topic that should have escalated? This is cheap insurance against the failure modes that get legal-AI companies sued.

**Escalation & handoff.** Structured lead-generation to the lawyer network — the model produces a clean case summary the lawyer can act on. This is both a safety mechanism and your best revenue line.

**Document engine.** Deterministic (non-LLM) form filling from the structured profile, with LLM assistance for explanation and gap-finding. Start with *assisted prep* (fill and hand back to the user to file), not auto-file. See §6 on tax.

**Lawyer network.** Directory + matching + booking + payments. Can start as a simple curated list and a booking link; grows into a marketplace.

---

## 4. The knowledge base — data pipeline

This is the heart of the product. Garbage sources → garbage answers, no matter how good the model.

### 4.1 What to ingest, and where to get it (all free / low-cost)

| Domain | Primary sources | Access |
|---|---|---|
| Immigration | Immigration & Nationality Act (INA), Title 8 CFR, USCIS Policy Manual, USCIS form instructions, DOS visa pages | eCFR API, govinfo.gov (bulk XML), USCIS.gov, uscis.gov Policy Manual |
| Federal tax | Internal Revenue Code (Title 26), IRS Publications, form instructions, Revenue Rulings | IRS.gov, govinfo, eCFR (26 CFR) |
| Statutes / regs (general) | US Code, Code of Federal Regulations | govinfo.gov bulk data, eCFR API, Cornell LII |
| Case law | 9M+ opinions, 2,000+ courts | **CourtListener / Free Law Project** REST API v4 + quarterly bulk data (free) |
| State/local (civil) | State statutes, traffic/parking codes | State legislature sites; add per-state as you expand |

Two anchors worth calling out: **govinfo.gov** (the US Government Publishing Office) offers bulk, authoritative, machine-readable US Code and CFR — this is your statutory backbone. **CourtListener** offers a free REST API (v4) and quarterly bulk downloads over 9M+ decisions, and as of 2026 even exposes an MCP connector; it's the standard free source for case law. Note CourtListener's 2026 free-tier rate limits (5 req/min, 125/day) — for ingestion you'll want bulk downloads, not live API crawling.

### 4.2 Pipeline stages

1. **Ingest** — pull bulk XML/JSON (govinfo, eCFR, CourtListener bulk). Schedule quarterly refreshes (CourtListener regenerates bulk data end of Mar/Jun/Sep/Dec; eCFR and IRS update continuously — track effective dates).
2. **Normalize** — strip to clean text, preserve structure (title → section → subsection), keep citations and hierarchy.
3. **Chunk** — split by logical unit (a CFR subsection, a case holding), not fixed token windows. Legal meaning lives in structure. Target ~500–1,000 tokens with overlap; attach rich metadata: `{jurisdiction, source_type, citation, section_path, effective_date, url}`.
4. **Embed** — run chunks through an embedding model; store vectors.
5. **Index** — store in a vector DB *and* a keyword index (legal search needs exact-term/citation matching that pure vectors miss).
6. **Version** — every chunk carries an effective date so the model never cites repealed law. This is non-negotiable for immigration/tax.

### 4.3 Storage / tooling

For a lean MVP: **Postgres + pgvector** covers both relational data and vector search in one database you already need — simplest path. Alternatives (Pinecone, Weaviate, Qdrant) if scale demands. Keyword search via Postgres full-text or a small OpenSearch instance. Don't over-build here; pgvector will carry you well past MVP.

---

## 5. Model choices (lean, managed-API-first)

You're a small team shipping fast, so **do not train a model from scratch and do not fine-tune early.** Modern frontier models + good RAG beat a custom-trained legal model that a small team could realistically produce, at a fraction of the cost and risk. The Stanford results are on RAG systems, not custom-trained models — retrieval quality, not model training, is where your effort pays off.

**Recommended stack for MVP:**

- **Generation:** a frontier instruction model via API (Claude, GPT, or Gemini class). Pick one to start; keep the interface model-agnostic so you can swap or route. Use a strong model for answers, a cheap/fast one for the router and intake.
- **Embeddings:** a managed embeddings API, or an open model (e.g., a strong open-source embedding model) if you want to control cost and keep data in-house.
- **Router/classifier:** cheap fast model, few-shot prompted at first; fine-tune a small classifier later once you have labeled traffic.

**When to fine-tune (later, Phase 3+):** only after you have (a) real usage data, (b) a solid eval set, and (c) a specific, measured gap that prompting + retrieval can't close — e.g., consistent formatting of immigration answers, or a domain-specialized retriever. Fine-tune the *retriever/embeddings* before the generator; retrieval quality has more leverage.

**"Train on the entire Constitution and all case law" — reframed.** You do not train the model *on* this text; you *retrieve from* it at query time (RAG). That's how you stay current (re-index, don't re-train), how you get citations (you know exactly what was retrieved), and how you avoid the model confidently inventing law. Treat the corpus as a live library the model reads from, not knowledge baked into weights.

---

## 6. Tax filing — the highest-liability feature, handled carefully

Tax auto-filing is the most valuable *and* most dangerous feature. Sequence it:

- **Phase 1 — Guidance & document checklist.** "Based on your situation (F-1, 3rd year, brokerage income, scholarship), here's your likely filing status, the forms you probably need (1040-NR? 8843? treaty benefits?), and the documents to gather." Information + organization. Low liability.
- **Phase 2 — Assisted prep.** Ingest the user's documents (W-2, 1099, 1042-S), extract fields, pre-fill a return, explain each line, and hand it back for the user to review and file themselves. This is the TurboTax model.
- **Phase 3 — Assisted/auto e-file.** Only after Phases 1–2 are proven and you understand the regulatory weight. Becoming a filer/preparer implicates **IRS Circular 230**, **PTIN** requirements, e-file provider (ERO) authorization, and per-return liability. Likely requires partnering with an authorized e-file provider or bringing a credentialed preparer (CPA/EA) into the loop rather than fully autonomous filing. Keep the user's "final submit" control as you described — that's both good UX and a liability firewall.

Document handling for tax means **serious privacy engineering from day one** (see §8): you're holding SSNs, income, immigration status — some of the most sensitive PII that exists.

---

## 7. Evaluation & accuracy strategy

You can't improve or defend what you don't measure. Build the eval harness *before* you scale.

- **Golden question set.** Assemble 200–500 real-world questions per Tier-A domain with expert-verified answers and the correct citations. This is your regression suite. Grow it continuously from real (anonymized) user questions.
- **Metrics that match the honest target:**
  - *Citation validity* — % of cited sources that actually exist in the corpus and support the claim (directly attacks hallucination).
  - *Grounding* — % of claims traceable to a retrieved source.
  - *Escalation recall* — of questions that *should* go to a lawyer, what % did the system route? (Optimize this hard; false negatives here are the dangerous ones.)
  - *Refusal calibration* — does it decline when it should?
  - *Answer accuracy* — expert-graded, on the golden set.
- **LLM-as-judge + human spot-checks.** Automated grading for scale, licensed-attorney review on a sample for ground truth.
- **Adversarial / sycophancy tests.** The Stanford study flagged *sycophancy* — the model agreeing with a user's wrong legal premise and fabricating support — as a top failure mode. Explicitly test "user asserts something false; does the model correct it or cave?"
- **Red-team the guardrails.** Try to make it give UPL-style directives, cite fake cases, or answer a Tier C question. Every failure becomes a test case.

Target for MVP launch: not a headline accuracy number, but *"escalation recall > 95% on high-risk, citation validity > 98%, zero fabricated-citation escapes in the eval set."* Those are the numbers that keep you safe.

---

## 8. Privacy, security & compliance (day-one, not later)

You're handling immigration status, SSNs, financial and tax data — a breach here is catastrophic for vulnerable users (some undocumented or status-precarious). Non-negotiables:

- **Encryption** at rest and in transit; documents in an encrypted vault, not general storage.
- **Data minimization** — collect only what a query needs; let users delete everything.
- **Access controls & audit logs** — who/what touched each record.
- **PII handling with LLMs** — be deliberate about what user PII goes to third-party model APIs; consider redaction of identifiers before sending context to external models, or use providers with zero-retention / no-training data agreements. For tax documents especially, minimize third-party exposure.
- **Consent & transparency** — explicit, plain-language consent for document processing; a real privacy policy.
- **Regulatory surface:** UPL (per-state), IRS Circular 230 / PTIN (tax prep), state consumer-protection and legal-referral rules, and — if you touch health or handle EU/other users — the corresponding privacy regimes. **Get a lawyer specializing in legal-tech / UPL before launch.** This is the one place you cannot bootstrap on vibes; a few hours of specialist counsel now prevents an existential problem later.
- **Mandatory disclaimers** surfaced in-product (not buried): "not a law firm, not legal advice, not a substitute for an attorney."

---

## 9. MVP definition (ship in ~8–12 weeks)

**Goal:** a web app that answers immigration + basic tax + common civil questions with cited sources, builds a user situation profile, escalates high-risk cases, and captures lawyer-referral leads. Broad enough to demo "handles anything," safe by design.

**In scope:**
1. Auth + editable user "situation" profile.
2. Chat interface with the full orchestration pipeline (intake → router → RAG → cited answer → guardrail → escalate).
3. Tier-A corpus: immigration (INA, 8 CFR, USCIS Policy Manual/pages) + federal tax basics (key IRS pubs/forms for students & nonresidents) + a starter civil set (traffic/parking/tenant/small-claims basics).
4. Tier-B/C fallback with strong escalation and disclaimers.
5. Citations rendered as clickable sources in every answer.
6. Lawyer referral: a "talk to a lawyer" flow that generates a case summary and captures the lead (even if the network is a hand-curated list at first).
7. Eval harness + golden set for the Tier-A domains.
8. Privacy baseline: encryption, delete-my-data, disclaimers, privacy policy.

**Explicitly out of scope for MVP:** auto-filing taxes, document auto-assembly/filing, custom model training/fine-tuning, native mobile apps, full lawyer marketplace with payments, 50-state coverage. All are roadmap items, not MVP.

**Suggested stack:** Next.js/React front end · Python (FastAPI) or Node orchestration · Postgres + pgvector · frontier LLM API for generation, cheap model for routing · govinfo/eCFR/CourtListener for corpus · S3-class encrypted storage for documents.

---

## 10. Roadmap

**Phase 0 — Foundations (weeks 0–2).** Legal-tech/UPL counsel engagement. Set up repo, infra, Postgres+pgvector. Build the ingestion pipeline for one domain (immigration). Draft ToS/privacy policy and disclaimer framework.

**Phase 1 — MVP (weeks 2–12).** Build the full pipeline end-to-end on immigration + tax basics + starter civil. Eval harness + golden set. Escalation + lead capture. Privacy baseline. Closed beta with real users (e.g., international students at your university — a perfect, reachable first audience).

**Phase 2 — Depth & trust (months 3–6).** Expand Tier-A corpora and states. Tax Phase-2 assisted prep with document ingestion. Harden guardrails from real traffic. Build out the lawyer network into a real matching/booking flow. Begin fine-tuning the retriever if evals justify it.

**Phase 3 — Automation & scale (months 6–12+).** Tax assisted/auto e-file via an authorized partner or credentialed preparer in the loop. Document assembly/filing for select immigration forms. Mobile. Marketplace with payments. Consider fine-tuning where measured gaps remain.

---

## 11. Business & go-to-market notes

- **Wedge audience:** international students are the ideal beachhead — concentrated, reachable (campus channels), acutely underserved, recurring needs (visa + tax every year), and you're at UW with direct access. Win them, then expand to H-1B/H-4 and general immigrants, then broader civil.
- **Revenue:** freemium (basic Q&A free) + paid tiers (document prep, tax prep) + **lawyer-referral fees / marketplace take** (often the strongest line, and it doubles as your safety escalation).
- **Moat:** the structured user profile + your curated, versioned legal corpus + accumulated eval data. Not the base model — anyone can call the same API.
- **Fit with DaarLabs:** shares infra, auth, billing, and document-handling patterns with your other products (Daar, DaarForce) — reuse aggressively.

---

## 12. Top risks & how the design handles them

| Risk | Mitigation baked into the design |
|---|---|
| Unauthorized practice of law | Information-not-advice framing, escalation tiers, disclaimers, specialist counsel, guardrail that blocks directive advice |
| Hallucinated law / fake citations | RAG + citation-validity verifier + "no source, no claim" |
| Stale law (immigration/tax change fast) | Versioned corpus with effective dates; re-index not re-train |
| High-stakes wrong answer (deadlines, removal, criminal) | Tier-C hard-stop + fast human escalation; optimize escalation recall |
| Sycophancy (agreeing with user's wrong premise) | Explicit adversarial evals; system prompt to correct false premises |
| PII / document breach | Encryption, minimization, redaction before external APIs, audit logs, zero-retention model agreements |
| Tax-prep liability | Phase gating; keep user's final submit; partner with authorized filer/credentialed preparer before auto-file |
| Over-promising accuracy | Replace "100%" with grounded/calibrated/current/auditable targets in product + marketing |

---

## 13. Immediate next steps

1. **Engage legal-tech/UPL counsel** — before building the escalation logic and disclaimers, so the design reflects real requirements.
2. **Stand up the immigration ingestion pipeline** (govinfo + eCFR + USCIS + CourtListener) into Postgres+pgvector — this de-risks the hardest technical piece first.
3. **Build the thin end-to-end slice** — intake → router → RAG → cited answer → guardrail → escalate — on immigration only, then widen.
4. **Assemble the first golden eval set** (start with 50 real F-1/OPT/H-1B questions and verified answers) so you're measuring from day one.
5. **Write the disclaimer + framing copy** and thread it through UI, system prompts, and ToS.

I can take any of these further right now — e.g., scaffold the repo, draft the ingestion pipeline for immigration, write the orchestration/system-prompt spec, or build the golden eval-set template. Say which and I'll start.

---

### Sources
- Stanford RegLab/HAI, *Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools* (J. Empirical Legal Studies, 2025) — hallucination rates of 17% (Lexis+), 33% (Westlaw), 43% (GPT-4); best tool 65% accurate; sycophancy as a top failure mode.
- Free Law Project / CourtListener — REST API v4, 9M+ decisions from 2,000+ courts, quarterly bulk data, 2026 rate limits, MCP connector.
