# Suits AI — Website

Marketing site + app shell for **Suits AI**, a DaarLabs / DaarForce product.
Legal information & news — *not* legal advice.

## Pages
| File | Purpose |
|---|---|
| `index.html` | Landing page (hero, categories, how-it-works, accuracy, CTA) |
| `chat.html` | Chat interface (front-end shell; wire to the RAG backend) |
| `privacy.html` | Privacy Policy |
| `disclaimer.html` | Disclaimer & Terms of Use (liability limitations) |
| `styles.css` | Shared design system (Suits theme: navy / charcoal / champagne gold) |
| `vercel.json` | Vercel config (clean URLs, security headers) |

## Design language
Modern corporate-law luxury inspired by *Suits*: deep navy + charcoal, champagne
gold accents, editorial serif (Playfair Display) over Inter, subtle pinstripe,
sharp/tailored corners. All tokens live at the top of `styles.css` (`:root`).

## Deploy to Vercel
This is a static site — no build step.

```bash
npm i -g vercel      # once
cd web
vercel               # preview deploy
vercel --prod        # production
```
Or: push to GitHub and "Import Project" in the Vercel dashboard, root = `web/`.

## Local preview
```bash
cd web
python3 -m http.server 5173   # then open http://localhost:5173
```

## Next steps (wiring the app)
- Replace the demo answer in `chat.html` (`addDemoAnswer()`) with a call to a
  backend endpoint (e.g. a Vercel Serverless Function `/api/ask`) that runs the
  RAG pipeline in `../data-pipeline`.
- Keep the disclaimer ribbon, confidence badge, "accurate as of" date, and
  citation cards on every real answer — they are part of the compliance posture.
- Migrate to Next.js when you add auth, accounts, and the situation profile.

## Disclaimers baked in (do not remove)
"Information & news, not legal advice" · "~95% target accuracy" ·
"accurate as of {date}" · "no attorney–client relationship" · cited sources.
