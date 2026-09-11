# Architecture — Loop

---

## 1. High-Level Component Diagram

```
┌────────────────────┐
│   React Frontend     │  Chat UI, session summary, progress view
└──────────┬───────────┘
           │ REST (JSON) + optionally WebSocket for streaming replies
┌──────────▼───────────┐
│   FastAPI Backend      │  Session orchestration, auth (single demo user), request validation
└──────────┬───────────┘
           │
┌──────────▼─────────────────────────────────────────┐
│              LangGraph Orchestrator                   │
│  (state graph wiring the 5 agents together, see §3)    │
└───┬───────────┬───────────┬───────────┬───────────────┘
    │           │           │           │
┌───▼───┐  ┌────▼────┐ ┌────▼─────┐ ┌───▼──────────┐
│Placement│ │Conversation│ │Error-  │ │Curriculum/    │
│Agent    │ │Partner Agent│ │Analysis│ │Scheduler Agent│
└─────────┘ └──────┬──────┘ │Agent   │ └───┬───────────┘
                    │         └────────┘     │
                    │  RAG retrieval          │ reads/writes
                    ▼                         ▼
           ┌─────────────────┐      ┌───────────────────┐
           │  ChromaDB/FAISS   │      │     MongoDB         │
           │  (leveled vocab   │      │  (learner profile,  │
           │   bank, embedded  │      │   review schedule,  │
           │   via HF          │      │   mistake tags,     │
           │   sentence-       │      │   conversation log) │
           │   transformers)   │      └───────────────────┘
           └─────────────────┘
```

Agent tools (`get_due_items`, `log_error_tag`, `fetch_level_vocab`, `schedule_next_review`) are wrapped as an **MCP server** sitting between the LangGraph nodes and the data layer — see §5. This is additive: the system works with direct function calls too; MCP is the "should have" wrapper around the same functions.

## 2. Request Lifecycle — One Daily Loop

```
1. Client → POST /session/start {user_id}
2. Backend → LangGraph.invoke(state={user_id, mode: "daily_loop"})
3. Orchestrator → Curriculum Agent: get due items + last session's tagged mistakes
4. Orchestrator → Conversation Partner Agent:
     - RAG-retrieve level-appropriate vocab
     - Generate opening line of roleplay, seeded with 1-2 due/mistake items
5. Client ↔ Backend: turn-by-turn exchange (POST /session/turn)
     - Each learner turn → Error-Analysis Agent tags mistakes (async, non-blocking to the chat)
6. After N turns (3-5) → Orchestrator → Curriculum Agent:
     - Update FSRS state for items touched this session
     - Persist new mistake tags
7. Backend → Client: POST /session/summary response
     {mastery_delta, next_review_eta, tagged_mistakes_this_session}
```

## 3. LangGraph State Graph

**Shared state object** (passed between nodes, superset of what any single node needs):

```python
class LoopState(TypedDict):
    user_id: str
    mode: Literal["placement", "daily_loop", "review_only"]
    level: str                      # "A1".."B1" — set by Placement, read by others
    due_items: list[dict]           # from Curriculum Agent
    conversation_history: list[dict]
    turn_count: int
    tagged_mistakes: list[dict]     # accumulated during this session
    session_summary: dict | None
```

**Node wiring:**

```
START
  → placement_agent            (only if mode == "placement" or first-ever session)
  → curriculum_agent_pull       (fetch due_items + prior mistake tags)
  → conversation_partner_agent  (loop: generate turn ↔ receive learner reply)
      ↳ error_analysis_agent    (runs after each learner reply, appends to tagged_mistakes)
  → curriculum_agent_update     (reschedule touched items, persist new tags)
  → END (returns session_summary)
```

Conditional edge: after `conversation_partner_agent`, loop back to itself while `turn_count < max_turns`; otherwise proceed to `curriculum_agent_update`.

## 4. RAG Grounding (why the Conversation Agent doesn't drift above level)

- **Store:** ChromaDB collection `vocab_bank`, documents = example sentences, metadata = `{lemma, cefr_level, pos, theme}`.
- **Embeddings:** Hugging Face `sentence-transformers/all-MiniLM-L6-v2` (or similar — small, fast, good enough for a leveled vocab bank).
- **Query pattern:** before generating a line, the Conversation Agent queries `vocab_bank` filtered to `cefr_level <= learner.level`, biased toward the learner's `theme` (travel/family/work) and any due items from the Curriculum Agent.
- **Failure mode this prevents:** an ungrounded LLM tends to reach for whatever vocabulary is statistically common in its training data for a topic, which is frequently above a true beginner's level. Filtering retrieval by level keeps generation inside the learner's zone.

## 5. MCP Tool Layer

Expose these as MCP tools rather than hardcoded Python function calls inside the LangGraph process:

| Tool | Called by | Purpose |
|---|---|---|
| `get_due_items(user_id)` | Curriculum Agent | Returns items due per FSRS state |
| `fetch_level_vocab(level, theme, k)` | Conversation Partner Agent | RAG query against ChromaDB |
| `log_error_tag(user_id, item, error_type, severity)` | Error-Analysis Agent | Writes a mistake tag to MongoDB |
| `schedule_next_review(user_id, item, outcome)` | Curriculum Agent | Updates FSRS ease/interval for one item |
| `get_learner_profile(user_id)` | Placement Agent, Orchestrator | Reads level, goal, history summary |

Why bother: it decouples "which agent framework calls this" from "what the tool does" — you can swap LangGraph for CrewAI without rewriting the tools, and it's a concrete, demoable answer to "is this just a wrapper around one prompt." See API-SPEC.md §3 for exact tool schemas.

## 6. Tech Stack Summary

| Layer | Choice |
|---|---|
| Frontend | React |
| Backend | FastAPI + Uvicorn |
| Agent orchestration | LangGraph (primary), LangChain for tool wrapping |
| Tool layer | MCP server |
| LLMs | Gemini Pro (conversation, error analysis), Groq (low-latency review prompts) |
| Vector store | ChromaDB (or FAISS for fully local demo) |
| Embeddings | Hugging Face sentence-transformers |
| Database | MongoDB |
| Deployment | Docker, Hugging Face Spaces / Render / Vercel |

## 7. Deployment Diagram (demo-scale)

```
Docker Compose
  ├── frontend   (React, served static or via Vite dev server)
  ├── backend    (FastAPI + LangGraph + MCP server, one container)
  └── mongo      (MongoDB, one container)

ChromaDB: embedded/local mode inside the backend container (no separate service needed at demo scale)
```

No message queue, no separate microservices — a single backend container is sufficient for a hackathon demo and avoids infra you'd have to debug live.
