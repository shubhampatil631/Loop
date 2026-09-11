from typing import List, Dict, Any, Optional, Literal
from datetime import datetime, timedelta
from app.models.schemas import VocabItem, MistakeTag, OutcomeType
from app.models.db import db
from app.rag.vocab_store import vocab_store

def get_due_items(user_id: str, limit: int = 10) -> List[VocabItem]:
    """Return vocab_items due for review, ordered by due_at ascending."""
    raw_items = db.get_due_vocab_items(user_id=user_id, limit=limit)
    return [VocabItem(**item) for item in raw_items]

def fetch_level_vocab(level: str, theme: str, k: int = 5, query_text: Optional[str] = None) -> List[Dict[str, Any]]:
    """RAG query against ChromaDB vocab_bank, filtered to cefr_level <= level."""
    return vocab_store.query_vocab(level=level, theme=theme, k=k, query_text=query_text)

def log_error_tag(
    user_id: str,
    vocab_item_id: Optional[str],
    error_type: str,
    severity: str,
    example_turn: str,
    correction: Optional[str] = None,
    explanation: Optional[str] = None
) -> str:
    """Insert a mistake_tags document, return its id."""
    tag = db.log_mistake_tag(
        user_id=user_id,
        vocab_item_id=vocab_item_id,
        error_type=error_type,
        severity=severity,
        example_turn=example_turn,
        correction=correction,
        explanation=explanation
    )
    return tag["id"]

def schedule_next_review(
    user_id: str,
    vocab_item_id: str,
    outcome: OutcomeType
) -> Optional[VocabItem]:
    """Update ease_factor/interval_days/due_at for one item per the FSRS rule."""
    all_vocab = db.get_all_user_vocab(user_id)
    target = next((v for v in all_vocab if v.get("id") == vocab_item_id or v.get("_id") == vocab_item_id), None)
    if not target:
        return None

    ease_factor = float(target.get("ease_factor", 2.5))
    interval_days = int(target.get("interval_days", 1))
    reps = int(target.get("reps", 0))

    if outcome == "correct":
        ease_factor = round(min(ease_factor + 0.1, 3.0), 2)
        interval_days = max(1, round(interval_days * ease_factor))
    elif outcome == "hesitated":
        interval_days = max(1, round(interval_days * 0.7))
    else:  # incorrect
        ease_factor = round(max(ease_factor - 0.3, 1.3), 2)
        interval_days = 1

    due_at = datetime.utcnow() + timedelta(days=interval_days)
    reps += 1

    updates = {
        "ease_factor": ease_factor,
        "interval_days": interval_days,
        "due_at": due_at,
        "reps": reps,
        "last_outcome": outcome,
        "last_reviewed_at": datetime.utcnow()
    }
    updated = db.update_vocab_item(vocab_item_id, updates)
    return VocabItem(**updated) if updated else None

def get_learner_profile(user_id: str) -> Dict[str, Any]:
    """Return {level, goal, target_language, streak_days}."""
    user = db.get_user(user_id)
    if not user:
        return {
            "level": "A1",
            "goal": "travel",
            "target_language": "es",
            "streak_days": 1
        }
    return {
        "user_id": user.get("id"),
        "name": user.get("name"),
        "level": user.get("level", "A1"),
        "goal": user.get("goal", "travel"),
        "target_language": user.get("target_language", "es"),
        "streak_days": user.get("streak_days", 1)
    }

# MCP Tool registry dictionary for server exposure
MCP_TOOL_DEFINITIONS = [
    {
        "name": "get_due_items",
        "description": "Fetch vocab items due for review for a learner",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "limit": {"type": "integer", "default": 10}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "fetch_level_vocab",
        "description": "Retrieve level-appropriate example sentences from the vocab bank grounded in CEFR constraints",
        "parameters": {
            "type": "object",
            "properties": {
                "level": {"type": "string", "enum": ["A1", "A2", "B1", "B2"]},
                "theme": {"type": "string"},
                "k": {"type": "integer", "default": 5},
                "query_text": {"type": "string", "description": "Optional semantic search query text"}
            },
            "required": ["level", "theme"]
        }
    },
    {
        "name": "log_error_tag",
        "description": "Record a tagged mistake for a learner",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "vocab_item_id": {"type": "string"},
                "error_type": {"type": "string"},
                "severity": {"type": "string"},
                "example_turn": {"type": "string"},
                "correction": {"type": "string"},
                "explanation": {"type": "string"}
            },
            "required": ["user_id", "error_type", "severity", "example_turn"]
        }
    },
    {
        "name": "schedule_next_review",
        "description": "Update spaced-repetition state for one vocab item",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "vocab_item_id": {"type": "string"},
                "outcome": {"type": "string", "enum": ["correct", "incorrect", "hesitated"]}
            },
            "required": ["user_id", "vocab_item_id", "outcome"]
        }
    },
    {
        "name": "get_learner_profile",
        "description": "Fetch a learner's level, goal, and streak",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"}
            },
            "required": ["user_id"]
        }
    }
]
