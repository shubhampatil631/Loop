from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    OnboardingStartRequest, OnboardingStartResponse,
    PlacementTurnRequest, PlacementTurnResponse
)
from app.models.db import db
from app.agents.placement import assess_placement_turn

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

@router.post("/start", response_model=OnboardingStartResponse)
def onboarding_start(req: OnboardingStartRequest):
    try:
        user = db.create_user(
            name=req.name,
            target_language=req.target_language,
            goal=req.goal,
            level="A1"
        )
        user_id = user["id"]

        placement_session = db.create_session(user_id=user_id, mode="placement")
        sess_id = placement_session["id"]


        greeting = f"¡Hola {req.name}! Bienvenido a Loop. Dime, ¿cómo te llamas y por qué te gustaría aprender español?"
        db.update_session(sess_id, {
            "turns": [{"role": "agent", "text": greeting}]
        })

        return OnboardingStartResponse(
            user_id=user_id,
            placement_session_id=sess_id,
            greeting=greeting
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": {"code": "ONBOARDING_ERROR", "message": str(e)}})

@router.post("/placement/turn", response_model=PlacementTurnResponse)
def onboarding_placement_turn(req: PlacementTurnRequest):
    sess = db.get_session(req.placement_session_id)
    if not sess:
        raise HTTPException(status_code=404, detail={"error": {"code": "SESSION_NOT_FOUND", "message": "Placement session not found"}})

    user_id = sess["user_id"]
    user = db.get_user(user_id) or {"target_language": "es"}
    target_lang = user.get("target_language", "es")

    history = sess.get("turns", [])
    result = assess_placement_turn(
        target_language=target_lang,
        conversation_history=history,
        learner_text=req.learner_text
    )

    history.append({"role": "learner", "text": req.learner_text})
    history.append({"role": "agent", "text": result["agent_text"]})

    updates = {"turns": history}
    if result["placement_complete"]:
        updates["is_ended"] = True
        level = result.get("level", "A1")
        db.update_user(user_id, {"level": level})

    db.update_session(req.placement_session_id, updates)

    return PlacementTurnResponse(
        agent_text=result["agent_text"],
        placement_complete=result["placement_complete"],
        level=result.get("level"),
        notes=result.get("notes")
    )
