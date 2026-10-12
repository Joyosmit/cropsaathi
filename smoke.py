"""Boot + smoke test CropBima backend (live key)."""
import asyncio, json, sys, os
os.chdir("cropbima-express/backend")
sys.path.insert(0, os.getcwd())
from httpx import AsyncClient, ASGITransport
from app.main import app

async def main():
    from app.models.db_models import Base
    from app.routes.claim_routes import engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    t = ASGITransport(app=app)
    async with AsyncClient(transport=t, base_url="http://t") as c:
        r = await c.get("/health"); print("HEALTH:", r.json())
        r = await c.post("/api/v1/claims/audit", json={"data": {"farmer_name": "Ramesh Patil", "survey_khasra_number": "123/4", "land_area_acres": 2.5, "district_state": "Nashik", "crop_type": "Soybean", "damage_reason": "", "damage_percentage": 60, "loss_date": ""}, "language": "hi-IN"})
        print("AUDIT:", json.dumps(r.json(), ensure_ascii=False)[:400])
        r = await c.post("/api/v1/claims/voice-fill", json={"data": {"farmer_name": "", "survey_khasra_number": "", "land_area_acres": None, "crop_type": "", "damage_reason": "", "loss_date": ""}, "transcript": "माझं नाव रमेश पाटील, गट नंबर 123/4", "language": "mr-IN"})
        print("VOICEFILL:", json.dumps(r.json(), ensure_ascii=False)[:400])
        r = await c.post("/api/v1/voice/tts", json={"text": "आपके दस्तावेज़ से नुकसान की तारीख समझ नहीं आ रही है।", "language_code": "hi-IN", "speaker": "simran"})
        print("TTS:", r.status_code, r.headers.get("content-type"), len(r.content), "bytes")
        r = await c.post("/api/v1/claims", json={"farmer_name": "Ramesh Patil", "survey_khasra_number": "123/4", "land_area_acres": 2.5, "district_state": "Nashik, Maharashtra", "crop_type": "Soybean", "damage_reason": "Excess Rainfall", "damage_percentage": 60, "loss_date": "2026-09-18", "language": "hi-IN"})
        print("CREATE:", r.json())
        cid = r.json()["id"]
        r = await c.post(f"/api/v1/claims/{cid}/submit"); print("SUBMIT:", r.json())
        r = await c.get(f"/api/v1/claims/{cid}/receipt.pdf"); print("PDF:", r.status_code, len(r.content))

asyncio.run(main())
