"""Live pair test on user's real samples."""
import asyncio, json, sys, os
os.chdir("cropbima-express/backend")
sys.path.insert(0, os.getcwd())
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.db_models import Base
from app.routes.claim_routes import engine

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    t = ASGITransport(app=app)
    async with AsyncClient(transport=t, base_url="http://t") as c:
        with open("../test_data/sample_pmfby_form.png", "rb") as f1, \
             open("../test_data/sample_712_extract.png", "rb") as f2:
            files = {"form": ("sample_pmfby_form.png", f1, "image/png"),
                     "land_record": ("sample_712_extract.png", f2, "image/png")}
            r = await c.post("/api/v1/documents/process-pair", files=files, timeout=180)
        print("PAIR STATUS:", r.status_code)
        out = r.json()
        print("FORM:", json.dumps(out.get("form", {}), ensure_ascii=False)[:800])
        print("LAND:", json.dumps(out.get("land", {}), ensure_ascii=False)[:800])
        print("MERGED:", json.dumps(out.get("merged", {}), ensure_ascii=False)[:1200])
        m = out.get("merged", {})
        r2 = await c.post("/api/v1/claims/audit", json={"data": m, "language": "hi-IN"})
        print("AUDIT:", json.dumps(r2.json(), ensure_ascii=False)[:500])
        r3 = await c.post("/api/v1/claims", json={**{k: m.get(k) for k in
            ["farmer_name","father_name","survey_khasra_number","land_area_acres","land_area_hectare",
             "village_taluka_district","district_state","crop_type","damage_reason","damage_percentage",
             "loss_date","mobile_number"]}, "language": "hi-IN"})
        print("CREATE:", r3.status_code, json.dumps(r3.json(), ensure_ascii=False)[:400])
        if r3.status_code == 200:
            cid = r3.json()["id"]
            r4 = await c.post(f"/api/v1/claims/{cid}/submit")
            print("SUBMIT:", json.dumps(r4.json(), ensure_ascii=False)[:500])

asyncio.run(main())
