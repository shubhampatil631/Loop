import json
import re
from typing import Dict, Any, List, Optional
from app.config import settings
from app.llm import call_llm
from app.agents.error_analysis import is_unintelligible_or_gibberish

# Extensive Spanish Core Vocabulary for accurate language identification
EXTENDED_SPANISH_VOCAB = {
    # Basic greetings & common words
    "hola", "buenos", "días", "tardes", "noches", "por", "favor", "gracias", "de", "nada",
    "sí", "si", "no", "bien", "adiós", "hasta", "luego", "pronto", "perdón", "disculpe",
    # Pronouns & determiners
    "yo", "tú", "tu", "él", "el", "ella", "usted", "nosotros", "nosotras", "ellos", "ellas",
    "ustedes", "me", "te", "se", "nos", "le", "les", "lo", "la", "los", "las", "un", "una",
    "unos", "unas", "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas", "aquel",
    "mi", "mis", "su", "sus", "nuestro", "nuestra", "nuestros", "nuestras",
    # Common verbs (present, infinitive, gerund)
    "quiero", "quieres", "quiere", "queremos", "quieren", "querer",
    "tengo", "tienes", "tiene", "tenemos", "tienen", "tener",
    "soy", "eres", "es", "somos", "son", "ser",
    "estoy", "estás", "esta", "está", "estamos", "están", "estar",
    "vivo", "vives", "vive", "vivimos", "viven", "vivir",
    "trabajo", "trabajas", "trabaja", "trabajamos", "trabajan", "trabajar",
    "estudio", "estudias", "estudia", "estudiamos", "estudian", "estudiar",
    "aprendo", "aprendes", "aprende", "aprendemos", "aprenden", "aprender",
    "hablo", "hablas", "habla", "hablamos", "hablan", "hablar",
    "viajo", "viajas", "viaja", "viajamos", "viajan", "viajar",
    "visito", "visitas", "visita", "visitamos", "visitan", "visitar",
    "como", "comes", "come", "comemos", "comen", "comer",
    "bebo", "bebes", "bebe", "bebemos", "beben", "beber",
    "puedo", "puedes", "puede", "podemos", "pueden", "poder",
    "hago", "haces", "hace", "hacemos", "hacen", "hacer",
    "voy", "vas", "va", "vamos", "van", "ir",
    "gusta", "gustan", "gustaría", "gustar", "encanta", "encantan",
    "llamo", "llamas", "llama", "llamamos", "llaman", "llamarse",
    "necesito", "necesitas", "necesita", "necesitamos", "necesitan", "necesitar",
    "conozco", "conoces", "conoce", "conocemos", "conocen", "conocer",
    "saber", "sé", "sabes", "sabe", "sabemos", "saben",
    "veo", "ves", "ve", "vemos", "ven", "ver", "mirar", "escuchar",
    # Nouns & topics
    "español", "inglés", "idioma", "idiomas", "lengua", "lenguas", "palabra", "palabras",
    "país", "países", "ciudad", "ciudades", "casa", "familia", "amigo", "amigos", "amiga",
    "tiempo", "libre", "trabajo", "música", "comida", "café", "agua", "restaurante",
    "libro", "libros", "película", "películas", "viaje", "viajes", "vacaciones", "gente",
    "año", "años", "mes", "meses", "semana", "semanas", "día", "días", "hoy", "mañana", "ayer",
    # Connectors & prepositions
    "y", "e", "o", "u", "pero", "porque", "cuando", "donde", "como", "con", "sin", "para", "por",
    "en", "a", "de", "desde", "hasta", "sobre", "entre", "también", "tampoco", "más", "menos",
    "muy", "mucho", "mucha", "muchos", "muchas", "poco", "poca", "pocos", "pocas", "siempre", "nunca"
}

# Advanced syntactic & lexical markers
SUBJUNCTIVE_MARKERS = {
    "sea", "sean", "seas", "seamos", "haya", "hayan", "hayas", "hayamos",
    "tenga", "tengan", "tengas", "tengamos", "pueda", "puedan", "puedas", "podamos",
    "quiera", "quieran", "quieras", "queramos", "esté", "estén", "estés", "estemos",
    "haga", "hagan", "hagas", "hagamos", "vaya", "vayan", "vayas", "vayamos",
    "sepa", "sepan", "sepas", "sepamos", "diga", "digan", "digas", "digamos",
    "fuera", "fueran", "fueras", "fuéramos", "fuese", "fuesen", "fueses",
    "tuviera", "tuvieran", "tuvieras", "tuviéramos", "tuviese", "tuviesen",
    "pudiera", "pudieran", "pudieras", "pudiéramos", "pudiese", "pudiesen",
    "quisiera", "quisieran", "quisieras", "quisiéramos",
    "hubiera", "hubieran", "hubieras", "hubiéramos", "hubiese", "hubiesen"
}

