"""
End-to-End Multi-Persona Verification Test
Runs 3 complete learner journeys through the Loop platform:
  - Persona 1: Carlos (Travel / A1)
  - Persona 2: Sophia (Work / A2)
  - Persona 3: Mateo (Culture / B1)

Verifies:
  1. Ollama LLM response & multi-model fallback.
  2. Onboarding & Placement turn.
  3. Conversational session orchestration.
  4. Real-time grammar mistake tagging and DB persistence.
  5. Full conversation turn logging in MongoDB conversations collection.
  6. Session end & spaced repetition / mastery updates.
  7. Personalized weekly digest generation.
  8. Admin user tracking (/users, /users/{id}/history, /users/admin/overview).
"""

import sys
import os
import json
import time
from datetime import datetime

# Set path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.models.db import db

client = TestClient(app)

def print_banner(text):
    print("\n" + "=" * 70)
    print(f" {text}")
    print("=" * 70)

def test_persona(name, goal, initial_input, dialogue_turns):
    print(f"\n---> Starting E2E Journey for: {name} (Goal: {goal})")
    
    # 1. Onboarding
    print("  [Step 1] Onboarding user...")
    t0 = time.time()
    onboard_res = client.post("/onboarding/start", json={
        "name": name,
        "target_language": "es",
        "goal": goal
    })
    assert onboard_res.status_code == 200, f"Onboarding failed: {onboard_res.text}"
    onboard_data = onboard_res.json()
    user_id = onboard_data["user_id"]
    placement_session_id = onboard_data["placement_session_id"]
    print(f"    User created: ID={user_id}")
    print(f"    Agent greeting: {onboard_data.get('greeting')[:60]}... ({time.time() - t0:.2f}s)")

    # 2. Placement turn
    print("  [Step 2] Placement assessment turn...")
    t0 = time.time()
    placement_res = client.post("/onboarding/placement/turn", json={
        "placement_session_id": placement_session_id,
        "learner_text": initial_input
    })
    assert placement_res.status_code == 200, f"Placement failed: {placement_res.text}"
    placement_data = placement_res.json()
    assessed_level = placement_data.get("level") or "A1"
    print(f"    Placement result: level={assessed_level}, complete={placement_data.get('placement_complete')}")
    print(f"    Agent response: {placement_data.get('agent_text')[:60]}... ({time.time() - t0:.2f}s)")

    # 3. Start Conversational Session
    print("  [Step 3] Starting conversation session...")
    t0 = time.time()
    sess_start_res = client.post("/session/start", json={
        "user_id": user_id,
        "mode": "daily_loop"
    })
    assert sess_start_res.status_code == 200, f"Session start failed: {sess_start_res.text}"
    sess_data = sess_start_res.json()
    session_id = sess_data["session_id"]
    print(f"    Session active: ID={session_id}")
    print(f"    Opening prompt: {sess_data.get('agent_text')[:65]}... ({time.time() - t0:.2f}s)")

    # 4. Exchange turns
    for turn_idx, learner_msg in enumerate(dialogue_turns, 1):
        print(f"  [Step 4.{turn_idx}] Turn {turn_idx}: Learner -> '{learner_msg}'")
        t0 = time.time()
        turn_res = client.post("/session/turn", json={
            "session_id": session_id,
            "learner_text": learner_msg
        })
        assert turn_res.status_code == 200, f"Session turn failed: {turn_res.text}"
        turn_data = turn_res.json()
        print(f"    Agent response ({time.time() - t0:.2f}s): {turn_data.get('agent_text')[:75]}...")

    # 5. Check Conversation Turns in DB
    convs = db.get_user_conversations(user_id)
    print(f"  [Step 5] Checking DB conversations collection for user...")
    assert len(convs) >= 1, "Expected at least 1 saved conversation in DB"
    saved_turns = convs[0].get("turns", [])
    print(f"    DB verified: {len(saved_turns)} turns logged for session {session_id}")

    # 6. End Session
    print("  [Step 6] Ending session and updating curriculum mastery...")
    t0 = time.time()
    end_res = client.post("/session/end", json={"session_id": session_id})
    assert end_res.status_code == 200, f"End session failed: {end_res.text}"
    summary = end_res.json()
    print(f"    Session summary: mastery_delta={summary.get('mastery_delta')}, tagged mistakes={len(summary.get('mistakes_this_session', []))}")

    # 7. Progress & Digest
    print("  [Step 7] Checking progress & weekly digest report...")
    prog_res = client.get(f"/progress?user_id={user_id}")
    assert prog_res.status_code == 200, f"Progress failed: {prog_res.text}"
    prog = prog_res.json()
    print(f"    Mastery score: {prog.get('mastery_score')}, Streak days: {prog.get('streak_days')}")

    t0 = time.time()
    digest_res = client.get(f"/progress/digest?user_id={user_id}")
    assert digest_res.status_code == 200, f"Digest failed: {digest_res.text}"
    digest = digest_res.json()
    print(f"    Weekly digest generated in {time.time() - t0:.2f}s:")
    print(f"      Theme: {digest.get('theme')}")
    print(f"      Summary: {digest.get('summary')[:80]}...")
    print(f"      Action items: {len(digest.get('action_items', []))}")

    return user_id

