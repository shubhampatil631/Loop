import json
import re
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models.db import db
from app.tools.mcp_tools import log_error_tag

VALID_ERROR_TYPES = {"gender_agreement", "conjugation", "word_order", "false_friend", "other"}
VALID_SEVERITIES = {"low", "medium", "high"}

def normalize_error_type(raw_type: str) -> str:
    """Normalizes error type to one of the 5 canonical CEFR categories."""
    raw = (raw_type or "").lower().strip().replace("-", "_").replace(" ", "_")
    if raw in VALID_ERROR_TYPES:
        return raw
    if "gender" in raw or "agreement" in raw or "masculine" in raw or "feminine" in raw:
        return "gender_agreement"
    if "conjug" in raw or "tense" in raw or "verb" in raw or "person" in raw:
        return "conjugation"
    if "order" in raw or "syntax" in raw or "position" in raw:
        return "word_order"
    if "friend" in raw or "cognate" in raw:
        return "false_friend"
    return "other"

def normalize_severity(raw_sev: str) -> str:
    raw = (raw_sev or "").lower().strip()
    return raw if raw in VALID_SEVERITIES else "medium"

from app.llm import call_llm

def call_analysis_llm(prompt: str, system_instruction: str) -> str:
    """Invokes Ollama -> Groq -> Gemini fallback chain."""
    return call_llm(prompt=prompt, system_instruction=system_instruction, temperature=0.1, json_mode=False)


def rule_based_spanish_error_analysis(text: str) -> List[Dict[str, Any]]:
    """Comprehensive deterministic rule-based analysis for Spanish errors."""
    detected = []
    txt_lower = text.lower()

    # 1. Gender Agreement Errors
    if "la problema" in txt_lower or "una problema" in txt_lower:
        detected.append({
            "vocab_item": "el problema",
            "error_type": "gender_agreement",
            "severity": "medium",
            "correction": "el problema",
            "explanation": "'Problema' is a masculine Greek-root noun ending in -a and takes the masculine article 'el'."
        })
    if "la sistema" in txt_lower or "una sistema" in txt_lower:
        detected.append({
            "vocab_item": "el sistema",
            "error_type": "gender_agreement",
            "severity": "medium",
            "correction": "el sistema",
            "explanation": "'Sistema' is masculine in Spanish and takes 'el'."
        })
    if "la tema" in txt_lower or "una tema" in txt_lower:
        detected.append({
            "vocab_item": "el tema",
            "error_type": "gender_agreement",
            "severity": "medium",
            "correction": "el tema",
            "explanation": "'Tema' is masculine and takes 'el'."
        })
    if "la idioma" in txt_lower or "una idioma" in txt_lower:
        detected.append({
            "vocab_item": "el idioma",
            "error_type": "gender_agreement",
            "severity": "medium",
            "correction": "el idioma",
            "explanation": "'Idioma' is masculine and takes 'el'."
        })
    if "café fría" in txt_lower or "cafe fria" in txt_lower:
        detected.append({
            "vocab_item": "el café",
            "error_type": "gender_agreement",
            "severity": "medium",
            "correction": "café frío",
            "explanation": "'Café' is masculine, so its adjective must agree: 'frío'."
        })
    if "mucho gracias" in txt_lower:
        detected.append({
            "vocab_item": "las gracias",
            "error_type": "gender_agreement",
            "severity": "low",
            "correction": "muchas gracias",
            "explanation": "'Gracias' is feminine plural, so it requires 'muchas'."
        })
    if "el foto" in txt_lower or "un foto" in txt_lower:
        detected.append({
            "vocab_item": "la foto",
            "error_type": "gender_agreement",
            "severity": "medium",
            "correction": "la foto",
            "explanation": "'Foto' is feminine (short for fotografía) and takes 'la'."
        })
    if "la mapa" in txt_lower or "una mapa" in txt_lower:
        detected.append({
            "vocab_item": "el mapa",
            "error_type": "gender_agreement",
            "severity": "medium",
            "correction": "el mapa",
            "explanation": "'Mapa' is masculine and takes 'el'."
        })
    if "una día" in txt_lower or "la día" in txt_lower:
        detected.append({
            "vocab_item": "el día",
            "error_type": "gender_agreement",
            "severity": "medium",
            "correction": "un día",
            "explanation": "'Día' is a masculine noun taking 'el'/'un'."
        })

    # 2. Conjugation Errors
    if re.search(r"\byo querer\b", txt_lower):
        detected.append({
            "vocab_item": "querer",
            "error_type": "conjugation",
            "severity": "high",
            "correction": "yo quiero",
            "explanation": "The verb 'querer' conjugates to 'quiero' in the first-person present indicative."
        })
    if re.search(r"\byo tener\b", txt_lower):
        detected.append({
            "vocab_item": "tener",
            "error_type": "conjugation",
            "severity": "high",
            "correction": "yo tengo",
            "explanation": "'Tener' conjugates to 'tengo' in the first-person present indicative."
        })
    if re.search(r"\byo ir\b", txt_lower):
        detected.append({
            "vocab_item": "ir",
            "error_type": "conjugation",
            "severity": "high",
            "correction": "yo voy",
            "explanation": "'Ir' conjugates irregularly to 'voy' for the first person."
        })
    if re.search(r"\byo hablar español\b", txt_lower) or re.search(r"\byo hablar\b", txt_lower):
        detected.append({
            "vocab_item": "hablar",
            "error_type": "conjugation",
            "severity": "high",
            "correction": "yo hablo",
            "explanation": "Use the conjugated verb form 'hablo' instead of the infinitive."
        })
    if re.search(r"\byo gusto\b", txt_lower):
        detected.append({
            "vocab_item": "gustar",
            "error_type": "conjugation",
            "severity": "high",
            "correction": "me gusta",
            "explanation": "In Spanish, express likes using indirect object pronouns: 'me gusta'."
        })
    if re.search(r"\byo sabo\b", txt_lower):
        detected.append({
            "vocab_item": "saber",
            "error_type": "conjugation",
            "severity": "high",
            "correction": "yo sé",
            "explanation": "'Saber' has the irregular first-person form 'sé'."
        })

    # 3. Word Order Errors
    if re.search(r"\b(el|un)\s+(negro|blanco|azul|rojo|caliente|frío)\s+(café|té|coche|carro|libro)\b", txt_lower):
        detected.append({
            "vocab_item": None,
            "error_type": "word_order",
            "severity": "medium",
            "correction": "sustantivo + adjetivo (ej. café negro)",
            "explanation": "Descriptive adjectives in Spanish typically follow the noun."
        })

    # 4. False Friend Errors
    if "embarazada" in txt_lower and any(w in txt_lower for w in ["error", "pena", "vergüenza", "tímido", "sorry", "mistake"]):
        detected.append({
            "vocab_item": "avergonzado",
            "error_type": "false_friend",
            "severity": "high",
            "correction": "avergonzado/a (o tener vergüenza)",
            "explanation": "'Embarazada' means pregnant in Spanish; to express feeling embarrassed, use 'avergonzado/a'."
        })

    return detected

