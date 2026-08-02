# ats-scan — ATS Gap Detector

Not a keyword matcher. Extracts real requirements from a JD, semantically
diffs them against a resume, and emails the candidate a gap report with
concrete next steps (not just "add these keywords").

## How it works

1. Candidate uploads resume (PDF/DOCX/TXT) + pastes a JD + enters email
2. **Stage 1** (`analyzer.py::extract_jd_requirements`) — Claude parses the JD
   into structured competency clusters, split into must-have / nice-to-have
3. **Stage 2** (`analyzer.py::analyze_gap`) — Claude semantically compares
   resume content against each requirement, classifying it as:
   - `have` — clearly demonstrated with real evidence
   - `weak` — mentioned but thin/unsupported (fixable by rewording)
   - `missing` — not evidenced at all (needs a project/course/cert)
4. Report is rendered as HTML and emailed via Resend, and also shown
   live in the browser

## Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- `ANTHROPIC_API_KEY` — from https://console.anthropic.com/settings/keys
- `RESEND_API_KEY` — from https://resend.com/api-keys (free tier: 100/day)
- `FROM_EMAIL` — use `onboarding@resend.dev` for testing, or a verified domain for production
- `ALLOWED_ORIGINS` — origins allowed to call the API (comma-separated)

Run it:
```bash
uvicorn main:app --reload --port 8000
```

Check it's alive: `curl http://localhost:8000/health` → `{"status":"ok"}`

### Frontend

Just a static file — no build step needed.

```bash
cd frontend
python3 -m http.server 5500
```

Open `http://localhost:5500`. If you deploy the backend elsewhere, update
`API_URL` at the top of the `<script>` block in `index.html`.

## Deploying (when you're ready to make it public)

- **Backend**: Render, Railway, or Fly.io all have free tiers that work
  well for FastAPI. Set the same env vars there.
- **Frontend**: Any static host (Vercel, Netlify, GitHub Pages, or even
  Render static site). Just point `API_URL` at your deployed backend.
- **Domain email**: verify your own domain in Resend once you're past
  testing, so `FROM_EMAIL` isn't `onboarding@resend.dev`.

## Known limitations / v2 ideas

- No auth, no history — every scan is stateless. Fine for MVP, add a DB
  (Postgres) later if you want candidates to track score over time.
- Scanned/image-only PDFs won't extract text — flagged with a clear error.
- JD must be pasted as text; a "paste JD URL" scraper is a natural v2.
- Rate limiting isn't implemented — add before going public, since each
  scan costs 2 Claude API calls + 1 email send.
- Cost per scan: roughly 2 Claude Sonnet calls (~3-5K tokens combined) +
  a Resend email — budget accordingly if this gets real traffic.

## Tech stack

- **Backend**: FastAPI, Anthropic SDK (Claude Sonnet), pdfplumber, python-docx, Resend
- **Frontend**: Vanilla HTML/CSS/JS (no build step, no framework)
