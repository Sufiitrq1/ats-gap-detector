# VS Code Setup + Live Deployment Guide

Two parts: (1) get it running locally in VS Code, (2) deploy it so you have
a live link. Both use free tiers — no credit card needed.

---

## PART 1 — Run it in VS Code

### 1. Install prerequisites (skip any you already have)
- **VS Code**: https://code.visualstudio.com
- **Python 3.11+**: https://python.org/downloads (on install, check "Add to PATH")
- **Git**: https://git-scm.com/downloads

Verify in a terminal:
```bash
python3 --version
git --version
```

### 2. Unzip the project
Unzip `ats-gap-detector.zip` somewhere like `~/projects/`, then:
```bash
cd ~/projects/ats-gap-detector
code .
```
This opens the folder in VS Code.

### 3. Install VS Code extensions
Open the Extensions panel (`Ctrl+Shift+X` / `Cmd+Shift+X`) and install:
- **Python** (by Microsoft)
- **Pylance** (usually installs with Python)

### 4. Set up the backend virtual environment
In VS Code, open a terminal: **Terminal → New Terminal** (`` Ctrl+` ``)

```bash
cd backend
python3 -m venv venv
```

Activate it:
- **Mac/Linux**: `source venv/bin/activate`
- **Windows**: `venv\Scripts\activate`

You'll know it worked because your terminal prompt now starts with `(venv)`.

Install dependencies:
```bash
pip install -r requirements.txt
```

**Tell VS Code to use this environment**: press `Ctrl+Shift+P` (`Cmd+Shift+P`
on Mac) → type "Python: Select Interpreter" → pick the one that shows
`./backend/venv/bin/python`. This gets you autocomplete and error-checking
on the actual packages you installed.

### 5. Add your API keys
In the `backend` folder, copy `.env.example` to a new file named `.env`:
```bash
cp .env.example .env
```
Open `.env` in VS Code and fill in:
- `ANTHROPIC_API_KEY` — get one at https://console.anthropic.com/settings/keys
- `RESEND_API_KEY` — get one free at https://resend.com/api-keys (sign up,
  no card needed, 100 emails/day free)
- Leave `FROM_EMAIL=onboarding@resend.dev` for now (works without domain setup)

**Never commit `.env` to git** — it's already excluded via `.gitignore`
(create one in step 7 if it's missing).

### 6. Run the backend
Still in the `backend` folder with `venv` active:
```bash
uvicorn main:app --reload --port 8000
```
You should see `Uvicorn running on http://127.0.0.1:8000`. Test it by
opening http://localhost:8000/health in a browser — should show
`{"status":"ok"}`.

### 7. Run the frontend
Open a **second terminal** in VS Code (click the `+` icon in the terminal
panel) so the backend keeps running:
```bash
cd frontend
python3 -m http.server 5500
```
Open http://localhost:5500 — you should see the ats-scan form. Try a full
scan with a real resume and JD to confirm the whole pipeline works
end-to-end before deploying.

If something breaks, the error will show in whichever terminal is running
that piece — backend errors in the `uvicorn` terminal, frontend/network
errors in the browser console (`F12`).

---

## PART 2 — Get a live link

Plan: backend → **Render** (free tier), frontend → **Vercel** (free tier).
Both deploy straight from GitHub.

### 1. Push the project to GitHub
Create a `.gitignore` in the project root (VS Code: right-click root folder
→ New File):
```
backend/venv/
backend/__pycache__/
backend/.env
*.pyc
```

In the VS Code terminal, at the project root:
```bash
git init
git add .
git commit -m "Initial commit: ATS gap detector"
```

Create a new repo on GitHub (github.com/new), name it `ats-gap-detector`,
**don't** initialize with a README (you already have one). Then:
```bash
git remote add origin https://github.com/Sufiitrq1/ats-gap-detector.git
git branch -M main
git push -u origin main
```

### 2. Deploy the backend on Render
1. Go to https://render.com → sign up with GitHub
2. **New +** → **Web Service** → connect your `ats-gap-detector` repo
3. Fill in:
   - **Name**: `ats-gap-detector-api` (this becomes part of your URL)
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free
4. Under **Environment Variables**, add each one from your `.env` file:
   - `ANTHROPIC_API_KEY`
   - `RESEND_API_KEY`
   - `FROM_EMAIL` → `onboarding@resend.dev`
   - `ALLOWED_ORIGINS` → leave blank for now, you'll fill this in after
     step 3 once you know your frontend URL
5. Click **Create Web Service**. First deploy takes 2-5 minutes.
6. Once live, you'll get a URL like `https://ats-gap-detector-api.onrender.com`.
   Test it: visit `https://ats-gap-detector-api.onrender.com/health`.

**Free tier note**: Render's free web services spin down after 15 minutes
of no traffic and take ~30-50 seconds to wake up on the next request. Fine
for a portfolio/demo link; upgrade to a paid instance ($7/mo) if you want
it always-warm.

### 3. Deploy the frontend on Vercel
1. First, point the frontend at your live backend. In VS Code, open
   `frontend/index.html`, find this line near the bottom:
   ```js
   const API_URL = "http://localhost:8000/analyze";
   ```
   Change it to:
   ```js
   const API_URL = "https://ats-gap-detector-api.onrender.com/analyze";
   ```
   Save, then commit and push:
   ```bash
   git add frontend/index.html
   git commit -m "Point frontend at live backend"
   git push
   ```
2. Go to https://vercel.com → sign up with GitHub
3. **Add New** → **Project** → import your `ats-gap-detector` repo
4. Set **Root Directory** to `frontend`
5. Framework Preset: **Other** (it's static HTML, no build step needed)
6. Click **Deploy**. Takes about 30 seconds.
7. You'll get a live link like `https://ats-gap-detector.vercel.app`

### 4. Close the loop — fix CORS
Go back to Render → your backend service → **Environment** → edit
`ALLOWED_ORIGINS` and set it to your actual Vercel URL:
```
https://ats-gap-detector.vercel.app
```
Save — Render will auto-redeploy with the new setting (~1 min).

### 5. Test the live version
Open your Vercel link, run a real scan. First request may take ~40s if
Render's free instance was asleep — that's expected, not a bug.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| CORS error in browser console | `ALLOWED_ORIGINS` on Render doesn't match your Vercel URL exactly (check http vs https, trailing slash) |
| 502/504 on first request | Render free instance waking up — wait 30-50s and retry |
| Email not arriving | Check spam folder; Resend free tier caps at 100/day; check Render logs for the actual error |
| `ModuleNotFoundError` locally | Your VS Code interpreter isn't pointed at `venv` — redo step 4 in Part 1 |
| Resume upload fails silently | File over 5MB, or it's a scanned/image PDF with no extractable text |

## What to do with the live link
Put it in your LinkedIn bio/posts, or link it from your portfolio site —
it's a working AI tool built end-to-end (FastAPI + Claude API + email
delivery), which is a strong DevOps/full-stack talking point for
interviews: you can speak to the deploy pipeline, env var management,
and CORS/service-to-service config, not just the code.