def analyze_learner_errors(
    user_id: str,
    learner_text: str,
    level: str = "A1",
    target_language: str = "es"
) -> List[Dict[str, Any]]:
    """
    Analyzes learner text for errors asynchronously without interrupting the conversation.
    Normalizes categories to {"gender_agreement", "conjugation", "word_order", "false_friend", "other"},
    links mistakes to known user vocab items, logs them via MCP tool, and returns tagged errors.
    """
    if not learner_text or len(learner_text.strip().split()) < 2:
        # Edge case: Avoid false positives on single-word responses
        return []

    system_prompt = f"""You are a precise Spanish language error classifier. Given one learner turn at CEFR level {level}, identify grammatical and lexical errors ONLY from this canonical set:
- gender_agreement
- conjugation
- word_order
- false_friend
- other

Output a JSON object with this EXACT structure:
{{
  "errors": [
    {{
      "vocab_item": "the specific word/lemma involved if any, e.g. el problema, el café, querer",
      "error_type": "gender_agreement|conjugation|word_order|false_friend|other",
      "severity": "low|medium|high",
      "correction": "the corrected target phrase or sentence",
      "explanation": "one clear sentence explaining the grammatical rule"
    }}
  ]
}}

RULES:
- If there are no errors, output: {{"errors": []}}
- Do not flag stylistic variations or informal greetings as errors — only clear grammatical/lexical mistakes.
- Always output valid JSON with an "errors" list."""

    user_prompt = f"Learner input: \"{learner_text}\""
    llm_output = call_analysis_llm(user_prompt, system_prompt)

    errors = []
    if llm_output:
        try:
            cleaned = llm_output.strip()
            json_obj = None
            try:
                json_obj = json.loads(cleaned)
            except Exception:
                m_obj = re.search(r"\{.*\}", cleaned, re.DOTALL)
                if m_obj:
                    try:
                        json_obj = json.loads(m_obj.group(0))
                    except Exception:
                        pass
                if json_obj is None:
                    m_arr = re.search(r"\[.*\]", cleaned, re.DOTALL)
                    if m_arr:
                        try:
                            json_obj = json.loads(m_arr.group(0))
                        except Exception:
                            pass

            if isinstance(json_obj, dict) and "errors" in json_obj:
                errors = json_obj["errors"]
            elif isinstance(json_obj, list):
                errors = json_obj
        except Exception as e:
            print(f"[ErrorAnalysis] JSON parsing error: {e}")

    # Fallback to rule-based engine if LLM returned nothing or offline
    if not errors:
        errors = rule_based_spanish_error_analysis(learner_text)

    # Fetch user's vocabulary to match vocab_item_id if applicable
    user_vocab_items = db.get_all_user_vocab(user_id) if user_id else []

    logged_mistakes = []
    for err in errors:
        error_type = normalize_error_type(err.get("error_type", "other"))
        severity = normalize_severity(err.get("severity", "medium"))
        vocab_lemma = err.get("vocab_item")
        
        # Associate vocab_item_id if matching user's vocab list
        matched_vocab_id = None
        if vocab_lemma and user_vocab_items:
            lemma_clean = vocab_lemma.lower().strip()
            for v in user_vocab_items:
                v_lemma = v.get("lemma", "").lower().strip()
                if v_lemma == lemma_clean or lemma_clean in v_lemma or v_lemma in lemma_clean:
                    matched_vocab_id = v.get("id") or v.get("_id")
                    break

        tag_id = log_error_tag(
            user_id=user_id,
            vocab_item_id=matched_vocab_id,
            error_type=error_type,
            severity=severity,
            example_turn=learner_text,
            correction=err.get("correction"),
            explanation=err.get("explanation")
        )

        err_record = {
            "id": tag_id,
            "vocab_item_id": matched_vocab_id,
            "vocab_item": vocab_lemma,
            "error_type": error_type,
            "severity": severity,
            "correction": err.get("correction"),
            "explanation": err.get("explanation"),
            "example_turn": learner_text
        }
        logged_mistakes.append(err_record)

    return logged_mistakes

