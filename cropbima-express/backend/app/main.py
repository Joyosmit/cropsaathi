"""FastAPI entrypoint."""
from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import document_routes, voice_routes, claim_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.models.db_models import Base
    from app.routes.claim_routes import engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="CropBima Express", version="1.0.0",
              description="Voice-first PMFBY crop insurance claim assistant (Sarvam AI)",
              lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*",])

app.include_router(document_routes.router)
app.include_router(voice_routes.router)
app.include_router(claim_routes.router)

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
FRONTEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.isdir(FRONTEND):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND, "assets")), name="assets")
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")

    @app.get("/app", include_in_schema=False)
    async def kiosk():
        return FileResponse(os.path.join(FRONTEND, "index.html"))

@app.get("/")
async def root():
    return {"service": "CropBima Express", "docs": "/docs", "health": "/health"}

@app.get("/health")
async def health():
    from app.config import use_mock
    return {"status": "ok", "mock_mode": use_mock()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
