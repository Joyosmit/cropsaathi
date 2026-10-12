# 🚀 Deploying CropBima Express

> **TL;DR — use Render (or Railway/Fly), not Vercel**, unless you accept
> Vercel's limits below. One service serves both the kiosk (`/app`) and APIs.

## Option A — Render ⭐ (recommended, ~5 min, free)
1. Push `cropbima-express/` to GitHub (**do NOT commit `backend/.env`** —
   it has your live key).
2. https://dashboard.render.com → New → **Blueprint** → select repo
   (`render.yaml` is already in the project root).
   Or New → Web Service manually:
   - Root directory: `cropbima-express`
   - Build: `pip install -r backend/requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` with
     env `PYTHONPATH=backend`
3. Environment variables:
   - `SARVAM_API_KEY` = your key (paste from `backend/.env`)
   - `MOCK_MODE` = `false`
4. Deploy → open `https://<your-app>.onrender.com/app` ✅
   - Free tier spins down after idle; first load ~30s. For the hackathon,
     open the URL 2 min before stage, or use Starter ($7/mo, always-on).

**Same steps work for Railway** (Root Directory `cropbima-express`,
same build/start) and **Fly.io** (`Dockerfile` included:
`fly launch` → `fly secrets set SARVAM_API_KEY=…`).

## Option B — Vercel ⚠️ (possible, with limits)
Files `vercel.json` + `api/index.py` are included, but know the trade-offs:
- ⏱️ Hobby functions time out at **60s**; `process-pair` on two PNGs takes
  ~15–40s live (fine) but can spike — keep uploads <4MB on Vercel.
- 💾 `/tmp` uploads + SQLite are **ephemeral**: claims/PDFs vanish between
  invocations. Fine for a demo, not for production.
- Steps: `vercel` CLI or dashboard → import repo → set env
  `SARVAM_API_KEY`, `MOCK_MODE=false` → deploy → kiosk at `/app`.
- If you hit timeouts, switch the demo to **MOCK_MODE=true** on Vercel
  (instant, no Sarvam polling).

## Pre-deploy checklist
- [ ] `backend/.env` in `.gitignore` (key must NOT go to GitHub)
- [ ] `pip freeze`-clean `requirements.txt` ✅ (pinned, `sarvamai==0.1.36`)
- [ ] Kiosk uses **relative `/api/...`** paths ✅ (works on any domain)
- [ ] Health check path: `/health`
- [ ] Judge backup: `MOCK_MODE=true` redeploys instantly with canned data
