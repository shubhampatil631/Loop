from typing import TypedDict, List, Dict, Any, Optional, Literal
from app.agents.placement import assess_placement_turn
from app.agents.conversation import generate_conversation_turn
from app.agents.error_analysis import analyze_learner_errors
from app.agents.curriculum import curriculum_agent
from app.agents.review_recall import generate_recall_prompt
from app.models.db import db
from app.tools.mcp_tools import get_learner_profile

class LoopState(TypedDict):
    user_id: str
    session_id: Optional[str]
    mode: Literal["placement", "daily_loop", "review_only"]
    level: str
    target_language: str
    theme: str
    persona: str
    due_items: List[Dict[str, Any]]
    items_touched: List[str]
    conversation_history: List[Dict[str, str]]
    turn_count: int
    max_turns: int
    tagged_mistakes: List[Dict[str, Any]]
    latest_agent_text: Optional[str]
    latest_learner_text: Optional[str]
    placement_complete: bool
    session_complete: bool
    session_summary: Optional[Dict[str, Any]]

# Node Functions

def placement_node(state: LoopState) -> Dict[str, Any]:
    """Placement assessment node estimating CEFR level."""
    res = assess_placement_turn(
        target_language=state.get("target_language", "es"),
        conversation_history=state.get("conversation_history", []),
        learner_text=state.get("latest_learner_text", "")
    )
    history = list(state.get("conversation_history", []))
    if state.get("latest_learner_text"):
        history.append({"role": "learner", "text": state["latest_learner_text"]})
    history.append({"role": "agent", "text": res["agent_text"]})

    level = res.get("level") or state.get("level", "A1")
    is_complete = res.get("placement_complete", False)

    if is_complete and state.get("user_id"):
        db.update_user(state["user_id"], {"level": level})

    return {
        "conversation_history": history,
        "latest_agent_text": res["agent_text"],
        "placement_complete": is_complete,
        "level": level,
        "session_complete": is_complete
    }

def curriculum_pull_node(state: LoopState) -> Dict[str, Any]:
    """Curriculum pull node fetching due items and candidate retrigger mistakes."""
    user_id = state.get("user_id", "")
    due_items = curriculum_agent.get_session_due_items(user_id=user_id, limit=3)
    retrigger_mistakes = curriculum_agent.get_retrigger_mistakes(user_id=user_id, limit=2)
    
    touched = list(state.get("items_touched", []))
    for d in due_items:
        d_id = d.get("id") or d.get("_id")
        if d_id and d_id not in touched:
            touched.append(d_id)

    return {
        "due_items": due_items,
        "tagged_mistakes": retrigger_mistakes,
        "items_touched": touched
    }

def conversation_node(state: LoopState) -> Dict[str, Any]:
    """Conversation partner node generating grounded in-level dialogue."""
    mode = state.get("mode", "daily_loop")
    target_lang = state.get("target_language", "es")
    
    if mode == "review_only":
        due_items = state.get("due_items", [])
        due_item = due_items[0] if due_items else {}
        lemma = due_item.get("lemma", "el café")
        cefr_level = due_item.get("cefr_level", state.get("level", "A1"))
        agent_reply = generate_recall_prompt(
            lemma=lemma,
            cefr_level=cefr_level,
            level=state.get("level", "A1"),
            target_language=target_lang
        )
    else:
        agent_reply = generate_conversation_turn(
            level=state.get("level", "A1"),
            theme=state.get("theme", "travel"),
            persona=state.get("persona", "barista"),
            target_language=target_lang,
            due_items=state.get("due_items", []),
            tagged_mistakes=state.get("tagged_mistakes", []),
            conversation_history=state.get("conversation_history", []),
            latest_learner_text=state.get("latest_learner_text")
        )

    history = list(state.get("conversation_history", []))
    if state.get("latest_learner_text"):
        history.append({"role": "learner", "text": state["latest_learner_text"]})
    history.append({"role": "agent", "text": agent_reply})

    turn_count = state.get("turn_count", 0) + (1 if state.get("latest_learner_text") else 0)
    max_turns = state.get("max_turns", 4)
    is_complete = turn_count >= max_turns

    return {
        "conversation_history": history,
        "latest_agent_text": agent_reply,
        "turn_count": turn_count,
        "session_complete": is_complete
    }

def error_analysis_node(state: LoopState) -> Dict[str, Any]:
    """Error analysis node running asynchronously on learner utterances."""
    learner_text = state.get("latest_learner_text", "")
    new_mistakes = []
    if learner_text:
        new_mistakes = analyze_learner_errors(
            user_id=state.get("user_id", ""),
            learner_text=learner_text,
            level=state.get("level", "A1"),
            target_language=state.get("target_language", "es")
        )
    existing = list(state.get("tagged_mistakes", []))
    return {
        "tagged_mistakes": existing + new_mistakes
    }