B2_DISCOURSE_CONNECTORS = [
    "sin embargo", "por lo tanto", "a pesar de", "no obstante", "en cambio",
    "por consiguiente", "dado que", "en cuanto a", "con respecto a", "a fin de que",
    "de modo que", "a medida que", "por otra parte", "en resumen", "cabe destacar"
]

B2_ADVANCED_VOCAB = {
    "perfeccionar", "profundizar", "imprescindible", "desafío", "desafíos", "complejo",
    "complejos", "compleja", "complejas", "cotidiano", "cotidiana", "cotidianos",
    "fluidez", "redactar", "extranjero", "extranjera", "matices", "sutilezas",
    "desarrollo", "discurso", "perspectiva", "argumento", "argumentos", "profesional",
    "habilidades", "ámbito", "autonomía", "comunicativa", "desenvolverme", "sutileza"
}

PAST_TENSE_VERBS = {
    "fui", "fuiste", "fue", "fuimos", "fueron", "estuve", "estuviste", "estuvo",
    "estuvimos", "estuvieron", "estaba", "estabas", "estábamos", "estaban",
    "había", "habías", "habíamos", "habían", "hice", "hiciste", "hizo", "hicimos",
    "hicieron", "hacía", "hacías", "hacíamos", "hacían", "viví", "viviste", "vivió",
    "vivimos", "vivieron", "vivía", "vivías", "vivíamos", "vivían", "viajé",
    "viajaste", "viajó", "viajamos", "viajaron", "visité", "visitaste", "visitó",
    "visitamos", "visitaron", "aprendí", "aprendiste", "aprendió", "aprendimos",
    "aprendieron", "comí", "comiste", "comió", "comimos", "comieron", "tenía",
    "tenías", "teníamos", "tenían", "tuve", "tuviste", "tuvo", "tuvimos", "tuvieron",
    "pude", "pudiste", "pudo", "pudimos", "pudieron", "podía", "podías", "podíamos",
    "podían", "gustaba", "gustaban", "quería", "querías", "queríamos", "querían",
    "empecé", "comencé", "conocí", "llegué", "pasé", "estudié"
}

PERFECT_PARTICIPLES = {
    "viajado", "vivido", "estado", "estudiado", "aprendido", "hablado", "comido",
    "hecho", "visto", "dicho", "escrito", "trabajado", "tenido", "podido"
}

B1_CONNECTORS = [
    "aunque", "cuando", "mientras", "ya que", "para que", "siempre que", "porque",
    "desde que", "hasta que", "a veces", "el año pasado", "hace dos años", "hace un año",
    "hace tiempo", "en el futuro", "por un lado", "además de", "por eso"
]

CONDITIONAL_VERBS = {
    "gustaría", "gustarían", "quisiera", "quisieras", "quisieran", "podría", "podrías",
    "podríamos", "podrían", "debería", "deberías", "deberíamos", "deberían", "sería",
    "serías", "seríamos", "serían", "estaría", "estarías", "tendría", "tendrías"
}

