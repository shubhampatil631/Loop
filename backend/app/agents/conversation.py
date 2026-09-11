from typing import List, Dict, Any, Optional
from app.config import settings
from app.tools.mcp_tools import fetch_level_vocab
from app.llm import call_llm

def call_conversation_llm(prompt: str, system_instruction: str) -> str:
    """Call LLM with Ollama -> Groq -> Gemini fallback."""
    return call_llm(prompt=prompt, system_instruction=system_instruction, temperature=0.7)

def generate_conversation_turn(
    level: str,
    theme: str,
    persona: str,
    target_language: str,
    due_items: List[Dict[str, Any]],
    tagged_mistakes: List[Dict[str, Any]],
    conversation_history: List[Dict[str, str]],
    latest_learner_text: Optional[str] = None
) -> str:
    """
    Generates the next conversation turn strictly grounded in level-appropriate CEFR vocab (RAG)
    and weaving in due spaced-repetition items and past mistakes.
    """
    due_lemmas = [d.get("lemma") for d in due_items if d.get("lemma")]
    due_str = ", ".join(due_lemmas) if due_lemmas else "none"

    # 1. Dynamic RAG retrieval biased by theme, persona, due words, and context
    semantic_query = f"{theme} {persona} {' '.join(due_lemmas)} {latest_learner_text or 'greeting'}".strip()
    retrieved = fetch_level_vocab(level=level, theme=theme, k=5, query_text=semantic_query)
    
    vocab_examples = [
        f"• {r.get('document', '')} (lemma: {r.get('metadata', {}).get('lemma', '')}, {r.get('metadata', {}).get('cefr_level', level)})"
        for r in retrieved if r.get("document")
    ]
    vocab_str = "\n".join(vocab_examples) if vocab_examples else "Basic conversational Spanish sentences"

    mistake_items = []
    for m in tagged_mistakes:
        err = m.get("error_type", "")
        corr = m.get("correction", "")
        ex = m.get("example_turn", "")
        mistake_items.append(f"[{err}] past slip: '{ex}' -> target correct form: '{corr}'")
    mistakes_str = "; ".join(mistake_items) if mistake_items else "none"

    system_prompt = f"""You are roleplaying as {persona} in a {theme}-themed scenario, speaking {target_language} with a learner at CEFR level {level}.

CRITICAL RAG GROUNDING CONSTRAINTS:
1. Speak strictly at or below CEFR level {level}. Do not use complex grammatical structures or advanced vocabulary that exceeds level {level}.
2. Use the following retrieved in-level reference vocabulary and sentences as your stylistic and lexical anchor:
{vocab_str}

REPETITION & DRILL INSTRUCTIONS:
- Naturally work in these spaced-repetition target words if a natural opening arises: {due_str}.
- If a natural opening arises, prompt the learner to use one of these structures they've previously struggled with: {mistakes_str}.
- Keep each turn to 1-2 short, natural sentences in character as {persona}.
- Do NOT break character to explain grammar or translate unless specifically asked in-character."""

    if not latest_learner_text and not conversation_history:
        # Opening turn
        user_prompt = f"Start the roleplay as {persona} with a warm, natural 1-2 sentence opening in {target_language} matching CEFR {level}."
    else:
        history_lines = [f"{t.get('role')}: {t.get('text')}" for t in conversation_history]
        if latest_learner_text:
            history_lines.append(f"learner: {latest_learner_text}")
        history_str = "\n".join(history_lines)
        user_prompt = f"Conversation history:\n{history_str}\n\nRespond as {persona} (1-2 sentences at CEFR {level}):"

    reply = call_conversation_llm(user_prompt, system_prompt)

    if not reply:
        # Heuristic grounded fallback if LLMs offline
        if not latest_learner_text and not conversation_history:
            if theme in ["travel", "station"]:
                reply = "¡Hola! Bienvenido a Madrid. ¿En qué puedo ayudarte hoy en la estación?"
            elif theme in ["cafe", "food"]:
                reply = "¡Buenos días! ¿Qué te gustaría pedir hoy en nuestra cafetería?"
            elif theme == "work":
                reply = "¡Hola! ¿Listo para nuestra reunión de equipo hoy?"
            else:
                reply = f"¡Hola! Qué gusto saludarte. ¿Cómo estás hoy?"
        else:
            txt = (latest_learner_text or "").lower()
            if "café" in txt or "pedir" in txt or "quiero" in txt or "por favor" in txt:
                reply = "¡Perfecto! ¿Te gustaría un café caliente o prefieres un agua mineral fría?"
            elif "gracias" in txt or "de nada" in txt:
                reply = "¡Un placer atenderte! ¿Necesitas algo más para llevar?"
            elif "billete" in txt or "boleto" in txt or "tren" in txt:
                reply = "El próximo tren sale a las tres. ¿Quieres billete de ida o de ida y vuelta?"
            elif "cuenta" in txt or "pagar" in txt:
                reply = "Aquí tiene la cuenta. ¿Prefiere pagar con tarjeta de crédito o en efectivo?"
            else:
                reply = "¡Muy bien! ¿En qué más puedo ayudarte hoy?"

    return reply

