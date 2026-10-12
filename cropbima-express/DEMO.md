# 🎤 CropBima Express — Hackathon Demo Guide (5 minutes)

**One-liner:** Farmer uploads a handwritten PMFBY form + 7/12 extract →
Sarvam Vision reads all 10 Devanagari fields → 7/12 cross-verifies →
voice fills gaps (Saaras) → Bulbul speaks back → claim + PDF receipt.

## 0. Project map
```
cropbima-express/
├── backend/
│   ├── app/main.py               # FastAPI + kiosk at /app
│   ├── app/services/
│   │   ├── sarvam_doc_service.py # Vision: COMPLAINT_SCHEMA (10 fields) + LAND_SCHEMA,
│   │   │                         # Devanagari-digit→ISO normalize, ha→acre, merge+verify
│   │   ├── sarvam_voice_service.py # Saaras v4 STT + Bulbul v3 TTS (simran)
│   │   ├── claim_rules_engine.py   # PMFBY audit + 5-language prompts + voice merge
│   ├── app/routes/  documents (/process, /process-pair) · voice · claims
│   ├── .env  → LIVE key, MOCK_MODE=false ✅
├── frontend/  plain HTML/CSS/JS — two upload slots (form + 7/12), verification cards
│   └── assets/sample_pmfby_form.png + sample_712_extract.png  ← YOUR real samples
├── test_data/ same two PNGs + mock payload
└── DEMO.md (this file)
```

## 1. Run (server already live; if needed)
```powershell
cd cropbima-express/backend
python -m uvicorn app.main:app --port 8000
```
Kiosk http://localhost:8000/app · APIs /docs · health /health (`mock_mode:false`)

## 2. The 5-minute script — with YOUR documents
1. **Hook (30s):** "PMFBY fails on paper: this handwritten Marathi form +
   this blurred 7/12. Our kiosk reads both and talks to the farmer."
2. **Upload (60s):** Click **✨ Use my sample docs** → previews appear →
   **⚙️ Process both documents**. Narrate: "Extract schema pulls fields
   1–10: रामभरोसे पटेल, 101/2/ब, भात, 0.3490 हेक्टर, 14/08/2026,
   अतिवृष्टि एवं बाढ़, 80%, 9876543210 — Devanagari digits normalized,
   hectare→0.86 acres."
3. **Cross-check (45s):** Point at verification cards: "Survey 101/2/ब ✅
   matches the 7/12; name ⚠️ differs (claimant vs holder काशिनाथ विठ्ठल पाटील)
   — the system flags family/holder mismatches instead of silently passing."
   7/12 also confirms crop भात + Raigad district.
4. **Audit+voice (75s):** **🔍 Run PMFBY audit** → eligible ✅ (or speak a
   correction) → **🔊 Listen prompt** → **🎤 Speak** a Marathi correction →
   Saaras fills it live.
5. **Submit (30s):** **✅ Submit** → `PMFBY-2026-00000X` + JSON + **🧾 PDF**.
   "Helpline 14447 on the receipt."
6. **Close (30s):** `/docs` → "process-pair, stt, tts, audit, voice-fill —
   and MOCK_MODE=true replays the same flow offline."

## 3. Verified live (Oct 12, your files)
- Form extract: all 10 fields correct (incl. १०१/२/ब, ०.३४९० हेक्टर, ८०%)
- 7/12: holder काशिनाथ विठ्ठल पाटील, survey 101/2/ब, crop भात, Raigad
- Merged → audit eligible ✅ → claim created → submitted (PMFBY-2026-000002) ✅
- TTS Bulbul v3 (`simran`) 158KB WAV ✅ · STT Saaras v4 ✅

## 4. If offline
`MOCK_MODE=true` → same UI with रामभरोसे पटेल canned data.

