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

    # Check if learner has real multi-word conversational substance
    meaningful_turns = [
        d for d in recent_dialogue
        if len(d.strip().split()) >= 2 and d.strip().lower() not in {"no no", "si si", "ok ok"}
    ]

    graduated_count = len([v for v in all_vocab if v.get("reps", 0) >= 3])

    if not meaningful_turns and graduated_count == 0:
        return {
            "summary": "You have completed initial onboarding sessions. To accelerate your Spanish progress, practice using full conversational phrases (such as 'Me llamo...', 'Quiero un café', or 'Muchas gracias') in your daily roleplays.",
            "strength": f"Initiated foundational Spanish onboarding in '{user.get('goal', 'travel')}' topics",
            "focus_area": "Forming complete beginner sentences and greetings"
        }

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
    mistakes_str = " | ".join(mistake_items[:3]) if mistake_items else "no major errors"

    from app.llm import call_llm
    system_prompt = f"""You are an insightful English-speaking language learning coach. Based on this learner's actual Spanish session data:
- CEFR Level: {user.get('level', 'A1')} (Goal: {user.get('goal', 'travel')})
- Words mastered in FSRS: {graduated_count}
- Recent spoken Spanish phrases: {dialogue_sample}
- Specific mistakes & target corrections: {mistakes_str}

CRITICAL ACCURACY RULES:
1. Write the entire report in clear, encouraging ENGLISH.
2. HONEST EVALUATION: NEVER praise single-word non-answers (e.g. 'no', 'si', 'ok') as accomplishments. If the learner has only spoken minimal words, honestly advise them to practice full phrases.
3. If they have practiced real phrases, acknowledge their actual communicative effort and provide constructive guidance on their specific error pattern ({most_common_error.replace('_', ' ')}).

Write a tailored 2-sentence feedback report in English."""

    llm_res = call_llm(prompt="Generate personalized weekly feedback report in English", system_instruction=system_prompt, temperature=0.3)
    if llm_res:
        return {
            "summary": llm_res.strip(),
            "strength": f"Practiced conversational communication in '{user.get('goal', 'travel')}' scenarios ({graduated_count} mastered lexemes)" if graduated_count > 0 else f"Initiated conversational practice in '{user.get('goal', 'travel')}' scenarios",
            "focus_area": most_common_error.replace('_', ' ') if most_common_error != "none" else "Vocabulary breadth and sentence structures"
        }

    # Fallback heuristic summary
    if most_common_error != "none":
        summary = f"You practiced conversational roleplays and worked on your core vocabulary. For your next sessions, pay special attention to {most_common_error.replace('_', ' ')} when forming spontaneous sentences."
    else:
        summary = f"You completed your conversational practice sessions with {graduated_count} vocabulary items mastered. Keep practicing regularly to build sentence fluency!"

    return {
        "summary": summary,
        "strength": f"Solidified {graduated_count} core vocabulary items with active recall" if graduated_count > 0 else "Engaged with daily interactive conversational practice",
        "focus_area": most_common_error.replace('_', ' ') if most_common_error != "none" else "Expanding vocabulary breadth"
    }
