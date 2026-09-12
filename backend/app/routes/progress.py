from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import ProgressResponse
from app.models.db import db

router = APIRouter(prefix="/progress", tags=["progress"])

@router.get("", response_model=ProgressResponse)
def get_progress(user_id: str = Query(..., description="User ID")):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}})

    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=3) as executor:
        fut_vocab = executor.submit(db.get_all_user_vocab, user_id)
        fut_mistakes = executor.submit(db.get_user_mistakes, user_id, 100)
        fut_sessions = executor.submit(db.get_user_sessions, user_id, 50)
        all_vocab = fut_vocab.result()
        all_mistakes = fut_mistakes.result()
        sessions = fut_sessions.result()

    graduated = len([v for v in all_vocab if v.get("reps", 0) >= 3 and v.get("ease_factor", 2.5) >= 2.4])
    in_progress = len([v for v in all_vocab if (v.get("reps", 0) > 0 and (v.get("reps", 0) < 3 or v.get("ease_factor", 2.5) < 2.4)) or v.get("last_reviewed_at") is not None])
    
    # If starting fresh, untouched starter words count as in-progress foundation
    if in_progress == 0 and graduated == 0 and all_vocab:
        in_progress = len(all_vocab)

    total_words = max(1, len(all_vocab))
    total_sessions_count = len(sessions)
    total_mistakes_count = len(all_mistakes)

    # Base level baseline calibration
    lvl = (user.get("level") or "A1").upper()
    baseline = 0.25 if lvl == "A1" else 0.45 if lvl == "A2" else 0.70 if lvl == "B1" else 0.85

    # Progression contribution
    vocab_ratio = (graduated * 1.0 + in_progress * 0.4) / total_words
    session_boost = min(0.35, total_sessions_count * 0.04)
    mastery_score = round(min(1.0, max(0.15, (baseline * 0.35) + (vocab_ratio * 0.35) + session_boost)), 2)

    # Average FSRS retention rate across vocab
    if all_vocab:
        avg_ease = sum(float(v.get("ease_factor", 2.5)) for v in all_vocab) / len(all_vocab)
        retention_rate = min(99, max(75, round((avg_ease / 2.7) * 92)))
    else:
        retention_rate = 92

    # Accuracy rate from total dialogue turns vs mistakes
    total_learner_turns = sum(len([t for t in s.get("turns", []) if t.get("role") == "learner"]) for s in sessions)
    if total_learner_turns > 0:
        accuracy_rate = max(0, min(100, round(((total_learner_turns - total_mistakes_count) / total_learner_turns) * 100)))
    elif total_mistakes_count == 0:
        accuracy_rate = 100
    else:
        accuracy_rate = max(0, 100 - total_mistakes_count * 10)

    return ProgressResponse(
        mastery_score=mastery_score,
        words_graduated=graduated,
        words_in_progress=in_progress,
        recent_mistakes=all_mistakes[:10],
        streak_days=user.get("streak_days", 1),
        total_sessions=total_sessions_count,
        total_mistakes=total_mistakes_count,
        accuracy_rate=accuracy_rate,
        retention_rate=retention_rate
    )

@router.get("/digest")
def get_weekly_digest(user_id: str = Query(..., description="User ID")):
    from app.agents.weekly_digest import generate_weekly_digest
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}})
    return generate_weekly_digest(user_id)

