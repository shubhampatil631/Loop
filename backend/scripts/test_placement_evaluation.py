import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agents.placement import assess_placement_turn, evaluate_placement_heuristically

def run_placement_tests():
    print("==================================================================")
    print("      LOOP CEFR PLACEMENT EVALUATION VERIFICATION TEST            ")
    print("==================================================================")

    # 1. Single word minimal replies (User screenshot scenario: "no", "no", "no")
    print("\n[Test 1/7] Testing Minimal Single-Word Replies ('no', 'no', 'no')...")
    h1 = [
        {"role": "agent", "text": "¡Hola! ¿Cómo te llamas y por qué te gustaría aprender español?"},
        {"role": "learner", "text": "no"},
        {"role": "agent", "text": "¡Hola! ¿Qué te gusta hacer en tu tiempo libre?"},
        {"role": "learner", "text": "no"},
        {"role": "agent", "text": "¡Hola! Me alegra que quieras aprender español. ¿Cuál es tu nombre?"}
    ]
    res1 = assess_placement_turn("es", h1, "no")
    print(f" -> Result: Level={res1['level']}, Complete={res1['placement_complete']}")
    print(f" -> Notes: {res1['notes']}")
    print(f" -> Agent Message: {res1['agent_text']}")
    assert res1["placement_complete"] is True
    assert res1["level"] == "A1", f"Expected A1, got {res1['level']}"

    # 2. Pure English responses
    print("\n[Test 2/7] Testing English-Only Replies...")
    h2 = [
        {"role": "agent", "text": "¡Hola! ¿Cómo te llamas?"},
        {"role": "learner", "text": "I want to learn Spanish for traveling to Spain"},
        {"role": "agent", "text": "¡Muy bien! ¿Qué te gusta hacer?"},
        {"role": "learner", "text": "I like listening to music and watching movies"},
        {"role": "agent", "text": "¿Has visitado algún país hispanohablante?"}
    ]
    res2 = assess_placement_turn("es", h2, "No I have never been there")
    print(f" -> Result: Level={res2['level']}, Complete={res2['placement_complete']}")
    print(f" -> Notes: {res2['notes']}")
    assert res2["placement_complete"] is True
    assert res2["level"] == "A1", f"Expected A1 for English-only, got {res2['level']}"

    # 3. Gibberish / keyboard mash
    print("\n[Test 3/7] Testing Gibberish / Random Keystrokes...")
    h3 = [
        {"role": "agent", "text": "¡Hola! ¿Cómo te llamas?"},
        {"role": "learner", "text": "asdfghjkl qwerty"},
        {"role": "agent", "text": "¿De dónde eres?"},
        {"role": "learner", "text": "zxcvbnm 123456"},
        {"role": "agent", "text": "¿Qué te gusta?"}
    ]
    res3 = assess_placement_turn("es", h3, "hjklñ poiuyt")
    print(f" -> Result: Level={res3['level']}, Complete={res3['placement_complete']}")
    assert res3["placement_complete"] is True
    assert res3["level"] == "A1", f"Expected A1 for gibberish, got {res3['level']}"

    # 4. Elementary A2 Spanish
    print("\n[Test 4/7] Testing Elementary A2 Spanish...")
    h4 = [
        {"role": "agent", "text": "¡Hola! ¿Cómo te llamas y por qué quieres aprender español?"},
        {"role": "learner", "text": "Hola, me llamo Carlos y quiero aprender español porque me gusta viajar."},
        {"role": "agent", "text": "¡Mucho gusto Carlos! ¿Qué te gusta hacer en tu tiempo libre?"},
        {"role": "learner", "text": "En mi tiempo libre me gusta cocinar con mi familia y ver fútbol."},
        {"role": "agent", "text": "¡Qué bueno! ¿Tienes planes de viajar pronto?"}
    ]
    res4 = assess_placement_turn("es", h4, "Sí, tengo planes de viajar a México con mis amigos.")
    print(f" -> Result: Level={res4['level']}, Complete={res4['placement_complete']}")
    print(f" -> Notes: {res4['notes']}")
    assert res4["placement_complete"] is True
    assert res4["level"] == "A2", f"Expected A2, got {res4['level']}"

    # 5. Intermediate B1 Spanish (Past tenses, conditionals, connectors)
    print("\n[Test 5/7] Testing Intermediate B1 Spanish...")
    h5 = [
        {"role": "agent", "text": "¡Hola! ¿Cómo te llamas y qué experiencia tienes con el español?"},
        {"role": "learner", "text": "Hola, empecé a estudiar español hace un año porque trabajo con clientes en América Latina."},
        {"role": "agent", "text": "¡Excelente! ¿Has viajado o practicado con nativos?"},
        {"role": "learner", "text": "El año pasado estuve viviendo en Colombia durante dos meses y visité muchos lugares hermosos."},
        {"role": "agent", "text": "¿Qué aspectos del idioma te gustaría mejorar ahora?"}
    ]
    res5 = assess_placement_turn("es", h5, "Aunque entiendo bastante bien cuando me hablan, me gustaría perfeccionar los verbos en pasado.")
    print(f" -> Result: Level={res5['level']}, Complete={res5['placement_complete']}")
    print(f" -> Notes: {res5['notes']}")
    assert res5["placement_complete"] is True
    assert res5["level"] == "B1", f"Expected B1, got {res5['level']}"

    # 6. Upper Intermediate / Advanced B2 Spanish (Subjunctive, complex discourse markers)
    print("\n[Test 6/7] Testing Upper Intermediate B2 Spanish...")
    h6 = [
        {"role": "agent", "text": "¡Hola! Cuéntame sobre tus objetivos con el español."},
        {"role": "learner", "text": "Buenas tardes. Llevo varios años practicando y desearía profundizar en mi fluidez comunicativa y matices estilísticos."},
        {"role": "agent", "text": "¡Impresionante! ¿En qué contextos utilizas el idioma cotidianamente?"},
        {"role": "learner", "text": "En mi ámbito profesional redacto informes técnicos; sin embargo, considero imprescindible dominar el modo subjuntivo y expresiones cotidianas."},
        {"role": "agent", "text": "¿Qué desafío lingüístico consideras prioritario en este momento?"}
    ]
    res6 = assess_placement_turn("es", h6, "Dudo que pueda alcanzar una naturalidad total sin sumergirme continuamente en debates sobre temas abstractos y complejos.")
    print(f" -> Result: Level={res6['level']}, Complete={res6['placement_complete']}")
    print(f" -> Notes: {res6['notes']}")
    assert res6["placement_complete"] is True
    assert res6["level"] == "B2", f"Expected B2, got {res6['level']}"

    # 7. Multi-turn continuity: B1 learner with short 3rd turn ("Sí, claro")
    print("\n[Test 7/7] Testing Multi-Turn Continuity (Fluent turns 1 & 2 + short turn 3)...")
    h7 = [
        {"role": "agent", "text": "¡Hola! ¿Cómo te llamas y por qué aprendes español?"},
        {"role": "learner", "text": "Hola, me gustaría hablar con fluidez porque viajo a España por motivos de trabajo."},
        {"role": "agent", "text": "¡Genial! ¿Has estado en España antes?"},
        {"role": "learner", "text": "Sí, el año pasado visité Madrid y Barcelona durante tres semanas y aprendí mucho."},
        {"role": "agent", "text": "¿Te gustó la gastronomía local?"}
    ]
    res7 = assess_placement_turn("es", h7, "Sí, claro, me encantó.")
    print(f" -> Result: Level={res7['level']}, Complete={res7['placement_complete']}")
    print(f" -> Notes: {res7['notes']}")
    assert res7["placement_complete"] is True
    assert res7["level"] in ["A2", "B1"], f"Demonstrated proficiency should be preserved, got {res7['level']}"

    print("\n==================================================================")
    print("      ALL 7 CEFR PLACEMENT EVALUATION TESTS PASSED!               ")
    print("==================================================================")

if __name__ == "__main__":
    run_placement_tests()