def curriculum_update_node(state: LoopState) -> Dict[str, Any]:
    """Curriculum update node computing FSRS scheduling updates & mastery delta."""
    summary = curriculum_agent.update_session_learning_state(
        user_id=state.get("user_id", ""),
        items_touched_ids=state.get("items_touched", []),
        tagged_mistakes=state.get("tagged_mistakes", []),
        turn_count=state.get("turn_count", 0)
    )
    return {
        "session_summary": summary,
        "session_complete": True
    }

# Build LangGraph StateGraph
def build_loop_graph():
    try:
        from langgraph.graph import StateGraph, END
        workflow = StateGraph(LoopState)

        workflow.add_node("placement_agent", placement_node)
        workflow.add_node("curriculum_pull", curriculum_pull_node)
        workflow.add_node("conversation_partner", conversation_node)
        workflow.add_node("error_analysis", error_analysis_node)
        workflow.add_node("curriculum_update", curriculum_update_node)

        # Route entry point
        def route_start(state: LoopState):
            if state.get("mode") == "placement":
                return "placement_agent"
            # If session is already initialized with due items, go straight to conversation
            if state.get("due_items"):
                return "conversation_partner"
            return "curriculum_pull"

        workflow.set_conditional_entry_point(
            route_start,
            {
                "placement_agent": "placement_agent",
                "curriculum_pull": "curriculum_pull",
                "conversation_partner": "conversation_partner"
            }
        )

        workflow.add_edge("placement_agent", END)
        workflow.add_edge("curriculum_pull", "conversation_partner")
        
        # After conversation turn, run error analysis if there was learner input
        def route_after_conversation(state: LoopState):
            if state.get("latest_learner_text"):
                return "error_analysis"
            return END

        workflow.add_conditional_edges(
            "conversation_partner",
            route_after_conversation,
            {
                "error_analysis": "error_analysis",
                END: END
            }
        )

        # After error analysis, if session complete, transition to curriculum update
        def route_after_error_analysis(state: LoopState):
            if state.get("session_complete"):
                return "curriculum_update"
            return END

        workflow.add_conditional_edges(
            "error_analysis",
            route_after_error_analysis,
            {
                "curriculum_update": "curriculum_update",
                END: END
            }
        )

        workflow.add_edge("curriculum_update", END)

        return workflow.compile()
    except Exception as e:
        print(f"[LangGraph] Graph compile error ({e}). Returning None.")
        return None

graph = build_loop_graph()

# LangGraph High-Level Orchestrator Helpers

def orchestrate_session_start(user_id: str, mode: str = "daily_loop") -> Dict[str, Any]:
    """Orchestrates session startup via LangGraph pipeline."""
    user = db.get_user(user_id) or get_learner_profile(user_id)
    level = user.get("level", "A1")
    theme = user.get("goal", "travel")
    persona = "barista" if theme in ["travel", "cafe"] else "coworker"
    
    sess = db.create_session(user_id=user_id, mode=mode)
    session_id = sess["id"]

    initial_state: LoopState = {
        "user_id": user_id,
        "session_id": session_id,
        "mode": mode,
        "level": level,
        "target_language": user.get("target_language", "es"),
        "theme": theme,
        "persona": persona,
        "due_items": [],
        "items_touched": [],
        "conversation_history": [],
        "turn_count": 0,
        "max_turns": 4,
        "tagged_mistakes": [],
        "latest_agent_text": None,
        "latest_learner_text": None,
        "placement_complete": False,
        "session_complete": False,
        "session_summary": None
    }

    if graph:
        out = graph.invoke(initial_state)
    else:
        # Fallback executor
        pull_res = curriculum_pull_node(initial_state)
        initial_state.update(pull_res)
        out = conversation_node(initial_state)

    agent_text = out.get("latest_agent_text", "¡Hola! ¿En qué puedo ayudarte hoy?")
    
    db.update_session(session_id, {
        "turns": [{"role": "agent", "text": agent_text}],
        "items_touched": out.get("items_touched", []),
        "mistakes_retriggered": [m.get("id") for m in out.get("tagged_mistakes", []) if m.get("id")]
    })

    # Persist in conversations collection
    try:
        db.create_conversation(
            user_id=user_id,
            session_id=session_id,
            initial_turns=[{"role": "agent", "text": agent_text}]
        )
    except Exception as e:
        print(f"[Graph] Error creating conversation record: {e}")

    return {
        "session_id": session_id,
        "agent_text": agent_text,
        "scenario": f"{persona.capitalize()} at {theme.capitalize()}"
    }

