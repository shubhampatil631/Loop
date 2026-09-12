from typing import Dict, Any, Optional
import re
from app.config import settings
from app.models.schemas import OutcomeType
from app.llm import call_llm
from app.agents.error_analysis import is_unintelligible_or_gibberish

FALLBACK_PROMPT_TEMPLATES = {
    "el café": "You're sitting at a terrace in Barcelona and want to order a coffee. What do you say to the waiter?",
    "el boleto": "You're at the Atocha train station in Madrid and need a ticket to Seville. How do you ask for it?",
    "la cuenta": "You've finished your meal at a restaurant and are ready to pay. What do you ask the server?",
    "la estación": "You are looking for the central railway station in the city. How do you ask where it is?",
    "el menú": "You just sat down at a cafe and want to see the list of food and drinks. What do you ask for?",
    "la maleta": "You are at airport baggage claim looking for your suitcase. How do you refer to it?",
    "el hotel": "You are in a taxi looking for where you are staying for the night. How do you ask to go there?",
    "el baño": "You need to find the restroom in a museum. What do you ask?"
}

def generate_recall_prompt(
    lemma: str,
    cefr_level: str = "A1",
    translation: str = "",
    level: str = "A1",
    target_language: str = "es"
) -> str:
    """
    Generate an active-recall scenario prompt per AGENT-SPECS.md §5.
    Prompts the learner with a realistic micro-scenario that requires producing the exact target lemma.
    """
    system_prompt = f"""You are an active-recall coach for a Spanish learner. Given a target vocabulary item or grammar rule, generate a brief, realistic scenario prompt that requires the learner to produce that exact item. Do not include the target word in the prompt.

Target item: {lemma} ({cefr_level}) — meaning: {translation or 'common word'}
Learner level: {level}

Generate ONE prompt in English or simple Spanish that naturally requires "{lemma}" in response. Keep it under 25 words. Do not explain, just output the prompt.
Example format:
"You're at a train station and want to buy a ticket to Madrid. What do you say?" """

    prompt_res = call_llm(prompt=f"Generate active recall prompt for '{lemma}'", system_instruction=system_prompt, temperature=0.3)
    if prompt_res:
        return prompt_res.strip().strip('"')

    lemma_clean = lemma.lower().strip()
    if lemma_clean in FALLBACK_PROMPT_TEMPLATES:
        return FALLBACK_PROMPT_TEMPLATES[lemma_clean]

    return f"You need to use '{translation or lemma}' in a practical conversation in Spanish. How would you express this naturally?"

def evaluate_recall_response(target_lemma: str, learner_text: str) -> Dict[str, Any]:
    """
    Evaluates whether the learner's response correctly incorporated the target recall item.
    Returns {outcome: OutcomeType, is_correct: bool, feedback: str}.
    """
    if not learner_text or not learner_text.strip() or is_unintelligible_or_gibberish(learner_text):
        return {
            "outcome": "incorrect",
            "is_correct": False,
            "feedback": f"The response was unintelligible. The target expression was '{target_lemma}'."
        }

    clean_target = target_lemma.lower().replace("el ", "").replace("la ", "").replace("un ", "").replace("una ", "").replace("los ", "").replace("las ", "").strip()
    clean_input = learner_text.lower().strip()

    # Spanish grammatical stop words that should not trigger false positive matches
    stop_words = {"el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al", "en", "a", "por", "para", "con", "y", "o", "no", "si", "sí"}
    target_tokens = [t for t in re.findall(r"[a-záéíóúüñ]+", clean_target) if t not in stop_words and len(t) >= 3]

    if clean_target in clean_input:
        return {
            "outcome": "correct",
            "is_correct": True,
            "feedback": f"¡Excelente! You correctly recalled and used '{target_lemma}'."
        }
    elif target_tokens and any(token in clean_input for token in target_tokens):
        return {
            "outcome": "hesitated",
            "is_correct": True,
            "feedback": f"Close! You were looking for '{target_lemma}'."
        }
    else:
        return {
            "outcome": "incorrect",
            "is_correct": False,
            "feedback": f"The target expression was '{target_lemma}'."
        }

