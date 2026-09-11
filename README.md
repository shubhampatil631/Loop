# Loop 🔄
> **Autonomous Multi-Agent Conversational Language Learning System with Spaced-Repetition Memory & Dynamic Error Retriggering**  
> *Built for Nerdy AI Hackathon Challenge — Track: Autonomous Language Learning Agents*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent_Workflow-blueviolet)](https://github.com/langchain-ai/langgraph)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_RAG-orange)](https://www.trychroma.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas_%26_Local-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com)
[![React](https://img.shields.io/badge/React_18-TypeScript_%2B_Vite-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![MCP](https://img.shields.io/badge/MCP-Model_Context_Protocol-purple)](https://modelcontextprotocol.io)

---

## 📌 Executive Summary

Most language apps are static flashcards or open-ended chatbots that fail to reinforce retention or correct mistakes systematically. **Loop** is a production-ready, agent-orchestrated conversational language tutor.

Loop conducts real-time conversational roleplays, silently analyzes grammatical and lexical errors in the background without breaking immersion, tracks spaced-repetition memory curves (FSRS algorithm), and dynamically re-injects past mistakes and overdue vocabulary into future conversational scenarios.

```
                               ┌───────────────────────────────────────────────────────────┐
                               │                    FastAPI REST / MCP                     │
                               └─────────────────────────────┬─────────────────────────────┘
                                                             │
                                                             ▼
                                     ┌───────────────────────────────────────────────┐
                                     │         LangGraph Multi-Agent Runtime         │
                                     └───────┬───────────────┬───────────────┬───────┘
                                             │               │               │
        ┌────────────────────────────────────┴──┐            │               └────────────────────────────────────┐
        ▼                                       ▼            ▼                                                    ▼
┌──────────────┐                        ┌──────────────┐ ┌──────────────┐                                 ┌──────────────┐
│  Placement   │                        │ Conversation │ │Error-Analysis│                                 │  Curriculum  │
│    Agent     │                        │Partner Agent │ │    Agent     │                                 │  Scheduler   │
└───────┬──────┘                        └───────┬──────┘ └───────┬──────┘                                 └───────┬──────┘
        │ (CEFR Baseline A1-B2)                 │                │ (Silent Mistake Classification)                │
        ▼                                       ▼                ▼                                                ▼
┌──────────────┐                        ┌──────────────┐ ┌──────────────┐                                 ┌──────────────┐
│ Learner Node │                        │ ChromaDB RAG │ │ Mistake Tag  │                                 │ FSRS Memory  │
│ Profile Init │                        │ Grounded Vocab│ │ Extractor   │                                 │ Matrix & DB  │
└──────────────┘                        └──────────────┘ └──────────────┘                                 └──────────────┘
```

---

## 🤖 Multi-Agent Architecture & Orchestration

Loop runs a compiled **LangGraph** state graph where specialized agents coordinate over shared state:

| Agent | Module | Responsibility | Key Mechanics |
| :--- | :--- | :--- | :--- |
| **Placement Agent** | `app.agents.placement` | Diagnostic CEFR Evaluation | Conducts a 3–4 turn adaptive interview assessing grammatical range, vocabulary breadth, and fluency to assign baseline CEFR level (`A1`, `A2`, `B1`, `B2`). |
| **Conversation Partner** | `app.agents.conversation` | Immersive Roleplay | Executes scenario roleplay (e.g. cafe, airport, workplace) strictly grounded via **ChromaDB RAG** to the learner's CEFR ceiling while seamlessly surfacing scheduled review targets. |
| **Error-Analysis Agent** | `app.agents.error_analysis` | Non-Blocking Diagnostics | Runs asynchronously in the pipeline. Identifies, categorizes (`gender_agreement`, `conjugation`, `word_order`, `false_friend`, `lexical`), and scores error severity with explanations and corrections. |
| **Curriculum Scheduler** | `app.agents.curriculum` | Spaced Repetition (FSRS) | Computes stability, ease factors, repetition counts, and calculates next review dates according to memory decay curves. Re-queues failed items for conversational retriggering. |
| **Review Recall Agent** | `app.agents.review_recall` | Retention Verification | Tests targeted recall of prioritized vocabulary before conversations, measuring active recall latency and accuracy. |
| **Weekly Digest Agent** | `app.agents.weekly_digest` | Longitudinal Mastery | Aggregates learner progress over time, generating error heatmaps, retention velocity, and personalized study recommendations. |

---

## ⚡ Key Technical Innovations

### 1. Robust Multi-Tier LLM Fallback Engine
Loop guarantees 100% uptime through a 3-tier LLM fallback hierarchy managed in `app/llm.py`:
1. **Tier 1 (Cloud Primary)**: Google Gemini Flash 1.5 (`langchain-google-genai`)
2. **Tier 2 (Cloud Backup)**: Groq Llama-3.3-70b-versatile (`langchain-groq`)
3. **Tier 3 (Local Air-Gapped)**: Ollama (`qwen2.5:1.5b`, `llama3.2:1b`, `phi3:mini`)

### 2. RAG-Grounded Level-Appropriate Vocabulary (ChromaDB)
- **Zero Hallucination Guardrails**: Conversation Partner Agent queries ChromaDB (`all-MiniLM-L6-v2` embeddings) filtered by CEFR level hierarchy (`A1` ⊂ `A2` ⊂ `B1` ⊂ `B2`) and scenario theme aliases.
- Pre-seeded with 200+ curated vocabulary items with ease factors, example usages, and grammatical metadata.

### 3. FSRS Memory Engine & Dynamic Error Retriggering
- Implements Free Spaced Repetition Scheduler (`FSRS`) with adaptive interval scaling:
  - **Correct Outcome**: Interval $\times$ Ease Factor (capped at 3.0), advancing interval days.
  - **Incorrect / Lapse Outcome**: Ease reduced by $0.3$, interval reset to $1$ day, item tagged for retriggering.
  - **Hesitation Outcome**: Interval scaled by $0.7\times$ to reinforce weak retention.
- Re-injects past error tags into subsequent scenario prompts naturally without explicitly alerting the learner.

### 4. Standardized Model Context Protocol (MCP) Server
Loop exposes its internal toolchain via standard JSON-RPC 2.0 and REST MCP endpoints (`app/tools/mcp_server.py`):
- `get_due_items`: Queries flashcards/vocab items due for review according to FSRS schedules.
- `fetch_level_vocab`: Vector search filtered by CEFR tier and contextual theme.
- `log_error_tag`: Records mistake taxonomy with turn examples and corrections.
- `schedule_next_review`: Updates interval and ease metrics for vocabulary items.
- `get_learner_profile`: Returns user proficiency, CEFR level, and active mistake backlog.

---

## 🛠️ Complete Tech Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn, LangGraph, LangChain, Pydantic v2
- **Vector Database**: ChromaDB (Persistent client with cosine similarity)
- **Database**: MongoDB (Atlas Cloud & Local Mongo support via PyMongo)
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS / Custom Glassmorphism System
- **Integration**: Model Context Protocol (MCP) Server & Client Tools
- **Containerization**: Docker, Docker Compose

---

## 📂 Repository Structure

```
Loop/
├── backend/
│   ├── app/
│   │   ├── agents/            # Multi-agent LangGraph workflows
│   │   │   ├── conversation.py    # Conversation Partner agent
│   │   │   ├── curriculum.py      # FSRS scheduler & retrigger logic
│   │   │   ├── error_analysis.py  # Grammar/lexical mistake tagger
│   │   │   ├── graph.py           # LangGraph orchestration state machine
│   │   │   ├── placement.py       # CEFR baseline evaluator
│   │   │   ├── review_recall.py   # Active recall verification
│   │   │   └── weekly_digest.py   # Long-term progress digest
│   │   ├── models/            # Pydantic schemas (Learner, Session, Vocab, Mistakes)
│   │   ├── rag/               # ChromaDB vector store & auto-seeder
│   │   ├── routes/            # FastAPI routers (onboarding, session, review, progress, admin)
│   │   ├── tools/             # MCP Server & tool definitions
│   │   ├── config.py          # Unified settings with environment validation
│   │   ├── llm.py             # Multi-tier LLM engine (Gemini -> Groq -> Ollama)
│   │   └── main.py            # FastAPI entry point & CORS configuration
│   ├── chroma_data/           # Persistent ChromaDB vector store
│   ├── scripts/               # Complete automated test & verification suite
│   │   ├── seed_vocab_bank.py             # ChromaDB vocabulary bank seeder
│   │   ├── test_curriculum_scheduling.py  # FSRS algorithm unit verification
│   │   ├── test_error_analysis.py         # Mistake tagging validation
│   │   ├── test_langgraph_wiring.py       # Multi-agent graph execution test
│   │   ├── test_llm_fallback_and_app.py   # LLM fallback resilience test
│   │   ├── test_rag_grounding.py          # Vector retrieval accuracy test
│   │   ├── test_mcp_wrapper.py            # MCP tool dispatch test
│   │   ├── test_e2e_multi_user.py         # Multi-user isolation test
│   │   ├── verify_admin_and_db.py         # Database integrity verification
│   │   └── smoke_test.py                  # Full HTTP smoke test
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.ts      # Type-safe API client & state interfaces
│   │   ├── pages/             # Onboarding, DailyLoop, SessionSummary, Progress, LearnersDirectory
│   │   ├── App.tsx            # Navigation & routing
│   │   ├── index.css          # Design system, glassmorphism & animations
│   │   └── main.tsx           # React DOM root
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── docs/                      # PRD, Architecture, Data Models, Agent Specs, API Specs
├── docker-compose.yml         # One-command full-stack container orchestration
├── .env.example               # Documented environment variables template
└── README.md
```

---

## 🚦 Verified API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/onboarding/start` | Initiates CEFR placement diagnostic session |
| `POST` | `/onboarding/respond` | Submits learner turn, advances diagnostic, or returns final CEFR baseline |
| `POST` | `/session/start` | Generates roleplay scenario with RAG vocab targets & retriggered error items |
| `POST` | `/session/turn` | Processes conversational exchange with real-time error analysis |
| `POST` | `/session/end` | Finalizes session, computes mastery delta, and updates FSRS review schedules |
| `GET`  | `/review/due` | Queries due spaced-repetition vocabulary items for learner |
| `POST` | `/review/schedule` | Directly updates interval/ease for a reviewed vocabulary card |
| `GET`  | `/progress/dashboard`| Returns mastery scores, retention curves, and mistake breakdown |
| `GET`  | `/users` | Lists all learner profiles and current levels |
| `POST` | `/mcp/call` | Dispatches standard MCP tool calls (`get_due_items`, `fetch_level_vocab`, etc.) |
| `GET`  | `/health` | Service health status and active target language |

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- (Optional) Docker & Docker Compose
- Google Gemini API Key or Groq API Key

### 2. Environment Configuration
Create a `.env` file in the root directory:
```bash
cp .env.example .env
```
Fill in your API keys:
```env
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key

# MongoDB Connection (Local or Atlas)
MONGO_URI=mongodb://localhost:27017/loop

# Vector Store
CHROMA_PERSIST_DIR=./chroma_data
TARGET_LANGUAGE=es
ENV=production
```

### 3. Option A: Run with Docker Compose (Recommended)
```bash
docker-compose up --build
```
- **Frontend App**: [http://localhost:3000](http://localhost:3000)
- **Interactive OpenAPI / Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Option B: Run Locally

#### Backend
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python scripts/seed_vocab_bank.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run build    # Or 'npm run dev' for hot-reloading dev server
npm run preview
```

---

## 🧪 Automated Test & Verification Suite

All core systems have dedicated, reproducible test scripts in `backend/scripts/`:

```bash
# 1. Verify Spaced Repetition (FSRS) intervals & scheduling math
python backend/scripts/test_curriculum_scheduling.py

# 2. Verify Multi-Agent LangGraph workflow execution
python backend/scripts/test_langgraph_wiring.py

# 3. Verify ChromaDB RAG retrieval & CEFR hierarchical filtering
python backend/scripts/test_rag_grounding.py

# 4. Verify Error Analysis classification & severity scoring
python backend/scripts/test_error_analysis.py

# 5. Verify LLM multi-tier fallback resilience (Gemini -> Groq -> Ollama)
python backend/scripts/test_llm_fallback_and_app.py

# 6. Verify Model Context Protocol (MCP) tool endpoints
python backend/scripts/test_mcp_wrapper.py

# 7. Verify Multi-user state isolation & database transactions
python backend/scripts/test_e2e_multi_user.py
```

---

## 🏆 Summary of Hackathon Rubric Alignment

1. **Autonomous Multi-Agent Collaboration**: LangGraph coordinates Placement, Roleplay, Error Analysis, and Spaced Repetition agents seamlessly.
2. **Pedagogical Grounding**: FSRS mathematical decay modeling and CEFR-bound vector RAG guarantee educational efficacy.
3. **Resilience & Production Readiness**: Zero-downtime multi-tier LLM failover, comprehensive Docker configuration, and verified end-to-end test coverage.
4. **Interoperability**: Standard Model Context Protocol (MCP) server enables any external agent to interface with Loop's memory and curriculum.