def extract_and_track_learner_vocab(user_id: str, text: str, theme: str = "travel", level: str = "A1") -> List[str]:
    """Scans learner text for Spanish vocabulary items and tracks them in MongoDB."""
    if not user_id or not text:
        return []
    
    text_lower = text.lower()
    user_vocab = db.get_all_user_vocab(user_id)
    vocab_by_lemma = { (v.get("lemma") or "").lower().strip(): v for v in user_vocab }
    
    # Common core Spanish lemmas mapped to keyword detections
    candidate_lemmas = [
        ("el café", ["café", "cafe"]),
        ("el agua", ["agua"]),
        ("el té", ["té", "te"]),
        ("el problema", ["problema"]),
        ("el dinero", ["dinero", "euros", "pesos"]),
        ("la cuenta", ["cuenta"]),
        ("el boleto", ["boleto", "billete", "ticket", "pasaje"]),
        ("la estación", ["estación", "estacion", "tren"]),
        ("el hotel", ["hotel", "habitación", "habitacion"]),
        ("la comida", ["comida", "tapas", "plato", "menú"]),
        ("el museo", ["museo", "arte"]),
        ("el viaje", ["viaje", "viajar"]),
        ("el trabajo", ["trabajo", "oficina", "reunión", "reunion"]),
        ("la familia", ["familia", "amigo", "amiga"]),
        ("las gracias", ["gracias"]),
        ("el tiempo", ["tiempo", "hora", "tarde", "mañana", "noche"]),
    ]
    
    touched_ids = []
    for canonical_lemma, triggers in candidate_lemmas:
        if any(tr in text_lower for tr in triggers):
            if canonical_lemma in vocab_by_lemma:
                v_doc = vocab_by_lemma[canonical_lemma]
                v_id = v_doc.get("id") or v_doc.get("_id")
                if v_id and v_id not in touched_ids:
                    touched_ids.append(v_id)
            else:
                new_v = db.create_vocab_item(
                    user_id=user_id,
                    lemma=canonical_lemma,
                    cefr_level=level,
                    theme=theme
                )
                v_id = new_v.get("id") or new_v.get("_id")
                if v_id and v_id not in touched_ids:
                    touched_ids.append(v_id)
                vocab_by_lemma[canonical_lemma] = new_v

    return touched_ids

def orchestrate_session_turn(session_id: str, learner_text: str) -> Dict[str, Any]:
    """Orchestrates a conversation turn via LangGraph pipeline."""
    sess = db.get_session(session_id)
    if not sess:
        raise ValueError(f"Session '{session_id}' not found")

    user_id = sess["user_id"]
    user = db.get_user(user_id) or get_learner_profile(user_id)
    level = user.get("level", "A1")
    theme = user.get("goal", "travel")
    persona = "barista" if theme in ["travel", "cafe"] else "coworker"

    history = sess.get("turns", [])
    prior_turn_count = len([t for t in history if t.get("role") == "learner"])
    
    retriggered_ids = sess.get("mistakes_retriggered", [])
    tagged_mistakes = db.get_mistakes_by_ids(retriggered_ids) if retriggered_ids else []

    due_items = curriculum_agent.get_session_due_items(user_id=user_id, limit=3)

    # Extract words spoken by learner in this turn
    spoken_vocab_ids = extract_and_track_learner_vocab(user_id=user_id, text=learner_text, theme=theme, level=level)
    existing_items_touched = sess.get("items_touched", [])
    all_touched = list(set(existing_items_touched + spoken_vocab_ids))

    state: LoopState = {
        "user_id": user_id,
        "session_id": session_id,
        "mode": sess.get("mode", "daily_loop"),
        "level": level,
        "target_language": user.get("target_language", "es"),
        "theme": theme,
        "persona": persona,
        "due_items": due_items,
        "items_touched": all_touched,
        "conversation_history": history,
        "turn_count": prior_turn_count,
        "max_turns": 4,
        "tagged_mistakes": tagged_mistakes,
        "latest_agent_text": None,
        "latest_learner_text": learner_text,
        "placement_complete": False,
        "session_complete": False,
        "session_summary": None
    }

    if graph:
        out = graph.invoke(state)
    else:
        # Direct execution fallback
        conv_res = conversation_node(state)
        state.update(conv_res)
        err_res = error_analysis_node(state)
        state.update(err_res)
        out = state

    agent_reply = out.get("latest_agent_text", "¡Muy bien!")
    new_turn_count = prior_turn_count + 1
    is_complete = new_turn_count >= 4 or out.get("session_complete", False)

    updated_history = out.get("conversation_history", history)
    
    # Store newly tagged mistake ids in session
    new_tagged = [m.get("id") for m in out.get("tagged_mistakes", []) if m.get("id")]
    existing_mistakes_tagged = sess.get("mistakes_tagged", [])
    combined_mistakes = list(set(existing_mistakes_tagged + new_tagged))

    db.update_session(session_id, {
        "turns": updated_history,
        "items_touched": all_touched,
        "mistakes_tagged": combined_mistakes,
        "is_ended": is_complete
    })

    # Persist dialogue turns into conversations collection
    try:
        db.append_conversation_turn(session_id=session_id, role="learner", text=learner_text)
        db.append_conversation_turn(session_id=session_id, role="agent", text=agent_reply)
        if is_complete:
            db.end_conversation(session_id=session_id)
    except Exception as e:
        print(f"[Graph] Error appending conversation turn: {e}")

    return {
        "agent_text": agent_reply,
        "turn_count": new_turn_count,
        "session_complete": is_complete,
        "summary": out.get("session_summary")
    }


