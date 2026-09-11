from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.config import settings
from app.models.db import db

def generate_weekly_digest(user_id: str) -> Dict[str, Any]:
    """
    Generates a 2-sentence LLM-assisted weekly digest summarizing
    one strength and one focus area based on the past week's sessions and mistake tags.
    """
    user = db.get_user(user_id)
    if not user:
        return {"summary": "User not found.", "strength": "", "focus_area": ""}

    mistakes = db.get_user_mistakes(user_id, limit=10)
    all_vocab = db.get_all_user_vocab(user_id)
    recent_sessions = db.get_user_sessions(user_id, limit=3)

    # Collect actual learner conversation turns from recent sessions
    recent_dialogue = []
    for s in recent_sessions:
        s_id = s.get("id") or s.get("_id")
        conv = db.get_conversation_by_session(s_id)
        turns = conv.get("turns", []) if conv else s.get("turns", [])
        for t in turns:
            if t.get("role") == "learner" and t.get("text"):
                recent_dialogue.append(t["text"])

    dialogue_sample = "; ".join([f'"{d}"' for d in recent_dialogue[-6:]]) if recent_dialogue else "none"

    mistake_items = []
    mistake_counts = {}
    for m in mistakes:
        etype = m.get("error_type", "other")
        mistake_counts[etype] = mistake_counts.get(etype, 0) + 1
        ex = m.get("example_turn", "")
        corr = m.get("correction", "")
        if ex and corr:
            mistake_items.append(f"[{etype}] '{ex}' -> target: '{corr}'")

    most_common_error = max(mistake_counts, key=mistake_counts.get) if mistake_counts else "none"
    graduated_count = len([v for v in all_vocab if v.get("reps", 0) >= 3])
    mistakes_str = " | ".join(mistake_items[:3]) if mistake_items else "no major errors"

    from app.llm import call_llm
    system_prompt = f"""You are an insightful English-speaking language learning coach. Based on this learner's actual Spanish session data:
- CEFR Level: {user.get('level', 'A1')} (Goal: {user.get('goal', 'travel')})
- Words mastered in FSRS: {graduated_count}
- Recent spoken Spanish phrases: {dialogue_sample}
- Specific mistakes & target corrections: {mistakes_str}

CRITICAL REQUIREMENT: You MUST write the entire report in clear, encouraging ENGLISH. Do not write the explanation in Spanish.

Write a tailored 2-sentence feedback report in English:
Sentence 1: Praise a specific positive communicative accomplishment from their spoken phrases in English.
Sentence 2: Offer constructive guidance in English on their specific error pattern (e.g. {most_common_error.replace('_', ' ')}) with a clear explanation and helpful tip (quoting Spanish examples in quotes if needed)."""

    llm_res = call_llm(prompt="Generate personalized weekly feedback report in English", system_instruction=system_prompt, temperature=0.3)
    if llm_res:
        return {
            "summary": llm_res.strip(),
            "strength": f"Demonstrated active communication in '{user.get('goal', 'travel')}' scenarios with {graduated_count} mastered lexemes",
            "focus_area": most_common_error.replace('_', ' ') if most_common_error != "none" else "Vocabulary breadth and complex tenses"
        }

    # Fallback heuristic summary
    if most_common_error != "none":
        summary = f"You demonstrated great conversational initiative and solidified {graduated_count} core vocabulary items. For your next sessions, pay special attention to {most_common_error.replace('_', ' ')} when forming spontaneous sentences."
    else:
        summary = f"You maintained excellent grammatical consistency throughout your recent roleplays with {graduated_count} vocabulary items mastered. Keep up the consistent daily conversational practice!"

    return {
        "summary": summary,
        "strength": f"Solidified {graduated_count} core vocabulary items with active recall",
        "focus_area": most_common_error.replace('_', ' ') if most_common_error != "none" else "Expanding vocabulary breadth"
    }
