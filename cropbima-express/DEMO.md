# 🎤 CropBima Express — Hackathon Demo Guide (5 minutes)

**One-liner:** Voice-first PMFBY claim kiosk — farmer uploads a 7/12 photo,
Sarvam Vision digitises it, Saaras voice fills the gaps, Bulbul speaks back,
claim submitted with PDF receipt.

## 0. Project map (what lives where)
```
cropbima-express/
├── backend/
│   ├── app/main.py                  # FastAPI + serves kiosk at /app
│   ├── app/config.py                # SARVAM_API_KEY, MOCK_MODE
│   ├── app/services/
│   │   ├── sarvam_doc_service.py    # Vision digitise+extract (live) / mock
│   │   ├── sarvam_voice_service.py  # Saaras v4 STT + Bulbul v3 TTS (live) / mock
│   │   ├── claim_rules_engine.py    # PMFBY audit + Marathi/Hindi prompts + voice merge
│   │   └── translation_service.py   # translate helper
│   ├── app/routes/                  # documents / voice / claims APIs
│   ├── app/models/                  # SQLite claim table + schemas
│   ├── .env                         # ← YOUR LIVE KEY IS HERE (MOCK_MODE=false) ✅
│   └── requirements.txt
├── frontend/                        # NO React — plain HTML/CSS/JS, zero build
│   ├── index.html  styles.css  app.js
│   └── assets/sample_khasra.svg     # demo 7/12 doc
├── test_data/                       # mock payload + sample record text
└── README.md
```

## 1. Run it (30 seconds)
```powershell
cd cropbima-express/backend
python -m uvicorn app.main:app --port 8000
```
| URL | What |
|---|---|
| http://localhost:8000/app | 📱 Kiosk UI (demo this!) |
| http://localhost:8000/docs | Swagger APIs |
| http://localhost:8000/health | `{"mock_mode": false}` = LIVE ✅ |

No `npm install`, no build — kiosk is served by FastAPI itself.

## 2. The 5-minute demo script (follow exactly)
1. **Hook (30s):** "PMFBY claims fail because 7/12 extracts are handwritten in
   Marathi/Hindi and farmers can't fill English portals. We made a kiosk that
   listens." Open `/app`.
2. **Upload (60s):** Click **✨ Use sample doc** → narrate: "Sarvam Vision
   (`doc_ai.digitise` + `extract`) is OCR-ing the 7/12…" Fields appear.
3. **Audit gap (60s):** **🔍 Run PMFBY audit** → `loss_date` missing →
   Hindi prompt shows: *"नुकसान की तारीख समझ नहीं आ रही…"* Click
   **🔊 Listen prompt** (Bulbul v3 speaks it — judges hear it!).
4. **Voice fill (90s):** Click **🎤 Speak** and read the Marathi line on the
   sample doc: *"पाऊस 18 सप्टेंबर, सोयाबीनचे साठ टक्के नुकसान"*
   → Saaras v4 transcribes → `loss_date=2026-09-18`, `damage=60%` auto-fill ✅
5. **Submit (30s):** **✅ Submit** → `PMFBY-2026-000001` reference + JSON +
   **🧾 Receipt PDF**. Mention helpline 14447.
6. **Close (30s):** Flip to `/docs` — "Every step is an API: STT, TTS, audit,
   voice-fill — works without a key in MOCK_MODE too."

## 3. If internet dies (fallback)
Set `MOCK_MODE=true` in `backend/.env`, restart — same UI flow with canned
Ramesh Patil data. Mention it: "graceful offline demo mode."

## 4. What to say about Sarvam usage (judges ask this)
- **Vision:** `client.doc_ai.digitise(file=[...], output_format="md")` poll
  `get_status` → `get_download_url`; then `extract(schema=CLAIM_SCHEMA)`.
- **STT:** `client.speech_to_text.transcribe(file, model="saaras:v4", mode="transcribe")`
  → transcript + `language_code` auto-detect (Marathi/Hinglish/noisy audio).
- **TTS:** `client.text_to_speech.convert(text, language_code, model="bulbul:v3", speaker="simran")`
  → base64 WAV (note: `anushka` is v2-only — we use `simran`).
- **Translate:** `client.text.translate(...)` verified live with your key.

## 5. Files to show judges
- `backend/.env` → live key, `MOCK_MODE=false`
- `smoke.py` output (already verified: HEALTH/AUDIT/VOICEFILL/TTS/SUBMIT/PDF all ✅)
- `test_data/mock_claim_payload.json` → missing-field test case
