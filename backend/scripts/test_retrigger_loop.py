import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.db import db
from app.tools.mcp_tools import log_error_tag
from app.agents.curriculum import curriculum_agent
from app.agents.conversation import generate_conversation_turn
from fastapi.testclient import TestClient
from app.main import app

def run_retrigger_loop_suite():
    print("==================================================================")
    print("      LOOP CURRICULUM/SCHEDULER (RE-TRIGGER) VERIFICATION SUITE   ")
    print("==================================================================")

    # 1. Setup User
    user = db.create_user(name="Retrigger Master", target_language="es", goal="travel")
    user_id = user["id"]
    print(f"\n[Step 1] Initialized test learner: {user_id}")

    # 2. Test Priority Tiering: 2-5 Days Forgetting Window Preference
    print("\n[Step 2] Testing Forgetting-Window Priority Tiering (2-5 Days Old)...")
    # Tag A: 10 days old (stale)
    tag_stale = db.log_mistake_tag(
        user_id=user_id,
        vocab_item_id=None,
        error_type="gender_agreement",
        severity="low",
        example_turn="el foto",
        correction="la foto"
    )
    db.update_mistake_tag(tag_stale["id"], {
        "created_at": datetime.utcnow() - timedelta(days=10),
        "retriggered_count": 0
    })

    # Tag B: 3 days old (ideal forgetting window: 2-5 days)
    tag_ideal = db.log_mistake_tag(
        user_id=user_id,
        vocab_item_id=None,
        error_type="gender_agreement",
        severity="medium",
        example_turn="una problema",
        correction="un problema"
    )
    db.update_mistake_tag(tag_ideal["id"], {
        "created_at": datetime.utcnow() - timedelta(days=3),
        "retriggered_count": 0
    })

    # Tag C: 1 hour old (fresh)
    tag_fresh = db.log_mistake_tag(
        user_id=user_id,
        vocab_item_id=None,
        error_type="conjugation",
        severity="high",
        example_turn="yo querer",
        correction="yo quiero"
    )

    # Query retrigger candidates
    candidates = curriculum_agent.get_retrigger_mistakes(user_id=user_id, limit=1)
    assert len(candidates) == 1
    selected = candidates[0]
    print(f" -> Retrigger Query returned: '{selected['correction']}' (Created: {selected['created_at']})")
    assert selected["id"] == tag_ideal["id"], "Must prioritize the 3-day-old mistake in the 2-5 day forgetting window"

    # Verify retriggered_count was incremented
    updated_tag = db.get_retriggerable_mistakes(user_id=user_id, limit=5)
    ideal_after = next((t for t in db.get_user_mistakes(user_id) if t["id"] == tag_ideal["id"]), None)
    assert ideal_after is not None
    assert ideal_after.get("retriggered_count") == 1
    print(" -> Retrigger count successfully incremented from 0 to 1.")

    # 3. Non-Negotiable Multi-Session Simulation (Day 12 Checkpoint)
    print("\n[Step 3] Testing Full Multi-Session Re-trigger Loop (Session 1 -> Session 2)...")
    client = TestClient(app)

    # --- SESSION 1 ---
    print(" -> Starting Session 1 (Learner makes grammar slip)...")
    s1_res = client.post("/session/start", json={"user_id": user_id, "mode": "daily_loop"})
    assert s1_res.status_code == 200
    s1_id = s1_res.json()["session_id"]

    # Turn with error: "un café fría"
    turn1_res = client.post("/session/turn", json={
        "session_id": s1_id,
        "learner_text": "Hola, quiero un café fría por favor."
    })
    assert turn1_res.status_code == 200

    # End Session 1
    end1_res = client.post("/session/end", json={"session_id": s1_id})
    assert end1_res.status_code == 200
    end1_data = end1_res.json()
    print(f" -> Session 1 Completed: {len(end1_data['mistakes_this_session'])} mistakes tagged.")
    assert len(end1_data["mistakes_this_session"]) > 0

    # --- SIMULATE 3 DAYS ELAPSED ---
    s1_tag_id = end1_data["mistakes_this_session"][0]["id"]
    db.update_mistake_tag(s1_tag_id, {
        "created_at": datetime.utcnow() - timedelta(days=3),
        "retriggered_count": 0
    })
    print(f" -> Simulated 3 days passing for mistake '{s1_tag_id}'...")

    # --- SESSION 2 ---
    print(" -> Starting Session 2 (Conversation Partner should weave in past mistake)...")
    s2_res = client.post("/session/start", json={"user_id": user_id, "mode": "daily_loop"})
    assert s2_res.status_code == 200
    s2_data = s2_res.json()
    s2_id = s2_data["session_id"]
    
    s2_sess_doc = db.get_session(s2_id)
    print(f" -> Session 2 Retriggered Mistakes in Session Document: {s2_sess_doc.get('mistakes_retriggered')}")
    assert s1_tag_id in s2_sess_doc.get("mistakes_retriggered", [])

    # Turn in Session 2: Learner uses target correct form
    s2_turn_res = client.post("/session/turn", json={
        "session_id": s2_id,
        "learner_text": "Buenos días, hoy quiero un café frío y un agua."
    })
    assert s2_turn_res.status_code == 200
    print(f" -> Session 2 Agent Reply:\n    \"{s2_turn_res.json()['agent_text']}\"")

    # End Session 2
    end2_res = client.post("/session/end", json={"session_id": s2_id})
    assert end2_res.status_code == 200
    end2_data = end2_res.json()
    print(f" -> Session 2 Summary: Mastery Delta = +{end2_data['mastery_delta']}, Words Closer = {end2_data['words_closer_to_fluent']}")
    assert end2_data["mastery_delta"] > 0

    print("\n==================================================================")
    print("   ALL CURRICULUM RE-TRIGGERING CHECKS PASSED SUCCESSFULLY!       ")
    print("==================================================================")

if __name__ == "__main__":
    run_retrigger_loop_suite()
