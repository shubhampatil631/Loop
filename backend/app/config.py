import os
from pathlib import Path
from dotenv import load_dotenv

# Load env variables immediately
root_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=root_dir / ".env")
load_dotenv()  # Fallback for current working directory

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    _raw_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    OLLAMA_HOST: str = _raw_host.replace("localhost", "127.0.0.1")
    OLLAMA_TIMEOUT: float = float(os.getenv("OLLAMA_TIMEOUT", "45.0"))
    OLLAMA_KEEP_ALIVE: str = os.getenv("OLLAMA_KEEP_ALIVE", "30m")
    raw_models: str = os.getenv("OLLAMA_MODELS", "qwen2.5:1.5b,phi3:mini,llama3.2:1b")
    _parsed = [m.strip() for m in raw_models.split(",") if m.strip()]
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", _parsed[0] if _parsed else "qwen2.5:1.5b")
    if OLLAMA_MODEL and OLLAMA_MODEL not in _parsed:
        _parsed.insert(0, OLLAMA_MODEL)
    OLLAMA_MODELS: list = _parsed
    MONGO_URI: str = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI", "mongodb://localhost:27017/loop")
    _raw_chroma: str = os.getenv("CHROMA_PERSIST_DIR", "")
    if _raw_chroma:
        _chroma_path = Path(_raw_chroma)
        if not _chroma_path.is_absolute():
            backend_chroma = Path(__file__).resolve().parent.parent / _raw_chroma
            CHROMA_PERSIST_DIR: str = str(backend_chroma.resolve()) if backend_chroma.exists() else str(_chroma_path.resolve())
        else:
            CHROMA_PERSIST_DIR: str = str(_chroma_path)
    else:
        CHROMA_PERSIST_DIR: str = str(Path(__file__).resolve().parent.parent / "chroma_data")

    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    TARGET_LANGUAGE: str = os.getenv("TARGET_LANGUAGE", "es")
    ENV: str = os.getenv("ENV", "development")

settings = Settings()
