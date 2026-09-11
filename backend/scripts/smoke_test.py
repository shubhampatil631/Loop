import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app

def run_smoke_test():
    print("[Smoke Test] Starting comprehensive Loop API smoke test...")
    client = TestClient(app)

    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print(f"[Smoke Test] 1. Health check OK: {res.json()}")

    # 2. Onboarding start
    onboarding_res = client.post("/onboarding/start", json={
        "name": "Maya SmokeTest",
        "target_language": "es",
        "goal": "travel"
    })
    assert onboarding_res.status_code == 200, f"Onboarding start failed: {onboarding_res.text}"
    onboarding_data = onboarding_res.json()
    user_id = onboarding_data["user_id"]
    placement_session_id = onboarding_data["placement_session_id"]
    print(f"[Smoke Test] 2. Onboarding start OK (user_id={user_id}, session_id={placement_session_id})")

    # 3. Placement turns (simulate 3 turns)
    turn1_res = client.post("/onboarding/placement/turn", json={
        "placement_session_id": placement_session_id,
        "learner_text": "Hola, me llamo Maya y quiero aprender español para viajar."
    })
    assert turn1_res.status_code == 200, f"Placement turn 1 failed: {turn1_res.text}"
    print(f"[Smoke Test] 3a. Placement turn 1 OK (agent: '{turn1_res.json()['agent_text'][:40]}...')")

    turn2_res = client.post("/onboarding/placement/turn", json={
        "placement_session_id": placement_session_id,
        "learner_text": "Me gusta visitar museos y comer comida típica."
    })
    assert turn2_res.status_code == 200, f"Placement turn 2 failed: {turn2_res.text}"
    print(f"[Smoke Test] 3b. Placement turn 2 OK")

    turn3_res = client.post("/onboarding/placement/turn", json={
        "placement_session_id": placement_session_id,
        "learner_text": "He viajado a México el año pasado."
    })
    assert turn3_res.status_code == 200, f"Placement turn 3 failed: {turn3_res.text}"
    turn3_data = turn3_res.json()
    assert turn3_data["placement_complete"] is True
    print(f"[Smoke Test] 3c. Placement complete OK! Assigned Level: {turn3_data['level']}")

    # 4. Start Daily Loop session
    sess_res = client.post("/session/start", json={
        "user_id": user_id,
        "mode": "daily_loop"
    })
    assert sess_res.status_code == 200, f"Session start failed: {sess_res.text}"
    sess_data = sess_res.json()
    session_id = sess_data["session_id"]
    print(f"[Smoke Test] 4. Daily Loop session started (session_id={session_id}, opening: '{sess_data['agent_text'][:40]}...')")

    # 5. Session Turn with intentional grammar slip to test Error Analysis
    turn_res = client.post("/session/turn", json={
        "session_id": session_id,
        "learner_text": "Hola, quiero un café fría y la problema es que no tengo dinero."
    })
    assert turn_res.status_code == 200, f"Session turn failed: {turn_res.text}"
    print(f"[Smoke Test] 5. Session turn processed (agent reply: '{turn_res.json()['agent_text'][:40]}...')")

    # 6. End session & get summary
    end_res = client.post("/session/end", json={"session_id": session_id})
    assert end_res.status_code == 200, f"Session end failed: {end_res.text}"
    end_data = end_res.json()
    print(f"[Smoke Test] 6. Session summary OK (mastery_delta={end_data['mastery_delta']}, mistakes_tagged={len(end_data['mistakes_this_session'])})")

    # 7. Progress check
    prog_res = client.get(f"/progress?user_id={user_id}")
    assert prog_res.status_code == 200, f"Progress check failed: {prog_res.text}"
    prog_data = prog_res.json()
    print(f"[Smoke Test] 7. Progress query OK (mastery_score={prog_data['mastery_score']}, graduated={prog_data['words_graduated']}, in_progress={prog_data['words_in_progress']})")

    # 8. Review due check
    due_res = client.get(f"/review/due?user_id={user_id}")
    assert due_res.status_code == 200, f"Review due check failed: {due_res.text}"
    due_data = due_res.json()
    print(f"[Smoke Test] 8. Due items OK (count={due_data['count']})")

    print("\n[Smoke Test] ALL 8 BACKEND INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_smoke_test()
