import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.db import db
from app.agents.error_analysis import (
    analyze_learner_errors,
    normalize_error_type,
    normalize_severity,
    VALID_ERROR_TYPES
)
from fastapi.testclient import TestClient
from app.main import app

def run_error_analysis_suite():
    print("==================================================================")
    print("        LOOP ERROR-ANALYSIS AGENT VERIFICATION SUITE              ")
    print("==================================================================")

    # Setup test user
    user = db.create_user(name="ErrorTest Learner", target_language="es", goal="travel")
    user_id = user["id"]
    print(f"\n[Setup] Created test user: {user_id}")

    # 1. Test Gender Agreement Classification
    print("\n[Test 1/7] Testing Gender Agreement Detection...")
    t1 = "Tengo una problema con la cuenta del restaurante."
    errs1 = analyze_learner_errors(user_id=user_id, learner_text=t1, level="A1", target_language="es")
    print(f" -> Input: '{t1}'")
    for e in errs1:
        print(f"    - Type: {e['error_type']} | Lemma: {e.get('vocab_item')} | Correction: {e.get('correction')}")
    assert any(e["error_type"] == "gender_agreement" for e in errs1), "Should detect gender_agreement error"

    # 2. Test Verb Conjugation Classification
    print("\n[Test 2/7] Testing Conjugation Detection...")
    t2 = "Yo querer un billete para el tren de las tres."
    errs2 = analyze_learner_errors(user_id=user_id, learner_text=t2, level="A1", target_language="es")
    print(f" -> Input: '{t2}'")
    for e in errs2:
        print(f"    - Type: {e['error_type']} | Lemma: {e.get('vocab_item')} | Correction: {e.get('correction')}")
    assert any(e["error_type"] == "conjugation" for e in errs2), "Should detect conjugation error"

    # 3. Test Word Order Classification
    print("\n[Test 3/7] Testing Word Order Detection...")
    t3 = "Por favor, tráigame un caliente café."
    errs3 = analyze_learner_errors(user_id=user_id, learner_text=t3, level="A1", target_language="es")
    print(f" -> Input: '{t3}'")
    for e in errs3:
        print(f"    - Type: {e['error_type']} | Correction: {e.get('correction')}")
    assert any(e["error_type"] == "word_order" for e in errs3), "Should detect word_order error"

    # 4. Test False Friend Classification
    print("\n[Test 4/7] Testing False Friend Detection...")
    t4 = "Lo siento, estoy muy embarazada por cometer este error."
    errs4 = analyze_learner_errors(user_id=user_id, learner_text=t4, level="B1", target_language="es")
    print(f" -> Input: '{t4}'")
    for e in errs4:
        print(f"    - Type: {e['error_type']} | Correction: {e.get('correction')}")
    assert any(e["error_type"] == "false_friend" for e in errs4), "Should detect false_friend error"

    # 5. Test Edge Case: Short / Ambiguous Single-Word Replies (Must NOT tag)
    print("\n[Test 5/7] Testing Edge Case: Short Single-Word Replies (No False Positives)...")
    short_inputs = ["Hola", "Sí", "Gracias", "Bien", "Adiós"]
    for s in short_inputs:
        res = analyze_learner_errors(user_id=user_id, learner_text=s, level="A1")
        assert len(res) == 0, f"Single-word '{s}' must NOT generate false positive errors"
    print(f" -> All {len(short_inputs)} single-word inputs safely returned 0 mistake tags.")

    # 6. Test Correct Sentences (Must NOT tag errors)
    print("\n[Test 6/7] Testing Clean / Correct Inputs (No False Positives)...")
    correct_inputs = [
        "Quiero un café con leche caliente, por favor.",
        "Buenos días, ¿a qué hora sale el próximo tren?",
        "Tengo una reserva en este hotel para dos noches."
    ]
    for c in correct_inputs:
        res_c = analyze_learner_errors(user_id=user_id, learner_text=c, level="A1")
        print(f" -> '{c}' -> Errors: {len(res_c)}")
        assert len(res_c) == 0, f"Correct sentence '{c}' should produce 0 errors"

    # 7. Test Async Background Task Integration via REST API
    print("\n[Test 7/7] Testing Async Error Analysis in /session/turn and /session/end...")
    client = TestClient(app)
    
    # Start a session
    sess_res = client.post("/session/start", json={"user_id": user_id, "mode": "daily_loop"})
    assert sess_res.status_code == 200
    session_id = sess_res.json()["session_id"]
    
    # Make a turn with an intentional mistake
    turn_res = client.post("/session/turn", json={
        "session_id": session_id,
        "learner_text": "Quiero una café fría y la problema es que no tengo dinero."
    })
    assert turn_res.status_code == 200
    
    # End the session and check session summary mistakes
    end_res = client.post("/session/end", json={"session_id": session_id})
    assert end_res.status_code == 200
    end_data = end_res.json()
    print(f" -> Session Summary Mistakes Count: {len(end_data['mistakes_this_session'])}")
    for m in end_data["mistakes_this_session"]:
        print(f"    - Tag: [{m['error_type']}] Severity: {m['severity']} | Turn: '{m['example_turn']}'")
    assert len(end_data["mistakes_this_session"]) > 0, "Session summary must contain logged mistakes"

    print("\n==================================================================")
    print("   ALL 7 ERROR-ANALYSIS AGENT CHECKS PASSED SUCCESSFULLY!         ")
    print("==================================================================")

if __name__ == "__main__":
    run_error_analysis_suite()
