import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agents.error_analysis import analyze_learner_errors
from app.models.db import db

def test_llm_multiword():
    print("==================================================================")
    print("     TESTING LLM ERROR ANALYSIS ON MULTI-WORD NONSENSE           ")
    print("==================================================================")

    user = db.create_user(name="MultiWord Tester", target_language="es", goal="travel")
    user_id = user["id"]

    test_cases = [
        ("I don't know what you are saying please give me pizza", "Multi-word Pure English"),
        ("blablabla wxyz qwerty uiop asdf", "Multi-word Keyboard Mash & Gibberish"),
        ("no no no no no", "Multi-word Repetitive Non-Answer"),
        ("shmorf glorp zorp flubber zorp", "Multi-word Fake/Nonsense Words"),
        ("hola me gusta zorp flubber qwerty", "Multi-word Spanish mixed with Nonsense"),
        ("Quiero pedir un café con leche caliente, por favor.", "Legitimate Spanish (No error expected)")
    ]

    for text, label in test_cases:
        print(f"\n--- Testing [{label}] ---")
        print(f"Input: \"{text}\"")
        errors = analyze_learner_errors(user_id=user_id, learner_text=text, level="A1", target_language="es")
        print(f"Errors Detected: {len(errors)}")
        for e in errors:
            print(f"  - Type: {e.get('error_type')}")
            print(f"  - Severity: {e.get('severity')}")
            print(f"  - Correction: {e.get('correction')}")
            print(f"  - Explanation: {e.get('explanation')}")

        if "Legitimate" in label:
            assert len(errors) == 0, f"Expected 0 errors for valid Spanish, got {len(errors)}"
            print("  -> PASSED: Clean Spanish correctly produced 0 errors.")
        else:
            assert len(errors) > 0, f"Expected at least 1 error for nonsense: '{text}', got 0"
            print(f"  -> PASSED: Multi-word nonsense correctly tagged as '{errors[0]['error_type']}'.")

    print("\n==================================================================")
    print("   ALL MULTI-WORD NONSENSE LLM TESTS PASSED SUCCESSFULLY!         ")
    print("==================================================================")

if __name__ == "__main__":
    test_llm_multiword()
