import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", "./downloads"))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ── Restore NotebookLM auth from env var ──────────────────────────────────────
_storage_b64 = os.getenv("NOTEBOOKLM_STORAGE_STATE")
if _storage_b64:
    _storage_path = Path("/root/.notebooklm/storage_state.json")
    _storage_path.parent.mkdir(parents=True, exist_ok=True)
    _storage_path.write_bytes(base64.b64decode(_storage_b64))

app = FastAPI(title="NotebookLM Backend", version="1.0.0", redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://frontend-organiza-o-estudos.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

from routers import notebooks, sources, chat, artifacts  # noqa: E402

app.include_router(notebooks.router, prefix="/api/notebooks", tags=["notebooks"])
app.include_router(sources.router, prefix="/api/notebooks", tags=["sources"])
app.include_router(chat.router, prefix="/api/notebooks", tags=["chat"])
app.include_router(artifacts.router, prefix="/api/notebooks", tags=["artifacts"])

# ── Static files (artefatos gerados) ─────────────────────────────────────────

app.mount("/files", StaticFiles(directory=str(DOWNLOAD_DIR)), name="files")

# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/debug-cors")
async def debug_cors():
    return {"allowed_origins": ALLOWED_ORIGINS}


# ── Global error handler ──────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    exc_type = type(exc).__name__
    detail = str(exc)

    # Auth expirada
    if "auth" in detail.lower() or "login" in detail.lower() or "cookie" in detail.lower() or "session" in detail.lower():
        return JSONResponse(
            status_code=401,
            content={
                "error": "Sessão expirada",
                "detail": "Sessão expirada. Execute `notebooklm login` no terminal.",
            },
        )

    # Não encontrado
    if "not found" in detail.lower() or "404" in detail:
        return JSONResponse(
            status_code=404,
            content={"error": "Recurso não encontrado", "detail": detail},
        )

    # Timeout
    if "timeout" in detail.lower() or exc_type == "TimeoutError":
        return JSONResponse(
            status_code=504,
            content={"error": "Timeout na geração do artefato", "detail": detail},
        )

    return JSONResponse(
        status_code=500,
        content={"error": "Erro interno do servidor", "detail": detail},
    )
