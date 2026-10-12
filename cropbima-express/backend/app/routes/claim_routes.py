"""Claim CRUD + audit + voice-fill + receipt PDF."""
from __future__ import annotations
import io
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.config import settings
from app.models.db_models import Base, Claim
from app.models.pydantic_schemas import (ClaimCreate, ClaimOut, AuditRequest, AuditResponse, VoiceFillRequest)
from app.services.claim_rules_engine import audit_claim, merge_voice_into_claim
from app.models.db_models import Base as _Base

async def _ensure_tables():
    async with engine.begin() as conn:
        await conn.run_sync(_Base.metadata.create_all)
        # lightweight migration for new columns on existing DBs
        try:
            from sqlalchemy import text
            for col, ddl in [
                ("father_name", "ALTER TABLE claims ADD COLUMN father_name VARCHAR(120) DEFAULT ''"),
                ("land_area_hectare", "ALTER TABLE claims ADD COLUMN land_area_hectare FLOAT"),
                ("village_taluka_district", "ALTER TABLE claims ADD COLUMN village_taluka_district VARCHAR(160) DEFAULT ''"),
                ("mobile_number", "ALTER TABLE claims ADD COLUMN mobile_number VARCHAR(15) DEFAULT ''"),
            ]:
                try:
                    await conn.execute(text(ddl))
                except Exception:
                    pass
        except Exception:
            pass

router = APIRouter(prefix="/api/v1/claims", tags=["claims"])
engine = create_async_engine(settings.DATABASE_URL, future=True)
Session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with Session() as s:
        yield s

@router.post("/audit", response_model=AuditResponse)
async def audit(body: AuditRequest):
    await _ensure_tables()
    return audit_claim(body.data, body.language)

@router.post("/voice-fill")
async def voice_fill(body: VoiceFillRequest):
    updated, filled = merge_voice_into_claim(body.data, body.transcript, body.target_field)
    return {"updated_data": updated, "filled_field": filled, "audit": audit_claim(updated, body.language)}

@router.post("", response_model=ClaimOut)
async def create_claim(body: ClaimCreate, db: AsyncSession = Depends(get_db)):
    await _ensure_tables()
    from app.models.db_models import Claim as _C
    cols = {c.name for c in _C.__table__.columns}
    vals = {k: v for k, v in body.model_dump().items() if k in cols}
    c = Claim(**vals, status="draft", claim_json=json.dumps(body.model_dump(), ensure_ascii=False))
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return ClaimOut(id=c.id, status=c.status, **body.model_dump())

@router.get("")
async def list_claims(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Claim).order_by(Claim.id.desc()).limit(50))).scalars().all()
    return [{"id": r.id, "farmer_name": r.farmer_name, "crop_type": r.crop_type,
             "status": r.status, "loss_date": r.loss_date} for r in rows]

@router.get("/{claim_id}", response_model=ClaimOut)
async def get_claim(claim_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.get(Claim, claim_id)
    if not r:
        raise HTTPException(404, "Claim not found")
    d = json.loads(r.claim_json or "{}")
    return ClaimOut(id=r.id, status=r.status, **{k: d.get(k, getattr(r, k, "")) for k in ClaimCreate.model_fields})

@router.post("/{claim_id}/submit")
async def submit_claim(claim_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.get(Claim, claim_id)
    if not r:
        raise HTTPException(404, "Claim not found")
    data = json.loads(r.claim_json or "{}")
    audit = audit_claim(data, r.language)
    if not audit["eligible"]:
        raise HTTPException(422, {"message": "Missing fields", "missing": audit["missing_fields"]})
    r.status = "submitted"
    await db.commit()
    ref = f"PMFBY-2026-{r.id:06d}"
    return {"claim_id": r.id, "reference": ref, "status": "submitted",
            "summary": data, "payout_hint": audit["payout_hint"]}

@router.get("/{claim_id}/receipt.pdf")
async def receipt(claim_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.get(Claim, claim_id)
    if not r:
        raise HTTPException(404, "Claim not found")
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(60, 780, "CropBima Express — PMFBY Claim Receipt")
    c.setFont("Helvetica", 12)
    data = json.loads(r.claim_json or "{}")
    y = 740
    c.drawString(60, y, f"Reference: PMFBY-2026-{r.id:06d}   Status: {r.status}")
    y -= 30
    for k, v in data.items():
        c.drawString(60, y, f"{k}: {v}")
        y -= 22
    c.drawString(60, 120, "Helpline: 14447 (PMFBY Toll Free)")
    c.save()
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=claim-{claim_id}.pdf"})
