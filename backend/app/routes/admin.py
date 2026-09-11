from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor
from app.models.db import db
from app.config import settings

router = APIRouter(prefix="/users", tags=["learners-and-audit"])

# Short-lived in-memory cache for overview metrics
_overview_cache: Dict[str, Any] = {"data": None, "expires_at": 0.0}

@router.get("")
def list_learners(limit: int = Query(50, ge=1, le=200)):
    """
    List all learners who tried the platform, with registration dates,
    CEFR level, goal, session counts, and mistake statistics.
    """
    users = db.get_all_users(limit=limit)
    formatted = []
    for u in users:
        formatted.append({
            "id": u.get("id"),
            "user_id": u.get("id"),
            "name": u.get("name"),
            "level": u.get("level"),
            "goal": u.get("goal"),
            "streak_days": u.get("streak_days", 1),
            "created_at": u.get("created_at"),
            "last_session_at": u.get("last_session_at"),
            "total_sessions": u.get("total_sessions", 0),
            "total_mistakes": u.get("total_mistakes", 0),
        })
    return {
        "count": len(formatted),
        "learners": formatted
    }

@router.get("/{user_id}/history")
def get_learner_full_history(user_id: str):
    """
    Retrieve complete record for a learner:
    - Profile information
    - All completed sessions & scenarios
    - All dialogue turns & conversational transcripts
    - All classified mistakes with target native forms
    - Spaced repetition vocabulary items
    """
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Learner not found")

    # Fetch sessions, mistakes, vocab, and conversations in parallel across threads
    with ThreadPoolExecutor(max_workers=4) as executor:
        fut_sessions = executor.submit(db.get_user_sessions, user_id)
        fut_mistakes = executor.submit(db.get_user_mistakes, user_id, 100)
        fut_vocab = executor.submit(db.get_all_user_vocab, user_id)
        fut_convs = executor.submit(db.get_user_conversations, user_id)

        sessions = fut_sessions.result()
        mistakes = fut_mistakes.result()
        vocab = fut_vocab.result()
        convs = fut_convs.result()

    conv_map = {c.get("session_id"): c.get("turns", []) for c in convs}

    detailed_sessions = []
    for s in sessions:
        sess_id = s.get("id") or s.get("_id")
        s_copy = dict(s)
        s_copy["conversation_turns"] = conv_map.get(sess_id, s.get("turns", []))
        detailed_sessions.append(s_copy)

    return {
        "user": {
            "user_id": user.get("id"),
            "name": user.get("name"),
            "level": user.get("level"),
            "goal": user.get("goal"),
            "streak_days": user.get("streak_days", 1),
            "created_at": user.get("created_at"),
            "last_session_at": user.get("last_session_at"),
        },
        "statistics": {
            "total_sessions": len(sessions),
            "total_mistakes_tagged": len(mistakes),
            "vocab_items_tracked": len(vocab),
            "vocab_graduated": len([v for v in vocab if v.get("reps", 0) >= 3]),
        },
        "sessions": detailed_sessions,
        "mistake_tags": mistakes,
        "vocab_sample": vocab[:15]
    }

@router.get("/admin/overview")
def get_platform_overview(force_refresh: bool = Query(False)):
    """Returns platform-wide metrics across all learners and AI models."""
    now = time.time()
    if not force_refresh and _overview_cache["data"] and now < _overview_cache["expires_at"]:
        return _overview_cache["data"]

    if db.is_connected and db.db is not None:
        try:
            with ThreadPoolExecutor(max_workers=3) as executor:
                fut_u = executor.submit(db.db.users.count_documents, {})
                fut_s = executor.submit(db.db.sessions.count_documents, {})
                fut_m = executor.submit(db.db.mistake_tags.count_documents, {})
                total_users = fut_u.result()
                total_sessions = fut_s.result()
                total_mistakes = fut_m.result()
        except Exception:
            total_users = 0
            total_sessions = 0
            total_mistakes = 0
    else:
        total_users = len(db.fallback.users)
        total_sessions = len(db.fallback.sessions)
        total_mistakes = len(db.fallback.mistake_tags)

    data = {
        "database_connected": db.is_connected,
        "active_database": db.db.name if db.db is not None else "In-Memory Fallback",
        "total_learners_registered": total_users,
        "total_sessions_conducted": total_sessions,
        "total_mistakes_classified": total_mistakes,
        "configured_llm_hierarchy": {
            "tier_1_ollama_host": settings.OLLAMA_HOST,
            "tier_1_ollama_models": settings.OLLAMA_MODELS,
            "tier_2_groq_configured": bool(settings.GROQ_API_KEY),
            "tier_3_gemini_configured": bool(settings.GEMINI_API_KEY)
        }
    }
    _overview_cache["data"] = data
    _overview_cache["expires_at"] = now + 4.0  # short 4s TTL for responsive live updates
    return data

