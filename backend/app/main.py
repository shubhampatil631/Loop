from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import onboarding, session, review, progress, admin
from app.tools.mcp_server import mcp_router
from app.rag.vocab_store import vocab_store

app = FastAPI(
    title="Loop AI Language Learning API",
    description="Agent-Orchestrated Conversational Language Tutor with Spaced Repetition",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(onboarding.router)
app.include_router(session.router)
app.include_router(review.router)
app.include_router(progress.router)
app.include_router(admin.router)
app.include_router(mcp_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": "Loop API",
        "target_language": settings.TARGET_LANGUAGE,
        "env": settings.ENV
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": str(exc)}}
    )

@app.on_event("startup")
def on_startup():
    print("[Server] Loop API started successfully.")
    # Ensure vocabulary bank is initialized and populated
    chroma_count = vocab_store.collection.count() if (vocab_store.is_chroma_ready and vocab_store.collection) else 0
    if chroma_count == 0 and not vocab_store.in_memory_docs:
        from scripts.seed_vocab_bank import seed_vocab
        seed_vocab()
    print(f"[Server] RAG Grounding ready. ChromaDB count: {chroma_count}, Memory count: {len(vocab_store.in_memory_docs)}")

