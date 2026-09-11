# Setup Guide — Loop

---

## 1. Repo Structure

```
loop/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entrypoint
│   │   ├── routes/
│   │   │   ├── onboarding.py       # /onboarding/*
│   │   │   ├── session.py          # /session/*
│   │   │   ├── review.py           # /review/*
│   │   │   └── progress.py         # /progress
│   │   ├── agents/
│   │   │   ├── graph.py            # LangGraph state graph wiring (ARCHITECTURE.md §3)
│   │   │   ├── placement.py
│   │   │   ├── conversation.py
│   │   │   ├── error_analysis.py
│   │   │   ├── curriculum.py
│   │   │   └── review_recall.py
│   │   ├── tools/
│   │   │   └── mcp_tools.py        # MCP tool definitions (API-SPEC.md §3)
│   │   ├── models/
│   │   │   ├── schemas.py          # Pydantic models (DATA-MODELS.md §2)
│   │   │   └── db.py               # Mongo collection helpers
│   │   ├── rag/
│   │   │   └── vocab_store.py      # ChromaDB/FAISS wrapper (DATA-MODELS.md §3)
│   │   └── config.py                # env var loading
│   ├── scripts/
│   │   └── seed_vocab_bank.py      # DATA-MODELS.md §4
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── Onboarding.tsx
│   │   │   ├── DailyLoop.tsx
│   │   │   ├── SessionSummary.tsx
│   │   │   └── Progress.tsx
│   │   └── api/
│   │       └── client.ts           # thin fetch wrapper around API-SPEC.md endpoints
│   ├── package.json
│   └── Dockerfile
├── docs/                            # this documentation set
├── docker-compose.yml
├── .env.example
└── README.md
```

## 2. Environment Variables (`.env.example`)

```bash
# LLM providers
GEMINI_API_KEY=
GROQ_API_KEY=

# Database
MONGO_URI=mongodb://mongo:27017/loop

# Vector store
CHROMA_PERSIST_DIR=./chroma_data

# App
TARGET_LANGUAGE=es
ENV=development
```

## 3. Backend Dependencies (`requirements.txt`)

```
fastapi
uvicorn[standard]
pydantic
pymongo
langgraph
langchain
langchain-google-genai
langchain-groq
chromadb
sentence-transformers
mcp
python-dotenv
```

## 4. Docker Compose

```yaml
version: "3.8"
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [mongo]
    volumes:
      - ./backend/chroma_data:/app/chroma_data

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]

  mongo:
    image: mongo:7
    ports: ["27017:27017"]
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

## 5. First-Time Setup

```bash
# 1. Clone / scaffold the repo structure above
git init loop && cd loop

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # fill in GEMINI_API_KEY, GROQ_API_KEY

# 3. Seed the vocab bank (one-time, before first run)
python scripts/seed_vocab_bank.py

# 4. Run backend locally (without Docker, for fast iteration)
uvicorn app.main:app --reload --port 8000

# 5. Frontend
cd ../frontend
npm install
npm run dev

# 6. OR run everything via Docker Compose once both sides work locally
cd ..
docker compose up --build
```

## 6. Smoke Test (run this after setup, before building further)

```bash
curl -X POST http://localhost:8000/onboarding/start \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "target_language": "es", "goal": "travel"}'
```
Expect a `user_id` and `placement_session_id` back. If this works, the FastAPI → LangGraph → Gemini/Groq → MongoDB path is wired correctly end to end — everything else is additive from here.

## 7. Common Setup Pitfalls

- **Chroma persistence path not writable inside Docker** — make sure the `chroma_data` volume mount in docker-compose matches `CHROMA_PERSIST_DIR` in `.env`.
- **Gemini/Groq key not loaded** — confirm `config.py` actually calls `load_dotenv()` before any agent module imports; a common bug is importing agents before env vars are loaded.
- **Mongo connection refused when running backend outside Docker** — `MONGO_URI` in `.env` should point to `localhost:27017` for local dev, `mongo:27017` only when the backend itself runs inside Docker Compose. Keep two `.env` variants (`.env.local`, `.env.docker`) if this gets confusing.
