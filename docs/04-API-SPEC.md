# API Specification — Loop

---

## 1. FastAPI REST Endpoints

### `POST /onboarding/start`
Kick off placement for a new user.
```json
// Request
{ "name": "Maya Demo", "target_language": "es", "goal": "travel" }

// Response
{ "user_id": "abc123", "placement_session_id": "sess001" }
```

### `POST /onboarding/placement/turn`
One turn of the 3–4 exchange placement conversation.
```json
// Request
{ "placement_session_id": "sess001", "learner_text": "Hola, me llamo Maya." }

// Response
{ "agent_text": "¡Hola Maya! ¿De dónde eres?", "placement_complete": false }
```
When `placement_complete: true`, response also includes `"level": "A2"`.

### `POST /session/start`
Begin a daily loop or review-only session.
```json
// Request
{ "user_id": "abc123", "mode": "daily_loop" }   // or "review_only"

// Response
{ "session_id": "sess045", "agent_text": "Buenos días! ¿Qué vas a pedir hoy en el café?" }
```

### `POST /session/turn`
Send one learner turn, get the agent's reply. Error-Analysis Agent runs async on the backend after this call; it does not block the response.
```json
// Request
{ "session_id": "sess045", "learner_text": "Quiero un café, por favor." }

// Response
{ "agent_text": "¡Perfecto! ¿Con leche o sin leche?", "turn_count": 2, "session_complete": false }
```

### `POST /session/end`
Force-end a session early (or called automatically when `turn_count` hits the max).
```json
// Response — SessionSummary shape (see DATA-MODELS.md §2)
{
  "session_id": "sess045",
  "mastery_delta": 0.03,
  "next_review_eta": "2026-09-05T09:00:00Z",
  "mistakes_this_session": [ { "error_type": "gender_agreement", "severity": "medium", "..." : "..." } ],
  "words_closer_to_fluent": 2
}
```

### `GET /review/due?user_id=abc123`
```json
{ "due_items": [ { "id": "v001", "lemma": "el café", "cefr_level": "A1" } ], "count": 6 }
```

### `GET /progress?user_id=abc123`
```json
{
  "mastery_score": 0.62,
  "words_graduated": 34,
  "words_in_progress": 12,
  "recent_mistakes": [ "..." ],
  "streak_days": 5
}
```

## 2. WebSocket (optional, for streaming conversation replies)

`WS /session/{session_id}/stream` — same payload shape as `/session/turn`, but the `agent_text` streams token-by-token instead of arriving as one blocking response. Not required for the MVP; add only if the typed-turn latency feels sluggish in testing.

## 3. MCP Tool Definitions

These back the agent nodes described in ARCHITECTURE.md §5. Each is a plain function wrapped as an MCP tool so any agent framework can call it identically.

```python
# tools/mcp_tools.py

def get_due_items(user_id: str, limit: int = 10) -> list[VocabItem]:
    """Return vocab_items due for review, ordered by due_at ascending."""

def fetch_level_vocab(level: str, theme: str, k: int = 5) -> list[dict]:
    """RAG query against ChromaDB vocab_bank, filtered to cefr_level <= level."""

def log_error_tag(user_id: str, vocab_item_id: str | None,
                   error_type: str, severity: str, example_turn: str) -> str:
    """Insert a mistake_tags document, return its id."""

def schedule_next_review(user_id: str, vocab_item_id: str,
                          outcome: Literal["correct", "incorrect", "hesitated"]) -> VocabItem:
    """Update ease_factor/interval_days/due_at for one item per the FSRS rule (see AGENT-SPECS.md)."""

def get_learner_profile(user_id: str) -> dict:
    """Return {level, goal, target_language, streak_days}."""
```

MCP tool manifest (what gets registered with the server):

```json
{
  "tools": [
    {"name": "get_due_items", "description": "Fetch vocab items due for review for a learner"},
    {"name": "fetch_level_vocab", "description": "Retrieve level-appropriate example sentences from the vocab bank"},
    {"name": "log_error_tag", "description": "Record a tagged mistake for a learner"},
    {"name": "schedule_next_review", "description": "Update spaced-repetition state for one vocab item"},
    {"name": "get_learner_profile", "description": "Fetch a learner's level, goal, and streak"}
  ]
}
```

## 4. Error Handling Conventions

- All endpoints return `{"error": {"code": "...", "message": "..."}}` with a 4xx/5xx status on failure — don't leak raw exceptions to the frontend.
- LLM call failures (Gemini/Groq timeout or rate limit) should fail over: Conversation Agent falls back from Gemini → Groq (or vice versa) rather than surfacing an error mid-conversation. This mirrors the failover pattern from PharmaFlow-AI.
- If `fetch_level_vocab` returns zero results for a level/theme combination, the Conversation Agent should widen the theme filter before widening the level filter — staying in-level matters more than staying on-theme.
