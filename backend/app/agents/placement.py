import json
import re
from typing import Dict, Any, List
from app.config import settings
from app.llm import call_llm

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
{"After 3-4 exchanges, output ONLY JSON: {{\"level\": \"A1|A2|B1\", \"notes\": \"one sentence justification\", \"agent_text\": \"Final encouraging message in Spanish and English\"}}" if is_final else "Keep your turn brief (1-2 sentences), friendly, and ask a simple conversational question to test their level."}
"""

    history_str = "\n".join([f"{t.get('role')}: {t.get('text')}" for t in conversation_history])
    user_prompt = f"Conversation so far:\n{history_str}\nlearner: {learner_text}\n\nAssess this turn and reply."

    llm_output = call_llm(user_prompt, system_prompt)

    if is_final:
        # Try to parse JSON from output
        try:
            match = re.search(r"\{.*\}", llm_output, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                return {
                    "agent_text": parsed.get("agent_text", "¡Excelente trabajo! Has completado tu evaluación inicial."),
                    "placement_complete": True,
                    "level": parsed.get("level", "A1"),
                    "notes": parsed.get("notes", "Good baseline vocabulary and comprehension.")
                }
        except Exception:
            pass

        # Heuristic level estimation fallback
        words = len(learner_text.split())
        level = "A1"
        if words > 7 or any(w in learner_text.lower() for w in ["porque", "cuando", "estoy", "quiero", "gustaría", "trabajo", "viajar"]):
            level = "A2"
        if any(w in learner_text.lower() for w in ["quisiera", "aunque", "había", "he estado", "desarrollo"]):
            level = "B1"

        return {
            "agent_text": f"¡Fantástico! Hemos determinado que tu nivel inicial es {level}. ¡Empecemos a practicar!",
            "placement_complete": True,
            "level": level,
            "notes": f"Estimated {level} based on communicative clarity and vocabulary expression."
        }
    else:
        # Intermediate turn
        if llm_output and "{" not in llm_output:
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
