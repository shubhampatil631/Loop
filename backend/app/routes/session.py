from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import (
    SessionStartRequest, SessionStartResponse,
    SessionTurnRequest, SessionTurnResponse,
    SessionSummary, MistakeTag
)
from app.models.db import db
from app.agents.graph import orchestrate_session_start, orchestrate_session_turn
from app.agents.curriculum import curriculum_agent

router = APIRouter(prefix="/session", tags=["session"])

MAX_SESSION_TURNS = 4

@router.post("/start", response_model=SessionStartResponse)
def session_start(req: SessionStartRequest):
    user = db.get_user(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}})

    result = orchestrate_session_start(user_id=req.user_id, mode=req.mode)
    return SessionStartResponse(
        session_id=result["session_id"],
        agent_text=result["agent_text"],
        scenario=result.get("scenario")
    )

@router.post("/turn", response_model=SessionTurnResponse)
def session_turn(req: SessionTurnRequest):
    sess = db.get_session(req.session_id)
    if not sess:
        raise HTTPException(status_code=404, detail={"error": {"code": "SESSION_NOT_FOUND", "message": "Session not found"}})

    result = orchestrate_session_turn(session_id=req.session_id, learner_text=req.learner_text)
    return SessionTurnResponse(
        agent_text=result["agent_text"],
        turn_count=result["turn_count"],
        session_complete=result["session_complete"]
    )


@router.post("/end", response_model=SessionSummary)
def session_end(req: dict):
    session_id = req.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail={"error": {"code": "BAD_REQUEST", "message": "session_id required"}})

    sess = db.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail={"error": {"code": "SESSION_NOT_FOUND", "message": "Session not found"}})

    user_id = sess["user_id"]
    tagged_ids = sess.get("mistakes_tagged", [])
    if tagged_ids:
        recent_mistakes_docs = db.get_mistakes_by_ids(tagged_ids)
    else:
        recent_mistakes_docs = db.get_user_mistakes(user_id=user_id, limit=5)

    summary_data = curriculum_agent.update_session_learning_state(
        user_id=user_id,
        items_touched_ids=sess.get("items_touched", []),
        tagged_mistakes=recent_mistakes_docs,
        turn_count=len(sess.get("turns", [])) // 2
    )

    db.update_session(session_id, {
        "is_ended": True,
        "mastery_delta": summary_data["mastery_delta"],
        "next_review_eta": summary_data["next_review_eta"]
    })

    # Update user streak and last session timestamp
    user = db.get_user(user_id)
    if user:
        now = datetime.utcnow()
        last_sess = user.get("last_session_at")
        streak = user.get("streak_days", 1)
        if last_sess:
            if isinstance(last_sess, str):
                try:
                    last_sess = datetime.fromisoformat(last_sess)
                except Exception:
                    last_sess = None
            if last_sess:
                delta_days = (now.date() - last_sess.date()).days
                if delta_days == 1:
                    streak += 1
                elif delta_days > 1:
                    streak = 1
        db.update_user(user_id, {
            "last_session_at": now,
            "streak_days": streak
        })

    mistakes_models = [MistakeTag(**m) for m in recent_mistakes_docs[:5]]


    return SessionSummary(
        session_id=session_id,
        mastery_delta=summary_data["mastery_delta"],
        next_review_eta=summary_data["next_review_eta"],
        mistakes_this_session=mistakes_models,
        words_closer_to_fluent=summary_data["words_closer_to_fluent"],
        accuracy_percentage=summary_data.get("accuracy_percentage", 100),
        stability_factor_delta=summary_data.get("stability_factor_delta", "+0.10x"),
        recall_probability=summary_data.get("recall_probability", 92),
        next_recommended_scenario=summary_data.get("next_recommended_scenario")
    )

@router.get("/rag/vocab")
def inspect_rag_vocab(
    level: str = "A1",
    theme: str = "travel",
    k: int = 5,
    query: str = None
):
    """Inspect RAG leveled vocabulary bank retrieval directly."""
    from app.tools.mcp_tools import fetch_level_vocab
    results = fetch_level_vocab(level=level, theme=theme, k=k, query_text=query)
    return {
        "level": level,
        "theme": theme,
        "query": query,
        "count": len(results),
        "results": results
    }

