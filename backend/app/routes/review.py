from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from app.models.schemas import ReviewDueResponse, VocabItem, OutcomeType
from app.models.db import db
from app.tools.mcp_tools import get_due_items, schedule_next_review
from app.agents.review_recall import generate_recall_prompt, evaluate_recall_response

router = APIRouter(prefix="/review", tags=["review"])

class ReviewRecordRequest(BaseModel):
    user_id: str
    vocab_item_id: str
    outcome: OutcomeType

class RecallPromptRequest(BaseModel):
    lemma: str
    cefr_level: Optional[str] = "A1"
    translation: Optional[str] = ""
    level: Optional[str] = "A1"

class RecallEvaluateRequest(BaseModel):
    user_id: str
    vocab_item_id: str
    target_lemma: str
    learner_text: str

@router.get("/due", response_model=ReviewDueResponse)
def get_review_due(user_id: str = Query(..., description="User ID")):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}})

    due = get_due_items(user_id=user_id, limit=20)
    return ReviewDueResponse(
        due_items=due,
        count=len(due)
    )

@router.post("/prompt")
def create_recall_prompt(req: RecallPromptRequest):
    """Generate an active-recall micro-scenario prompt for a target due item."""
    prompt_text = generate_recall_prompt(
        lemma=req.lemma,
        cefr_level=req.cefr_level or "A1",
        translation=req.translation or "",
        level=req.level or "A1"
    )
    return {"lemma": req.lemma, "prompt": prompt_text}

@router.post("/evaluate")
def evaluate_recall_submission(req: RecallEvaluateRequest):
    """Evaluates learner's recall submission, updates FSRS state, and returns feedback."""
    eval_res = evaluate_recall_response(target_lemma=req.target_lemma, learner_text=req.learner_text)
    outcome: OutcomeType = eval_res["outcome"]

    updated_item = schedule_next_review(user_id=req.user_id, vocab_item_id=req.vocab_item_id, outcome=outcome)

    return {
        "outcome": outcome,
        "is_correct": eval_res["is_correct"],
        "feedback": eval_res["feedback"],
        "updated_item": updated_item
    }

@router.post("/schedule", response_model=VocabItem)
def record_review_outcome(req: ReviewRecordRequest):
    """Direct endpoint to update spaced repetition FSRS state for a reviewed item."""
    user = db.get_user(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}})

    updated = schedule_next_review(user_id=req.user_id, vocab_item_id=req.vocab_item_id, outcome=req.outcome)
    if not updated:
        raise HTTPException(status_code=404, detail={"error": {"code": "ITEM_NOT_FOUND", "message": "Vocab item not found"}})
    return updated


