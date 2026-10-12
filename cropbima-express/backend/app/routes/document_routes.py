"""Document endpoints: single process + form/land pair."""
from __future__ import annotations
import os
import uuid
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.config import settings
from app.services.sarvam_doc_service import process_document, process_pair

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])
ALLOWED = {"image/png", "image/jpeg", "image/jpg", "application/pdf", "image/webp",
           "image/svg+xml"}

async def _save(file: UploadFile) -> str:
    if file.content_type not in ALLOWED:
        raise HTTPException(400, f"Unsupported type {file.content_type}. Use PNG/JPG/PDF.")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "doc")[1] or ".png"
    dest = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    size = 0
    async with aiofiles.open(dest, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > settings.MAX_UPLOAD_MB * 1024 * 1024:
                raise HTTPException(413, "File too large")
            await out.write(chunk)
    return dest

@router.post("/process")
async def process(file: UploadFile = File(...), language: str = Form("auto"),
                  doc_type: str = Form("auto")):
    dest = await _save(file)
    try:
        result = await process_document(dest, language=language, doc_type=doc_type)
    except Exception as e:
        raise HTTPException(502, f"Document AI failed: {e}")
    result["uploaded_as"] = file.filename
    return result

@router.post("/process-pair")
async def process_both(form: UploadFile | None = File(None),
                       land_record: UploadFile | None = File(None),
                       language: str = Form("auto")):
    """Upload PMFBY complaint form + 7/12 extract together; returns merged claim."""
    if not form and not land_record:
        raise HTTPException(400, "Upload at least one file (form and/or land_record).")
    fp = await _save(form) if form else None
    lp = await _save(land_record) if land_record else None
    try:
        return await process_pair(fp, lp, language)
    except Exception as e:
        raise HTTPException(502, f"Document AI failed: {e}")