def evaluate_placement_heuristically(all_learner_texts: List[str]) -> Dict[str, Any]:
    """
    Multi-feature algorithmic evaluation across ALL learner turns.
    Provides robust, deterministic CEFR calibration and pedagogical feedback.
    """
    if not all_learner_texts:
        return {
            "level": "A1",
            "notes": "Nivel inicial A1 calibrado — no se registraron respuestas del estudiante.",
            "agent_text": "¡Bienvenido a Loop! Comenzaremos desde el nivel principiante (A1) para construir bases sólidas juntos."
        }

    full_text = " ".join(all_learner_texts).strip().lower()
    words = re.findall(r"[a-záéíóúüñ]+", full_text)
    total_words = len(words)
    
    # Check if all turns are pure gibberish / keystrokes
    turns_gibberish = [is_unintelligible_or_gibberish(t) for t in all_learner_texts]
    if all(turns_gibberish) or total_words == 0:
        return {
            "level": "A1",
            "notes": "Nivel inicial A1 calibrado: respuestas no comprensibles o teclas aleatorias.",
            "agent_text": "¡Bienvenido a Loop! Comenzaremos desde el nivel principiante (A1) con vocabulario esencial y frases básicas."
        }

    # Count Spanish communicative vocabulary
    spanish_word_count = sum(
        1 for w in words
        if w in EXTENDED_SPANISH_VOCAB or w in PAST_TENSE_VERBS or w in SUBJUNCTIVE_MARKERS or w in B2_ADVANCED_VOCAB or w in PERFECT_PARTICIPLES
    )
    
    # Calculate Spanish density & average words per turn
    valid_turns = [t for t in all_learner_texts if t.strip()]
    avg_turn_length = total_words / max(1, len(valid_turns))
    spanish_density = (spanish_word_count / total_words) if total_words > 0 else 0

    # Count higher-level linguistic markers
    subjunctive_hits = sum(1 for w in words if w in SUBJUNCTIVE_MARKERS)
    b2_connector_hits = sum(1 for c in B2_DISCOURSE_CONNECTORS if c in full_text)
    b2_vocab_hits = sum(1 for w in words if w in B2_ADVANCED_VOCAB)
    b2_score = subjunctive_hits + b2_connector_hits + b2_vocab_hits

    past_verb_hits = sum(1 for w in words if w in PAST_TENSE_VERBS)
    conditional_hits = sum(1 for w in words if w in CONDITIONAL_VERBS)
    b1_connector_hits = sum(1 for c in B1_CONNECTORS if c in full_text)
    has_perfect_tense = ("he " in full_text or "has " in full_text or "ha " in full_text or "hemos " in full_text) and any(p in full_text for p in PERFECT_PARTICIPLES)
    b1_score = past_verb_hits + conditional_hits + b1_connector_hits + (2 if has_perfect_tense else 0)

    # 1. Check for A1 (Beginner / Minimal response)
    # If total words < 5 across all 3 turns, or very low Spanish density, or only 1-word replies like "no", "hola", "si"
    if total_words < 5 or spanish_word_count < 3 or (avg_turn_length < 2.5 and b1_score == 0 and b2_score == 0):
        return {
            "level": "A1",
            "notes": "Nivel inicial A1 calibrado: el estudiante responde con palabras aisladas, respuestas breves o está iniciando su aprendizaje.",
            "agent_text": "¡Bienvenido a Loop! Hemos calibrado tu nivel inicial en A1 (Principiante). Aprenderemos paso a paso con situaciones prácticas."
        }

    # If learner responded entirely in English without functional Spanish
    if spanish_density < 0.25 and b1_score == 0 and b2_score == 0:
        return {
            "level": "A1",
            "notes": "Nivel inicial A1 calibrado: respuestas principalmente en inglés / sin estructuras funcionales en español.",
            "agent_text": "¡Bienvenido a Loop! Tu nivel inicial es A1 (Principiante). Te guiaremos paso a paso para construir tu vocabulario en español."
        }

    # 2. Check for B2 (Upper Intermediate / Advanced)
    if b2_score >= 2 and total_words >= 15 and avg_turn_length >= 6:
        return {
            "level": "B2",
            "notes": "Nivel inicial B2 calibrado: demuestra excelente fluidez sintáctica, modo subjuntivo, conectores discursivos avanzados y vocabulario amplio.",
            "agent_text": "¡Excelente dominio! Tu nivel ha sido calibrado en B2 (Intermedio Alto / Avanzado). Practicaremos situaciones complejas y debates matizados."
        }

    # 3. Check for B1 (Intermediate)
    if (b1_score >= 2 or (b1_score >= 1 and total_words >= 12)) and avg_turn_length >= 4:
        return {
            "level": "B1",
            "notes": "Nivel inicial B1 calibrado: utiliza tiempos pasados, estructuras compuestas y conectores con buena fluidez comunicativa.",
            "agent_text": "¡Muy buen nivel! Tu nivel inicial ha sido establecido en B1 (Intermedio). Nos enfocaremos en perfeccionar tu fluidez y variedad gramatical."
        }

    # 4. Check for A2 (Elementary / High Beginner)
    # Multi-word coherent sentences with basic present verbs and basic vocabulary
    if avg_turn_length >= 3 and spanish_word_count >= 4:
        return {
            "level": "A2",
            "notes": "Nivel inicial A2 calibrado: capaz de formar oraciones sencillas con verbos cotidianos (gustar, querer, tener, vivir) y expresar ideas básicas.",
            "agent_text": "¡Buen trabajo! Hemos determinado que tu nivel inicial es A2 (Básico / Elemental). Ampliaremos tus estructuras y vocabulario cotidiano."
        }

    # Fallback to A1
    return {
        "level": "A1",
        "notes": "Nivel inicial A1 calibrado: vocabulario elemental y frases iniciales.",
        "agent_text": "¡Bienvenido a Loop! Tu nivel inicial es A1 (Principiante). ¡Empecemos a practicar juntos!"
    }


