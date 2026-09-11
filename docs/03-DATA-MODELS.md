# Data Models — Loop

---

## 1. MongoDB Collections

### `users`
```json
{
  "_id": "ObjectId",
  "name": "Maya Demo",
  "target_language": "es",
  "goal": "travel | family | work",
  "level": "A1",              // updated by Placement Agent, then drifts via Curriculum Agent
  "created_at": "ISODate",
  "last_session_at": "ISODate"
}
```

### `vocab_items` (per-user learning state — the FSRS "cards")
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "lemma": "el gato",
  "cefr_level": "A1",
  "theme": "family",
  "ease_factor": 2.5,          // FSRS/SM-2 style
  "interval_days": 3,
  "due_at": "ISODate",
  "reps": 4,
  "last_outcome": "correct | incorrect | hesitated",
  "last_reviewed_at": "ISODate"
}
```

### `mistake_tags`
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "vocab_item_id": "ObjectId | null",   // null if it's a general grammar pattern, not a single lexical item
  "error_type": "gender_agreement | conjugation | word_order | false_friend | other",
  "severity": "low | medium | high",
  "example_turn": "text of the learner's turn where this occurred",
  "created_at": "ISODate",
  "retriggered_count": 0                // incremented each time Curriculum Agent re-surfaces it
}
```

### `conversations`
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "session_id": "ObjectId",
  "turns": [
    {"role": "agent", "text": "...", "ts": "ISODate"},
    {"role": "learner", "text": "...", "ts": "ISODate"}
  ],
  "started_at": "ISODate",
  "ended_at": "ISODate"
}
```

### `sessions` (summary record, one per daily loop run)
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "mode": "placement | daily_loop | review_only",
  "mastery_delta": 0.04,
  "items_touched": ["ObjectId", "..."],
  "mistakes_tagged": ["ObjectId", "..."],
  "mistakes_retriggered": ["ObjectId", "..."],
  "next_review_eta": "ISODate",
  "created_at": "ISODate"
}
```

## 2. Pydantic Models (FastAPI request/response layer)

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Optional

class VocabItem(BaseModel):
    id: str
    lemma: str
    cefr_level: Literal["A1", "A2", "B1", "B2"]
    theme: str
    ease_factor: float
    interval_days: int
    due_at: datetime

class MistakeTag(BaseModel):
    id: str
    vocab_item_id: Optional[str]
    error_type: Literal["gender_agreement", "conjugation", "word_order", "false_friend", "other"]
    severity: Literal["low", "medium", "high"]
    example_turn: str
    retriggered_count: int = 0

class SessionSummary(BaseModel):
    session_id: str
    mastery_delta: float
    next_review_eta: datetime
    mistakes_this_session: list[MistakeTag]
    words_closer_to_fluent: int

class ConversationTurn(BaseModel):
    role: Literal["agent", "learner"]
    text: str
    ts: datetime
```

## 3. Vector Store Schema (ChromaDB / FAISS)

**Collection:** `vocab_bank` (shared across all learners — this is the static leveled reference bank, not per-learner state)

```python
# Each document = one example sentence
document = "Voy a comprar pan en la panadería."
metadata = {
    "lemma": "la panadería",
    "cefr_level": "A1",
    "pos": "noun",
    "theme": "travel"
}
```

Seed size for demo: 50–100 lemmas × 1–2 example sentences each = 50–200 documents. Source from an open CEFR wordlist (e.g., a public A1/A2 Spanish frequency list) — don't hand-write these, script the seed.

## 4. Seed Script Shape

```python
# scripts/seed_vocab_bank.py
# 1. Load a CSV of {lemma, cefr_level, theme, example_sentence}
# 2. Embed example_sentence with HF sentence-transformers
# 3. Upsert into ChromaDB collection "vocab_bank" with metadata above
# Run once before first demo; re-run if the CSV changes.
```

## 5. Indexing Notes

- `vocab_items`: index on `(user_id, due_at)` — this is the query the Curriculum Agent runs every session.
- `mistake_tags`: index on `(user_id, created_at)` — used to pull "recent mistakes eligible for re-trigger."
- `sessions`: index on `user_id` — used for the weekly digest and progress view.

At demo scale (one user, a few hundred items) these indexes aren't strictly required to perform well, but add them anyway — it's a five-minute change and it's the kind of detail a judge glancing at your repo will notice.
