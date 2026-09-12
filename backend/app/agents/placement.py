import json
import re
from typing import Dict, Any, List
from app.config import settings
from app.llm import call_llm
from app.agents.error_analysis import is_unintelligible_or_gibberish, COMMON_SPANISH_WORDS

def assess_placement_turn(
    target_language: str,
    conversation_history: List[Dict[str, str]],
    learner_text: str
) -> Dict[str, Any]:
    """
    Evaluates one placement turn. After 3-4 turns, returns final CEFR level.
    """
    turn_num = len(conversation_history) // 2 + 1

    # Check if this is the final assessment turn (e.g. 3 turns)
    is_final = turn_num >= 3

    system_prompt = f"""You are a language placement assessor for {target_language}. Hold a brief,
friendly 3-4 exchange conversation with the learner in {target_language},
mixed with English if they seem to struggle. After each learner reply,
silently estimate their CEFR level (A1/A2/B1) based on: vocabulary range,
grammatical accuracy, and sentence complexity. Do not tell the learner
their level mid-conversation.

CRITICAL ACCURACY RULES:
- If the learner writes gibberish, random keystrokes (e.g. asdf), unrelated English, or shows no functional Spanish ability, their level is STRICTLY 'A1' (Beginner). State in notes that the learner is at the absolute beginner level.
- Only assign 'A2' if they produce coherent multi-word Spanish sentences with basic verbs (e.g., quiero, tengo, me gusta, vivo).
- Only assign 'B1' if they show complex subordinate clauses, past/subjunctive tenses, or rich vocabulary.

{"After 3-4 exchanges, output ONLY JSON: {{\"level\": \"A1|A2|B1\", \"notes\": \"one sentence justification\", \"agent_text\": \"Encouraging placement message in Spanish and English\"}}" if is_final else "Keep your turn brief (1-2 sentences), friendly, and ask a simple conversational question to test their level."}
"""

    history_str = "\n".join([f"{t.get('role')}: {t.get('text')}" for t in conversation_history])
    user_prompt = f"Conversation so far:\n{history_str}\nlearner: {learner_text}\n\nAssess this turn and reply."

    llm_output = call_llm(user_prompt, system_prompt)

    # Check if learner input is gibberish
    is_gibberish = is_unintelligible_or_gibberish(learner_text)

    if is_final:
        # Try to parse JSON from output
        if not is_gibberish:
            try:
                match = re.search(r"\{.*\}", llm_output, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    assigned_lvl = parsed.get("level", "A1").upper()
                    if assigned_lvl not in ["A1", "A2", "B1"]:
                        assigned_lvl = "A1"
                    return {
                        "agent_text": parsed.get("agent_text", f"¡Bienvenido a Loop! Tu nivel inicial ha sido establecido en {assigned_lvl}."),
                        "placement_complete": True,
                        "level": assigned_lvl,
                        "notes": parsed.get("notes", "Evaluated based on communicative clarity and vocabulary expression.")
                    }
            except Exception:
                pass

        # Heuristic level estimation fallback
        txt_lower = learner_text.lower()
        words = re.findall(r"[a-záéíóúüñ]+", txt_lower)
        spanish_word_count = sum(1 for w in words if w in COMMON_SPANISH_WORDS)

        if is_gibberish or spanish_word_count == 0:
            level = "A1"
            return {
                "agent_text": "¡Bienvenido a Loop! Hemos determinado que tu nivel inicial es A1 (Principiante) para construir tus bases desde cero.",
                "placement_complete": True,
                "level": level,
                "notes": "Nivel inicial A1 asignado — respuestas iniciales o texto no comprensible."
            }

        level = "A1"
        if len(words) > 6 and spanish_word_count >= 3 and any(w in txt_lower for w in ["porque", "cuando", "estoy", "quiero", "gustaría", "trabajo", "viajar"]):
            level = "A2"
        if spanish_word_count >= 5 and any(w in txt_lower for w in ["quisiera", "aunque", "había", "he estado", "desarrollo", "además"]):
            level = "B1"

        return {
            "agent_text": f"¡Fantástico! Hemos determinado que tu nivel inicial es {level}. ¡Empecemos a practicar!",
            "placement_complete": True,
            "level": level,
            "notes": f"Estimated {level} based on communicative clarity and vocabulary expression."
        }
    else:
        # Intermediate turn
        if is_gibberish:
            agent_text = "No te preocupes si estás empezando. ¿De dónde eres o cómo te llamas? (You can answer with simple words in Spanish!)"
        elif llm_output and "{" not in llm_output:
            agent_text = llm_output.strip()
        else:
            if turn_num == 1:
                agent_text = "¡Mucho gusto! ¿De dónde eres y qué te gusta hacer en tu tiempo libre?"
            elif turn_num == 2:
                agent_text = "¡Qué interesante! ¿Por qué te gustaría aprender español?"
            else:
                agent_text = "¡Genial! ¿Has viajado alguna vez a un país hispanohablante?"

        return {
            "agent_text": agent_text,
            "placement_complete": False,
            "level": None,
            "notes": None
        }
