#!/usr/bin/env python3
"""
Suits AI — Embedding + vector store (starter)
=============================================

Reads corpus/corpus.jsonl (from ingest.py), embeds each chunk, and upserts
into Postgres + pgvector. This is the "build the model" step: the model is a
frontier LLM at query time; THIS builds the retrieval index it reads from.

Setup (once):
  createdb suitsai
  psql suitsai -c "CREATE EXTENSION IF NOT EXISTS vector;"
  export DATABASE_URL=postgres://localhost/suitsai
  export OPENAI_API_KEY=...            # or swap for your provider
  pip install -r requirements.txt

Run:
  python ingest.py       # produce corpus/corpus.jsonl
  python embed.py        # embed + load into pgvector
"""
from __future__ import annotations
import os, json, pathlib

CORPUS = pathlib.Path(__file__).parent / "corpus" / "corpus.jsonl"
EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-small")  # 1536 dims
DIMS = 1536

DDL = f"""
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS chunks (
    id           TEXT PRIMARY KEY,
    text         TEXT NOT NULL,
    domain       TEXT,
    source_type  TEXT,
    citation     TEXT,
    heading      TEXT,
    url          TEXT,
    as_of        DATE,
    metadata     JSONB,
    embedding    vector({DIMS})
);
CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_text_fts_idx
    ON chunks USING gin (to_tsvector('english', text));   -- hybrid keyword search
"""

def main():
    import psycopg
    from openai import OpenAI

    if not CORPUS.exists():
        raise SystemExit("Run ingest.py first — corpus.jsonl not found.")

    client = OpenAI()
    rows = [json.loads(l) for l in CORPUS.open(encoding="utf-8")]
    print(f"Embedding {len(rows)} chunks with {EMBED_MODEL} …")

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        conn.execute(DDL)
        for i in range(0, len(rows), 100):                 # batch
            batch = rows[i:i+100]
            vecs = client.embeddings.create(
                model=EMBED_MODEL, input=[r["text"][:8000] for r in batch]
            ).data
            with conn.cursor() as cur:
                for r, e in zip(batch, vecs):
                    m = r["metadata"]
                    cur.execute(
                        """INSERT INTO chunks
                           (id,text,domain,source_type,citation,heading,url,as_of,metadata,embedding)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                           ON CONFLICT (id) DO UPDATE SET
                             text=EXCLUDED.text, embedding=EXCLUDED.embedding,
                             as_of=EXCLUDED.as_of, metadata=EXCLUDED.metadata""",
                        (r["id"], r["text"], m.get("domain"), m.get("source_type"),
                         m.get("citation"), m.get("heading"), m.get("url"),
                         m.get("as_of"), json.dumps(m), str(e.embedding)),
                    )
            conn.commit()
            print(f"  upserted {min(i+100,len(rows))}/{len(rows)}")
    print("Done. Retrieval index ready — wire it to /api/ask.")

if __name__ == "__main__":
    main()