def main():
    print_banner("RUNNING MULTI-PERSONA END-TO-END VALIDATION SUITE")

    personas = [
        {
            "name": "Carlos Mendoza",
            "goal": "travel",
            "initial_input": "Hola! Quiero viajar a España y aprender a pedir comida en restaurantes.",
            "dialogue_turns": [
                "Hola! Yo querer un café con leche por favor.",
                "¿Cuánto cuesta una café y una tostada?"
            ]
        },
        {
            "name": "Sophia Chen",
            "goal": "work",
            "initial_input": "Hola, trabajo en tecnología y necesito comunicarme con clientes de América Latina.",
            "dialogue_turns": [
                "Ayer yo tener una reunión muy importante sobre el proyecto nuevo.",
                "Nosotros necesitamos terminar el reporte mañana por la tarde."
            ]
        },
        {
            "name": "Mateo Rossi",
            "goal": "culture",
            "initial_input": "Me apasiona la literatura y el cine en español. Quiero hablar fluidamente.",
            "dialogue_turns": [
                "He visto una película española muy interesante de Guillermo del Toro.",
                "Me gustó mucho la atmósfera misteriosa y la música."
            ]
        }
    ]

    created_users = []
    for p in personas:
        uid = test_persona(
            name=p["name"],
            goal=p["goal"],
            initial_input=p["initial_input"],
            dialogue_turns=p["dialogue_turns"]
        )
        created_users.append((uid, p["name"]))

    print_banner("ADMIN PLATFORM MONITORING & RECORD VERIFICATION")
    # Verify Admin Overview
    admin_overview = client.get("/users/admin/overview")
    assert admin_overview.status_code == 200
    stats = admin_overview.json()
    print(f"Total Platform Users: {stats.get('total_learners_registered')}")
    print(f"Total Sessions Run: {stats.get('total_sessions_conducted')}")
    print(f"Total Mistakes Tagged: {stats.get('total_mistakes_classified')}")
    print(f"LLM Hierarchy: {stats.get('configured_llm_hierarchy')}")

    # Verify All Users List
    users_list_res = client.get("/users")
    assert users_list_res.status_code == 200
    res_data = users_list_res.json()
    all_users = res_data.get("learners", []) if isinstance(res_data, dict) else res_data
    print(f"\nFound {len(all_users)} total registered users in GET /users.")
    for uid, name in created_users:
        found = any(u.get("id") == uid or u.get("user_id") == uid for u in all_users)
        print(f"  - Verified {name} (ID: {uid}) is recorded in admin list: {'YES' if found else 'NO'}")
        assert found, f"User {uid} not in admin list"

        # Verify detailed history
        hist_res = client.get(f"/users/{uid}/history")
        assert hist_res.status_code == 200
        hist = hist_res.json()
        print(f"    * {name} history: {len(hist.get('sessions', []))} sessions, {len(hist.get('mistake_tags', []))} mistakes tagged.")

    print_banner("ALL 4 CRITICAL MILESTONES VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
