# CropBima Express — voice-first PMFBY claim assistant (Sarvam AI, LIVE ✅)

Backend: FastAPI (`cropbima-express/backend`) · Frontend: **plain HTML/CSS/JS, no build**
(`cropbima-express/frontend` — served by FastAPI at `/app`).

## Run (one terminal)
```powershell
cd cropbima-express/backend
python -m uvicorn app.main:app --port 8000
```
- Kiosk: http://localhost:8000/app
- APIs: http://localhost:8000/docs
- Health: http://localhost:8000/health  → `mock_mode:false` = live Sarvam key ✅

Key lives in `backend/.env` (`MOCK_MODE=false`). Verified live: translate,
Bulbul v3 TTS (`simran`), audit, voice-fill, claim submit, PDF receipt.
See `DEMO.md` for the 5-minute hackathon script.
