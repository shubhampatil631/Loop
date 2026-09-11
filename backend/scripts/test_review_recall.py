import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.db import db
from app.agents.review_recall import generate_recall_prompt, evaluate_recall_response
from fastapi.testclient import TestClient
from app.main import app

def run_review_recall_suite():
    print("==================================================================")
    print("        LOOP REVIEW/RECALL AGENT VERIFICATION SUITE (DAY 16)      ")
    print("==================================================================")

    # 1. Setup User
    user = db.create_user(name="Recall Tester", target_language="es", goal="travel")
    user_id = user["id"]
    print(f"\n[Step 1] Initialized test user: {user_id}")

    # 2. Test Scenario Prompt Generation
    print("\n[Step 2] Testing Active Recall Prompt Generation...")
    items_to_test = [
        {"lemma": "el café", "cefr_level": "A1", "translation": "coffee"},
        {"lemma": "el boleto", "cefr_level": "A1", "translation": "ticket"},
        {"lemma": "la cuenta", "cefr_level": "A1", "translation": "the bill"}
    ]
    for item in items_to_test:
        prompt = generate_recall_prompt(
            lemma=item["lemma"],
            cefr_level=item["cefr_level"],
            translation=item["translation"],
            level="A1"
        )
        print(f" -> Target: '{item['lemma']}' -> Scenario Prompt: \"{prompt}\"")
        assert len(prompt) > 10
        # Target Spanish word should not be trivially revealed in the prompt text
        assert item["lemma"].lower() not in prompt.lower() or "Completa" not in prompt

    # 3. Test Active Recall Evaluation Logic
    print("\n[Step 3] Testing Active Recall Response Evaluation...")
    # 3a. Correct
    eval_corr = evaluate_recall_response(target_lemma="el café", learner_text="Quiero un café con leche.")
    print(f" -> 'Quiero un café con leche' vs 'el café' -> Outcome: {eval_corr['outcome']} (is_correct: {eval_corr['is_correct']})")
    assert eval_corr["outcome"] == "correct"
    assert eval_corr["is_correct"] is True

    # 3b. Hesitated / partial
    eval_hes = evaluate_recall_response(target_lemma="el boleto de tren", learner_text="Necesito un boleto.")
    print(f" -> 'Necesito un boleto' vs 'el boleto de tren' -> Outcome: {eval_hes['outcome']}")
    assert eval_hes["outcome"] in ["correct", "hesitated"]

    # 3c. Incorrect
    eval_inc = evaluate_recall_response(target_lemma="la cuenta", learner_text="No sé cómo se dice.")
    print(f" -> 'No sé cómo se dice' vs 'la cuenta' -> Outcome: {eval_inc['outcome']}")
    assert eval_inc["outcome"] == "incorrect"
    assert eval_inc["is_correct"] is False

    # 4. Test REST Endpoints via TestClient
    print("\n[Step 4] Testing REST API /review/prompt and /review/evaluate...")
    client = TestClient(app)

    # 4a. Get Due Items
    due_res = client.get(f"/review/due?user_id={user_id}")
    assert due_res.status_code == 200
    due_items = due_res.json()["due_items"]
    assert len(due_items) > 0
    target_item = due_items[0]
    target_id = target_item["id"]
    target_lemma = target_item["lemma"]
    print(f" -> Retrieved due item: '{target_lemma}' (ID: {target_id})")

    # 4b. POST /review/prompt
    p_res = client.post("/review/prompt", json={
        "lemma": target_lemma,
        "cefr_level": "A1",
        "translation": "beverage",
        "level": "A1"
    })
    assert p_res.status_code == 200
    p_data = p_res.json()
    print(f" -> Generated Prompt from API: \"{p_data['prompt']}\"")
    assert "prompt" in p_data

    # 4c. POST /review/evaluate (Correct Submission)
    eval_payload = {
        "user_id": user_id,
        "vocab_item_id": target_id,
        "target_lemma": target_lemma,
        "learner_text": f"Por favor, deme {target_lemma} caliente."
    }
    eval_api_res = client.post("/review/evaluate", json=eval_payload)
    assert eval_api_res.status_code == 200
    eval_api_data = eval_api_res.json()
    print(f" -> Evaluated via API: Outcome = {eval_api_data['outcome']}, Feedback = \"{eval_api_data['feedback']}\"")
    assert eval_api_data["outcome"] == "correct"
    assert eval_api_data["updated_item"]["interval_days"] >= 2

    print("\n==================================================================")
    print("   ALL REVIEW/RECALL AGENT CHECKS PASSED SUCCESSFULLY!            ")
    print("==================================================================")

if __name__ == "__main__":
    run_review_recall_suite()