def assess_placement_turn(
    target_language: str,
    conversation_history: List[Dict[str, str]],
    learner_text: str
) -> Dict[str, Any]:
    """
    Evaluates one placement turn. After 3 turns, comprehensively evaluates all turns
    and returns the calibrated CEFR level (A1, A2, B1, B2) with pedagogical justification.
    """
    # Collect all learner turns across the placement session
    all_learner_turns = [
        t.get("text", "").strip()
        for t in conversation_history
        if t.get("role") == "learner" and t.get("text", "").strip()
    ]
    if learner_text and learner_text.strip():
        all_learner_turns.append(learner_text.strip())

    turn_num = len(conversation_history) // 2 + 1
    is_final = turn_num >= 3

    # Generate heuristic baseline for consistency and fallback
    heuristic_res = evaluate_placement_heuristically(all_learner_turns)

    if is_final:
        # Construct detailed transcript for LLM
        transcript_lines = []
        for t in conversation_history:
            role = "Agent" if t.get("role") == "agent" else "Learner"
            transcript_lines.append(f"{role}: {t.get('text')}")
        transcript_lines.append(f"Learner: {learner_text}")
        transcript_str = "\n".join(transcript_lines)

        system_prompt = f"""You are an expert language placement assessor and CEFR examiner for {target_language}.
Your task is to evaluate the learner's overall proficiency based on ALL their responses during this 3-turn diagnostic interview, and assign their accurate baseline CEFR Level (A1, A2, B1, or B2).

CEFR LEVEL BENCHMARK RUBRIC:
- A1 (Beginner / Breakthrough):
  * Minimal, fragmentary, or zero functional Spanish (e.g. single words like "no", "sí", "hola", "bien", numbers).
  * Responses in English (e.g. "I want to learn Spanish", "travel").
  * Random typing, keystrokes, or gibberish.
  * Formulaic single-word greetings without verb conjugation or complete sentence structure.

- A2 (Elementary / High Beginner):
  * Forms simple, coherent multi-word sentences about basic everyday topics (likes/dislikes, hobbies, family, basic travel, routine).
  * Uses common present-tense verbs correctly (e.g. "me gusta", "quiero", "tengo", "vivo", "trabajo", "estudio", "como").
  * Uses simple connectors ("y", "pero", "porque", "también").

- B1 (Intermediate / Threshold):
  * Expresses connected ideas, personal experiences, opinions, and future/conditional plans using multi-clause sentences.
  * Uses past tenses (preterite / imperfect / present perfect: "fui", "estuve", "he viajado", "visité", "viví", "era") or conditionals ("me gustaría", "quisiera").
  * Uses subordinate connectors ("cuando", "aunque", "ya que", "para que", "siempre que").

- B2 (Upper Intermediate / Vantage):
  * High fluency, nuanced vocabulary, complex syntactic structures.
  * Correct use of the subjunctive mood ("sea", "haya", "tuviera", "pueda") and advanced discourse markers ("sin embargo", "por lo tanto", "a pesar de", "no obstante").

OUTPUT FORMAT:
Output ONLY a valid JSON object:
{{
  "level": "A1" | "A2" | "B1" | "B2",
  "notes": "One concise sentence in Spanish explaining the pedagogical reason for this CEFR placement based on their responses.",
  "agent_text": "Warm, encouraging message in Spanish (with a friendly English sentence) welcoming the learner to Loop and announcing their calibrated CEFR level."
}}"""

        user_prompt = f"""Diagnostic Conversation Transcript:
{transcript_str}

Learner responses to assess:
{json.dumps(all_learner_turns, ensure_ascii=False)}

Evaluate the learner's demonstrated proficiency and output the final placement JSON."""

        llm_output = call_llm(user_prompt, system_prompt, temperature=0.2, json_mode=True)

        if llm_output:
            try:
                # Clean and extract JSON object
                clean_output = llm_output.strip()
                match = re.search(r"\{[\s\S]*\}", clean_output)
                if match:
                    parsed = json.loads(match.group(0))
                    raw_lvl = str(parsed.get("level", "")).upper()
                    
                    # Extract canonical CEFR level
                    lvl_match = re.search(r"\b(A1|A2|B1|B2)\b", raw_lvl)
                    if lvl_match:
                        assigned_lvl = lvl_match.group(1)
                    else:
                        assigned_lvl = heuristic_res["level"]

                    # Guardrail: Check for extreme mismatch with ground-truth heuristic
                    # (e.g. all gibberish / single "no" turns should never be B1/B2)
                    if heuristic_res["level"] == "A1" and assigned_lvl in ["B1", "B2"]:
                        assigned_lvl = "A1"
                    elif heuristic_res["level"] == "B2" and assigned_lvl == "A1":
                        assigned_lvl = "B2"

                    agent_msg = parsed.get("agent_text")
                    if not agent_msg or len(agent_msg.strip()) < 10:
                        agent_msg = heuristic_res["agent_text"]

                    notes = parsed.get("notes")
                    if not notes or len(notes.strip()) < 10:
                        notes = heuristic_res["notes"]

                    return {
                        "agent_text": agent_msg.strip(),
                        "placement_complete": True,
                        "level": assigned_lvl,
                        "notes": notes.strip()
                    }
            except Exception as e:
                print(f"[Placement] JSON parsing error: {e}, falling back to heuristic evaluation.")

        # Fallback to robust heuristic evaluation
        return {
            "agent_text": heuristic_res["agent_text"],
            "placement_complete": True,
            "level": heuristic_res["level"],
            "notes": heuristic_res["notes"]
        }

    else:
        # Intermediate turns (Turns 1 & 2): Adaptive questioning
        latest_text = learner_text.strip()
        is_gibberish = is_unintelligible_or_gibberish(latest_text)

        system_prompt = f"""You are a friendly, encouraging Spanish placement assessor.
The learner is undergoing a 3-turn diagnostic conversation.
Look at their previous message:
- If they replied with single words (like 'no', 'hola', 'bien') or English: be warm, supportive, and ask a very simple, beginner-friendly question with helpful English cues (e.g., '¡No te preocupes! ¿Cuál es tu comida favorita o cómo te llamas?').
- If they replied in basic Spanish (A1/A2): acknowledge what they said warmly in Spanish, and ask a simple follow-up question (e.g. about their hobbies, city, or travel goals).
- If they replied in intermediate/advanced Spanish (B1/B2): respond naturally in Spanish and ask an engaging open-ended question to test past tenses or opinions.
Keep your reply to 1-2 friendly, conversational sentences. DO NOT reveal their level yet."""

        history_str = "\n".join([f"{t.get('role')}: {t.get('text')}" for t in conversation_history])
        user_prompt = f"Conversation so far:\n{history_str}\nLearner: {latest_text}\n\nRespond briefly and ask the next question:"

        llm_output = call_llm(user_prompt, system_prompt, temperature=0.7, timeout=8.0)

        if is_gibberish:
            agent_text = "¡No te preocupes si estás empezando! ¿De dónde eres o qué te gusta hacer? (You can reply in simple words in Spanish!)"
        elif llm_output and "{" not in llm_output and len(llm_output.strip()) > 5:
            agent_text = llm_output.strip()
        else:
            if turn_num == 1:
                agent_text = "¡Mucho gusto! ¿De dónde eres y qué te gusta hacer en tu tiempo libre?"
            elif turn_num == 2:
                agent_text = "¡Qué interesante! ¿Por qué te gustaría aprender español o qué lugares te gustaría visitar?"
            else:
                agent_text = "¡Genial! ¿Has tenido alguna experiencia hablando español o viajando?"

        return {
            "agent_text": agent_text,
            "placement_complete": False,
            "level": None,
            "notes": None
        }
