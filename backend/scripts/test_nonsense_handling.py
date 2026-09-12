import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.db import db
from app.agents.error_analysis import (
    analyze_learner_errors,
    is_unintelligible_or_gibberish
)
from app.agents.placement import assess_placement_turn
from app.agents.review_recall import evaluate_recall_response
from app.agents.conversation import generate_conversation_turn
from app.agents.curriculum import curriculum_agent
from fastapi.testclient import TestClient
from app.main import app

def run_nonsense_handling_suite():
    print("==================================================================")
    print("      LOOP NONSENSE & ROBUST EVALUATION VERIFICATION SUITE       ")
    print("==================================================================")

    # Setup test user
    user = db.create_user(name="Robustness Test Learner", target_language="es", goal="travel")
    user_id = user["id"]
    print(f"\n[Setup] Created test user: {user_id}")

    # 1. Test Gibberish & Unintelligible Detection
    print("\n[Test 1/6] Testing Gibberish & Unintelligible Text Detection...")
    gibberish_samples = [
        "asdfghjkl",
        "qweqweqwe zxczxc",
        "aaaaaaaaaa",
        "123456789 !!!",
        "hjksdhf sdkjfh",
        "I want a coffee please without any spanish"
    ]
    for sample in gibberish_samples:
        errs = analyze_learner_errors(user_id=user_id, learner_text=sample, level="A1")
        print(f" -> Input: '{sample}' -> Errors Detected: {len(errs)}")
        assert len(errs) > 0, f"Must detect error/unintelligible tag for nonsense: '{sample}'"
        assert errs[0]["error_type"] == "other", f"Should categorize nonsense as 'other', got '{errs[0]['error_type']}'"

    # 2. Test Placement Agent with Gibberish
    print("\n[Test 2/6] Testing Placement Agent on Gibberish Input...")
    history = [
        {"role": "agent", "text": "¡Hola! ¿Cómo te llamas y qué te gusta hacer?"},
        {"role": "learner", "text": "asdfghjk asdfghjk"},
        {"role": "agent", "text": "¿De dónde eres?"},
        {"role": "learner", "text": "qwerty zxcvbnm"}
    ]
    placement_res = assess_placement_turn(
        target_language="es",
        conversation_history=history,
        learner_text="123456 asdfghjk"
    )
    print(f" -> Final Placement Result: Level={placement_res['level']}, Notes='{placement_res['notes']}'")
    assert placement_res["level"] == "A1", f"Nonsense learner must be placed at A1, got '{placement_res['level']}'"
    assert placement_res["placement_complete"] is True

    # 3. Test Review Recall on Gibberish & Stop Word Overlap
    print("\n[Test 3/6] Testing Active Recall Evaluation on Gibberish & Stop-word Traps...")
    # 3a. Gibberish
    rec1 = evaluate_recall_response(target_lemma="el café", learner_text="asdfghjkl")
    print(f" -> Gibberish recall outcome: {rec1['outcome']} (is_correct={rec1['is_correct']})")
    assert rec1["is_correct"] is False, "Gibberish must be evaluated as incorrect"

    # 3b. Stop word overlap trap (e.g. 'de' in 'el boleto de tren' should not match 'no de nada')
    rec2 = evaluate_recall_response(target_lemma="el boleto de tren", learner_text="no de nada")
    print(f" -> Stop word trap recall outcome: {rec2['outcome']} (is_correct={rec2['is_correct']})")
    assert rec2["is_correct"] is False, "Stop word 'de' must not grant correct recall"

    # 3c. Valid recall
    rec3 = evaluate_recall_response(target_lemma="el café", learner_text="Quiero pedir un café caliente, por favor.")
    print(f" -> Valid recall outcome: {rec3['outcome']} (is_correct={rec3['is_correct']})")
    assert rec3["is_correct"] is True, "Valid sentence with target lemma must evaluate as correct"

    # 4. Test Conversation Partner on Gibberish
    print("\n[Test 4/6] Testing Conversation Partner response to Nonsense...")
    conv_reply = generate_conversation_turn(
        level="A1",
        theme="cafe",
        persona="barista",
        target_language="es",
        due_items=[],
        tagged_mistakes=[],
        conversation_history=[{"role": "agent", "text": "¡Buenos días! ¿Qué te gustaría pedir?"}],
        latest_learner_text="asdfghjkl qwerty"
    )
    print(f" -> Barista Response to Gibberish: '{conv_reply}'")
    assert "¡Muy bien!" not in conv_reply, "Agent must not praise gibberish with '¡Muy bien!'"

    # 5. Test Full Session Pipeline with All-Nonsense Turns
    print("\n[Test 5/6] Testing Full Session & Summary Pipeline with All-Nonsense Turns...")
    client = TestClient(app)
    
    # Start session
    s_start = client.post("/session/start", json={"user_id": user_id, "mode": "daily_loop"})
    assert s_start.status_code == 200
    sess_id = s_start.json()["session_id"]
    
    # 4 nonsense turns
    for t_idx in range(4):
        t_res = client.post("/session/turn", json={
            "session_id": sess_id,
            "learner_text": f"nonsense keystrokes {t_idx} asdfghjkl"
        })
        assert t_res.status_code == 200

    # End session
    s_end = client.post("/session/end", json={"session_id": sess_id})
    assert s_end.status_code == 200
    summary = s_end.json()
    
    print("\n--- Summary for All-Nonsense Session ---")
    print(f" -> Accuracy Percentage: {summary['accuracy_percentage']}%")
    print(f" -> Mastery Delta: +{summary['mastery_delta'] * 100}%")
    print(f" -> Words Solidified: {summary['words_closer_to_fluent']}")
    print(f" -> Mistakes Logged: {len(summary['mistakes_this_session'])}")
    print(f" -> Stability Factor Delta: {summary['stability_factor_delta']}")

    assert summary["accuracy_percentage"] < 40, f"Accuracy for all-nonsense turns must be low, got {summary['accuracy_percentage']}%"
    assert summary["words_closer_to_fluent"] == 0, f"Words closer to fluent must be 0 for nonsense, got {summary['words_closer_to_fluent']}"
    assert summary["mastery_delta"] == 0.0, f"Mastery delta must be 0.0 for all-nonsense session, got {summary['mastery_delta']}"
    assert len(summary["mistakes_this_session"]) > 0, "Mistakes must be logged for nonsense turns"

    # 6. Test Valid Clean Spanish Session
    print("\n[Test 6/6] Testing Clean Spanish Session (Valid Learning Performance)...")
    user_clean = db.create_user(name="Clean Spanish Learner", target_language="es", goal="cafe")
    s_clean_start = client.post("/session/start", json={"user_id": user_clean["id"], "mode": "daily_loop"})
    clean_sess_id = s_clean_start.json()["session_id"]
    
    client.post("/session/turn", json={
        "session_id": clean_sess_id,
        "learner_text": "Buenos días. Quisiera pedir un café con leche caliente, por favor."
    })
    client.post("/session/turn", json={
        "session_id": clean_sess_id,
        "learner_text": "¿Cuánto cuesta el café y el agua mineral?"
    })

    s_clean_end = client.post("/session/end", json={"session_id": clean_sess_id})
    clean_summary = s_clean_end.json()
    print("\n--- Summary for Clean Spanish Session ---")
    print(f" -> Accuracy Percentage: {clean_summary['accuracy_percentage']}%")
    print(f" -> Mastery Delta: +{clean_summary['mastery_delta'] * 100}%")
    print(f" -> Words Solidified: {clean_summary['words_closer_to_fluent']}")
    print(f" -> Mistakes Logged: {len(clean_summary['mistakes_this_session'])}")

    assert clean_summary["accuracy_percentage"] >= 80, f"Accuracy for clean Spanish must be high, got {clean_summary['accuracy_percentage']}%"
    assert clean_summary["words_closer_to_fluent"] >= 1, "Clean Spanish should advance words closer to fluent"
    assert clean_summary["mastery_delta"] > 0.0, "Mastery delta should grow for clean Spanish"

    print("\n==================================================================")
    print("     ALL 6 NONSENSE & ROBUST EVALUATION CHECKS PASSED!            ")
    print("==================================================================")

if __name__ == "__main__":
    run_nonsense_handling_suite()
