import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.db import db
from app.tools.mcp_tools import schedule_next_review, get_due_items
from app.agents.curriculum import curriculum_agent
from fastapi.testclient import TestClient
from app.main import app

def run_curriculum_scheduling_suite():
    print("==================================================================")
    print("      LOOP CURRICULUM/SCHEDULER (SCHEDULING) VERIFICATION SUITE   ")
    print("==================================================================")

    # 1. Setup User and Check Initial Due Items
    print("\n[Test 1/6] Testing User Creation and Due Items Query...")
    user = db.create_user(name="FSRS Scheduler Tester", target_language="es", goal="travel")
    user_id = user["id"]
    
    due_items = get_due_items(user_id=user_id, limit=10)
    print(f" -> User ID: {user_id} | Initial Due Items Count: {len(due_items)}")
    assert len(due_items) > 0, "New user must have initial due vocab items"
    for item in due_items[:3]:
        print(f"    - Due Item: '{item.lemma}' (CEFR: {item.cefr_level}, Ease: {item.ease_factor}, Interval: {item.interval_days}d)")

    # 2. Test FSRS Outcome: "correct"
    print("\n[Test 2/6] Testing FSRS Update: 'correct' Outcome...")
    target_item_1 = due_items[0]
    init_ease_1 = target_item_1.ease_factor
    init_interval_1 = target_item_1.interval_days
    init_reps_1 = target_item_1.reps

    res_correct = schedule_next_review(user_id=user_id, vocab_item_id=target_item_1.id, outcome="correct")
    assert res_correct is not None
    print(f" -> Item '{res_correct.lemma}' updated with 'correct':")
    print(f"    - Ease: {init_ease_1} -> {res_correct.ease_factor} (Expected: min({init_ease_1} + 0.1, 3.0))")
    print(f"    - Interval: {init_interval_1}d -> {res_correct.interval_days}d (Expected: round({init_interval_1} * {res_correct.ease_factor}))")
    print(f"    - Reps: {init_reps_1} -> {res_correct.reps}")
    print(f"    - Due At: {res_correct.due_at.strftime('%Y-%m-%d %H:%M:%S')}")
    assert res_correct.ease_factor == round(min(init_ease_1 + 0.1, 3.0), 2)
    assert res_correct.interval_days == max(1, round(init_interval_1 * res_correct.ease_factor))
    assert res_correct.reps == init_reps_1 + 1

    # 3. Test FSRS Outcome: "incorrect" (Reset Interval)
    print("\n[Test 3/6] Testing FSRS Update: 'incorrect' Outcome (Lapse / Mistake)...")
    target_item_2 = due_items[1]
    init_ease_2 = target_item_2.ease_factor
    init_reps_2 = target_item_2.reps

    res_incorrect = schedule_next_review(user_id=user_id, vocab_item_id=target_item_2.id, outcome="incorrect")
    assert res_incorrect is not None
    print(f" -> Item '{res_incorrect.lemma}' updated with 'incorrect':")
    print(f"    - Ease: {init_ease_2} -> {res_incorrect.ease_factor} (Expected: max({init_ease_2} - 0.3, 1.3))")
    print(f"    - Interval: -> {res_incorrect.interval_days}d (Expected: 1 day)")
    print(f"    - Reps: {init_reps_2} -> {res_incorrect.reps}")
    assert res_incorrect.ease_factor == round(max(init_ease_2 - 0.3, 1.3), 2)
    assert res_incorrect.interval_days == 1
    assert res_incorrect.reps == init_reps_2 + 1

    # 4. Test FSRS Outcome: "hesitated" (Scaled Interval)
    print("\n[Test 4/6] Testing FSRS Update: 'hesitated' Outcome...")
    # First grow interval of an item to 4 days
    db.update_vocab_item(target_item_1.id, {"interval_days": 4})
    res_hesitated = schedule_next_review(user_id=user_id, vocab_item_id=target_item_1.id, outcome="hesitated")
    assert res_hesitated is not None
    print(f" -> Item '{res_hesitated.lemma}' (4d interval) updated with 'hesitated':")
    print(f"    - Interval: 4d -> {res_hesitated.interval_days}d (Expected: round(4 * 0.7) = 3d)")
    assert res_hesitated.interval_days == max(1, round(4 * 0.7))

    # 5. Test Full Session Learning State Updates
    print("\n[Test 5/6] Testing CurriculumAgent.update_session_learning_state()...")
    test_mistake = {
        "id": "tag_err_01",
        "vocab_item": target_item_2.lemma,
        "vocab_item_id": target_item_2.id,
        "error_type": "gender_agreement"
    }
    summary = curriculum_agent.update_session_learning_state(
        user_id=user_id,
        items_touched_ids=[target_item_1.id],
        tagged_mistakes=[test_mistake],
        turn_count=3
    )
    print(f" -> Session State Result:")
    print(f"    - Mastery Delta: {summary['mastery_delta']}")
    print(f"    - Words Closer to Fluent: {summary['words_closer_to_fluent']}")
    print(f"    - Next Review ETA: {summary['next_review_eta']}")
    print(f"    - Updated Items Count: {summary['updated_items_count']}")
    assert summary["mastery_delta"] > 0
    assert summary["words_closer_to_fluent"] >= 1
    assert summary["updated_items_count"] >= 1

    # 6. Test REST API Endpoints: GET /review/due and POST /review/schedule
    print("\n[Test 6/6] Testing REST Endpoints: GET /review/due and POST /review/schedule...")
    client = TestClient(app)

    # 6a. GET /review/due
    due_res = client.get(f"/review/due?user_id={user_id}")
    assert due_res.status_code == 200
    due_data = due_res.json()
    print(f" -> GET /review/due count: {due_data['count']}")
    assert "due_items" in due_data

    # 6b. POST /review/schedule
    sched_payload = {
        "user_id": user_id,
        "vocab_item_id": target_item_1.id,
        "outcome": "correct"
    }
    sched_res = client.post("/review/schedule", json=sched_payload)
    assert sched_res.status_code == 200
    sched_item = sched_res.json()
    print(f" -> POST /review/schedule returned updated item: '{sched_item['lemma']}' (Interval: {sched_item['interval_days']}d, Ease: {sched_item['ease_factor']})")
    assert sched_item["id"] == target_item_1.id

    print("\n==================================================================")
    print("   ALL 6 CURRICULUM/SCHEDULING CHECKS PASSED SUCCESSFULLY!        ")
    print("==================================================================")

if __name__ == "__main__":
    run_curriculum_scheduling_suite()
