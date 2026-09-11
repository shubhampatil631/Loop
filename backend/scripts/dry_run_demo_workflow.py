import time
import requests
import json
from datetime import datetime, timedelta

API_BASE = "http://127.0.0.1:8000"

def run_demo_dry_run():
    print("==================================================================")
    print("      LOOP: EXACT DEMO WORKFLOW DRY-RUN VERIFICATION              ")
    print("==================================================================")

    # 1. Health check
    t0 = time.time()
    res = requests.get(f"{API_BASE}/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print(f"\n[Step 1] Health check OK in {time.time()-t0:.2f}s: {res.json()}")

    # 2. Onboarding start for Maya Demo
    t0 = time.time()
    res = requests.post(f"{API_BASE}/onboarding/start", json={
        "name": "Maya Demo",
        "target_language": "es",
        "goal": "travel"
    })
    assert res.status_code == 200, f"Onboarding failed: {res.text}"
    data = res.json()
    user_id = data["user_id"]
    placement_id = data["placement_session_id"]
    greeting = data.get("greeting", "")
    print(f"\n[Step 2] Onboarding started in {time.time()-t0:.2f}s:")
    print(f" -> User ID: {user_id}")
    print(f" -> Placement Session ID: {placement_id}")
    print(f" -> Greeting: \"{greeting}\"")

    # 3. Placement Turn 1
    t0 = time.time()
    p1 = requests.post(f"{API_BASE}/onboarding/placement/turn", json={
        "placement_session_id": placement_id,
        "learner_text": "Hola, me llamo Maya y quiero aprender español para viajar a España."
    })
    assert p1.status_code == 200
    p1_data = p1.json()
    print(f"\n[Step 3] Placement Turn 1 completed in {time.time()-t0:.2f}s:")
    print(f" -> Agent Reply: \"{p1_data['agent_text'][:80]}...\"")
    assert not p1_data["placement_complete"]

    # 4. Placement Turn 2
    t0 = time.time()
    p2 = requests.post(f"{API_BASE}/onboarding/placement/turn", json={
        "placement_session_id": placement_id,
        "learner_text": "Me gusta visitar museos y comer comida típica."
    })
    assert p2.status_code == 200
    p2_data = p2.json()
    print(f"\n[Step 4] Placement Turn 2 completed in {time.time()-t0:.2f}s:")
    print(f" -> Agent Reply: \"{p2_data['agent_text'][:80]}...\"")
    assert not p2_data["placement_complete"]

    # 5. Placement Turn 3 (Final Assessment)
    t0 = time.time()
    p3 = requests.post(f"{API_BASE}/onboarding/placement/turn", json={
        "placement_session_id": placement_id,
        "learner_text": "He viajado a México el año pasado."
    })
    assert p3.status_code == 200
    p3_data = p3.json()
    print(f"\n[Step 5] Placement Turn 3 completed in {time.time()-t0:.2f}s:")
    print(f" -> Agent Final Message: \"{p3_data['agent_text'][:80]}...\"")
    print(f" -> Placement Complete: {p3_data['placement_complete']}")
    print(f" -> Assigned Level: {p3_data['level']}")
    assert p3_data["placement_complete"] is True
    assert p3_data["level"] in ["A1", "A2", "B1"]

    # 6. Session 1: First Daily Loop (Roleplay in Cafe)
    t0 = time.time()
    s1_start = requests.post(f"{API_BASE}/session/start", json={
        "user_id": user_id,
        "mode": "daily_loop"
    })
    assert s1_start.status_code == 200
    s1_data = s1_start.json()
    s1_id = s1_data["session_id"]
    scenario = s1_data.get("scenario", "")
    opening_turn = s1_data["agent_text"]
    print(f"\n[Step 6] Session 1 Started in {time.time()-t0:.2f}s:")
    print(f" -> Session ID: {s1_id}")
    print(f" -> Scenario: {scenario}")
    print(f" -> Opening Greeting: \"{opening_turn}\"")

    # 7. Session 1 Turn with Deliberate Grammar Slip
    slip_text = "Hola, quiero un café fría y la problema es que no tengo dinero."
    t0 = time.time()
    s1_turn = requests.post(f"{API_BASE}/session/turn", json={
        "session_id": s1_id,
        "learner_text": slip_text
    })
    assert s1_turn.status_code == 200
    s1_turn_data = s1_turn.json()
    print(f"\n[Step 7] Session 1 Turn processed in {time.time()-t0:.2f}s:")
    print(f" -> Learner Input: \"{slip_text}\"")
    print(f" -> Agent In-Character Reply: \"{s1_turn_data['agent_text']}\"")
    print(f" -> Turn Count: {s1_turn_data['turn_count']}")

    # 8. End Session 1 & Verify Error Tagging in Summary
    t0 = time.time()
    s1_end = requests.post(f"{API_BASE}/session/end", json={"session_id": s1_id})
    assert s1_end.status_code == 200
    s1_summary = s1_end.json()
    print(f"\n[Step 8] Session 1 Concluded in {time.time()-t0:.2f}s:")
    print(f" -> Mastery Delta: +{s1_summary['mastery_delta']}")
    print(f" -> Words Closer to Fluent: {s1_summary['words_closer_to_fluent']}")
    print(f" -> Next Review ETA: {s1_summary['next_review_eta']}")
    print(f" -> Tagged Mistakes Count: {len(s1_summary['mistakes_this_session'])}")
    assert len(s1_summary["mistakes_this_session"]) > 0, "Mistake must be tagged in session summary"

    target_mistake_id = None
    for m in s1_summary["mistakes_this_session"]:
        print(f"    - [{m['error_type']}] Severity: {m['severity']} | Lemma: {m.get('vocab_item_id') or 'grammar'} | Turn: '{m['example_turn']}' -> Correct: '{m.get('correction')}'")
        if not target_mistake_id:
            target_mistake_id = m["id"]

    # 9. Simulate 3 Days Elapsed (Move mistake into optimal 2-5 day forgetting window)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.models.db import db

    db.update_mistake_tag(target_mistake_id, {
        "created_at": datetime.utcnow() - timedelta(days=3),
        "retriggered_count": 0
    })
    print(f"\n[Step 9] Simulated 3 days elapsed for mistake '{target_mistake_id}'. (Now in 2-5d forgetting curve)")

    # 10. Session 2: Start Second Session (The Re-trigger Wow Moment)
    t0 = time.time()
    s2_start = requests.post(f"{API_BASE}/session/start", json={
        "user_id": user_id,
        "mode": "daily_loop"
    })
    assert s2_start.status_code == 200
    s2_data = s2_start.json()
    s2_id = s2_data["session_id"]
    s2_doc = db.get_session(s2_id)
    retriggered = s2_doc.get("mistakes_retriggered", [])
    print(f"\n[Step 10] Session 2 Started in {time.time()-t0:.2f}s:")
    print(f" -> Session ID: {s2_id}")
    print(f" -> Retriggered Mistakes in Session Context: {retriggered}")
    print(f" -> Session 2 Agent Opening (weaving in past error): \"{s2_data['agent_text']}\"")
    assert target_mistake_id in retriggered, f"Mistake {target_mistake_id} must be selected for retriggering"

    # 11. Session 2 Turn: Learner Produces the Correct Target Form
    correct_text = "Hola, hoy sí quiero un café frío, por favor, y un vaso de agua."
    t0 = time.time()
    s2_turn = requests.post(f"{API_BASE}/session/turn", json={
        "session_id": s2_id,
        "learner_text": correct_text
    })
    assert s2_turn.status_code == 200
    s2_turn_data = s2_turn.json()
    print(f"\n[Step 11] Session 2 Turn processed in {time.time()-t0:.2f}s:")
    print(f" -> Learner Correct Input: \"{correct_text}\"")
    print(f" -> Agent Reply: \"{s2_turn_data['agent_text']}\"")

    # 12. End Session 2
    t0 = time.time()
    s2_end = requests.post(f"{API_BASE}/session/end", json={"session_id": s2_id})
    assert s2_end.status_code == 200
    s2_summary = s2_end.json()
    print(f"\n[Step 12] Session 2 Concluded in {time.time()-t0:.2f}s:")
    print(f" -> Mastery Delta: +{s2_summary['mastery_delta']}")
    print(f" -> Words Closer to Fluent: {s2_summary['words_closer_to_fluent']}")
    assert s2_summary["mastery_delta"] > 0

    # 13. Progress Dashboard
    t0 = time.time()
    prog_res = requests.get(f"{API_BASE}/progress?user_id={user_id}")
    assert prog_res.status_code == 200
    prog = prog_res.json()
    print(f"\n[Step 13] Progress query in {time.time()-t0:.2f}s:")
    print(f" -> Mastery Score: {prog['mastery_score']} ({int(prog['mastery_score']*100)}%)")
    print(f" -> Graduated Words: {prog['words_graduated']}")
    print(f" -> Words In Progress: {prog['words_in_progress']}")
    print(f" -> Streak: {prog['streak_days']} day(s)")

    # 14. Weekly AI Digest
    t0 = time.time()
    digest_res = requests.get(f"{API_BASE}/progress/digest?user_id={user_id}")
    assert digest_res.status_code == 200
    digest = digest_res.json()
    print(f"\n[Step 14] Weekly AI Digest in {time.time()-t0:.2f}s:")
    print(f" -> Summary: \"{digest.get('summary')}\"")
    print(f" -> Strength: \"{digest.get('strength')}\"")
    print(f" -> Focus Area: \"{digest.get('focus_area')}\"")

    # 15. Active Recall Micro-Prompt & Evaluate
    t0 = time.time()
    due_res = requests.get(f"{API_BASE}/review/due?user_id={user_id}")
    assert due_res.status_code == 200
    due_items = due_res.json().get("due_items", [])
    print(f"\n[Step 15] Review Due Items in {time.time()-t0:.2f}s: {len(due_items)} item(s)")

    if due_items:
        test_item = due_items[0]
        prompt_res = requests.post(f"{API_BASE}/review/prompt", json={
            "lemma": test_item["lemma"],
            "cefr_level": test_item["cefr_level"]
        })
        assert prompt_res.status_code == 200
        print(f" -> Active Recall Prompt for '{test_item['lemma']}': \"{prompt_res.json().get('prompt')}\"")

        eval_res = requests.post(f"{API_BASE}/review/evaluate", json={
            "user_id": user_id,
            "vocab_item_id": test_item["id"],
            "target_lemma": test_item["lemma"],
            "learner_text": f"Quiero {test_item['lemma']} por favor."
        })
        assert eval_res.status_code == 200
        eval_data = eval_res.json()
        print(f" -> Active Recall Evaluation: Outcome={eval_data['outcome']}, IsCorrect={eval_data['is_correct']}")
        print(f" -> Feedback: \"{eval_data['feedback']}\"")

    # 16. Admin / Learners Directory & History
    t0 = time.time()
    users_res = requests.get(f"{API_BASE}/users?limit=10")
    assert users_res.status_code == 200
    learners_count = users_res.json().get("count", 0)
    print(f"\n[Step 16] Learners Directory query in {time.time()-t0:.2f}s: {learners_count} registered learners")

    hist_res = requests.get(f"{API_BASE}/users/{user_id}/history")
    assert hist_res.status_code == 200
    hist = hist_res.json()
    print(f" -> Full History for {hist['user']['name']}:")
    print(f"    - Total Sessions Recorded: {hist['statistics']['total_sessions']}")
    print(f"    - Total Mistakes Classified: {hist['statistics']['total_mistakes_tagged']}")
    print(f"    - Vocab Items Tracked: {hist['statistics']['vocab_items_tracked']}")

    print("\n==================================================================")
    print("   EXACT DEMO SCRIPT DRY-RUN PASSED 100% WITH ZERO ISSUES!        ")
    print("==================================================================")

if __name__ == "__main__":
    run_demo_dry_run()
