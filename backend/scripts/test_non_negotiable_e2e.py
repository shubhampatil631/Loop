import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.db import db
from fastapi.testclient import TestClient
from app.main import app

def run_non_negotiable_e2e_test():
    print("==================================================================")
    print("      LOOP: THE NON-NEGOTIABLE END-TO-END TEST (DAY 12)           ")
    print("      'Confirm a mistake from Session 1 is naturally woven        ")
    print("       into Session 2 after 3 days elapsed - twice in a row'      ")
    print("==================================================================")

    client = TestClient(app)

    def execute_e2e_retrigger_cycle(cycle_num: int, user_name: str, goal: str, slip_text: str, correct_text: str):
        print(f"\n>>>>>>>> STARTING E2E RE-TRIGGER CYCLE #{cycle_num} ({user_name} - {goal.upper()}) <<<<<<<<")

        # -------------------------------------------------------------
        # STEP 1: ONBOARDING & PLACEMENT CONVERSATION
        # -------------------------------------------------------------
        print("\n[Step 1] Onboarding new learner...")
        onboard_res = client.post("/onboarding/start", json={
            "name": user_name,
            "target_language": "es",
            "goal": goal
        })
        assert onboard_res.status_code == 200, f"Onboarding failed: {onboard_res.text}"
        onboard_data = onboard_res.json()
        user_id = onboard_data["user_id"]
        placement_id = onboard_data["placement_session_id"]
        print(f" -> User '{user_name}' initialized with ID: {user_id}")
        print(f" -> Placement Session ID: {placement_id}")

        print("\n[Step 2] Executing 3-turn Placement Assessment...")
        # Placement Turn 1
        p_turn1 = client.post("/onboarding/placement/turn", json={
            "placement_session_id": placement_id,
            "learner_text": f"Hola, me llamo {user_name} y quiero aprender español para {goal}."
        })
        assert p_turn1.status_code == 200
        assert p_turn1.json()["placement_complete"] is False

        # Placement Turn 2
        p_turn2 = client.post("/onboarding/placement/turn", json={
            "placement_session_id": placement_id,
            "learner_text": "Me gusta viajar y hablar con personas locales."
        })
        assert p_turn2.status_code == 200
        assert p_turn2.json()["placement_complete"] is False

        # Placement Turn 3 (Final Assessment)
        p_turn3 = client.post("/onboarding/placement/turn", json={
            "placement_session_id": placement_id,
            "learner_text": "He practicado un poco de vocabulario básico."
        })
        assert p_turn3.status_code == 200
        p_final = p_turn3.json()
        assert p_final["placement_complete"] is True
        level = p_final["level"] or "A1"
        print(f" -> Placement Complete! Assessed CEFR Level: {level}")

        # -------------------------------------------------------------
        # STEP 2: SESSION 1 - FIRST DAILY LOOP (LEARNER MAKES MISTAKE)
        # -------------------------------------------------------------
        print("\n[Step 3] Starting Session 1 (First Daily Loop)...")
        s1_start = client.post("/session/start", json={"user_id": user_id, "mode": "daily_loop"})
        assert s1_start.status_code == 200
        s1_data = s1_start.json()
        s1_id = s1_data["session_id"]
        print(f" -> Session 1 Active: ID={s1_id}, Scenario='{s1_data.get('scenario')}'")
        print(f" -> Agent Opening Turn: \"{s1_data['agent_text']}\"")

        print(f"\n[Step 4] Session 1 Turns (Learner intentionally makes slip: '{slip_text}')...")
        s1_turn = client.post("/session/turn", json={
            "session_id": s1_id,
            "learner_text": slip_text
        })
        assert s1_turn.status_code == 200
        print(f" -> Agent In-Character Reply: \"{s1_turn.json()['agent_text']}\"")

        # End Session 1
        s1_end = client.post("/session/end", json={"session_id": s1_id})
        assert s1_end.status_code == 200
        s1_summary = s1_end.json()
        print(f"\n[Step 5] Session 1 Concluded:")
        print(f" -> Mastery Delta: {s1_summary['mastery_delta']}")
        print(f" -> Mistakes Tagged in Session 1: {len(s1_summary['mistakes_this_session'])}")
        assert len(s1_summary["mistakes_this_session"]) > 0, "Session 1 must have logged the mistake"
        
        tagged_mistake = s1_summary["mistakes_this_session"][0]
        mistake_id = tagged_mistake["id"]
        print(f"    - Error Tag ID: {mistake_id} | Type: {tagged_mistake['error_type']} | Correction: '{tagged_mistake.get('correction')}'")

        # -------------------------------------------------------------
        # STEP 3: SIMULATE 3 DAYS PASSING (NATURAL FORGETTING WINDOW)
        # -------------------------------------------------------------
        print("\n[Step 6] Simulating 3 days elapsed (setting created_at = now - 3 days)...")
        db.update_mistake_tag(mistake_id, {
            "created_at": datetime.utcnow() - timedelta(days=3),
            "retriggered_count": 0
        })
        print(f" -> Mistake '{mistake_id}' successfully backdated into optimal 2-5 day forgetting window.")

        # -------------------------------------------------------------
        # STEP 4: SESSION 2 - RE-TRIGGER MOMENT (THE 'WOW' DEMO MOMENT)
        # -------------------------------------------------------------
        print("\n[Step 7] Starting Session 2 (3 days later - Agent should re-trigger earlier mistake)...")
        s2_start = client.post("/session/start", json={"user_id": user_id, "mode": "daily_loop"})
        assert s2_start.status_code == 200
        s2_data = s2_start.json()
        s2_id = s2_data["session_id"]
        print(f" -> Session 2 Active: ID={s2_id}")
        
        # Verify Session 2 document tracked the re-triggered mistake ID
        s2_doc = db.get_session(s2_id)
        retriggered_list = s2_doc.get("mistakes_retriggered", [])
        print(f" -> Session 2 Retriggered Mistakes List: {retriggered_list}")
        assert mistake_id in retriggered_list, f"Session 2 must re-trigger mistake {mistake_id}"
        print(f" -> Agent Session 2 Opening Turn: \"{s2_data['agent_text']}\"")

        print(f"\n[Step 8] Session 2 Turn (Learner now uses correct structure: '{correct_text}')...")
        s2_turn = client.post("/session/turn", json={
            "session_id": s2_id,
            "learner_text": correct_text
        })
        assert s2_turn.status_code == 200
        print(f" -> Agent Reply: \"{s2_turn.json()['agent_text']}\"")

        # End Session 2
        s2_end = client.post("/session/end", json={"session_id": s2_id})
        assert s2_end.status_code == 200
        s2_summary = s2_end.json()
        print(f"\n[Step 9] Session 2 Concluded:")
        print(f" -> Mastery Delta: +{s2_summary['mastery_delta']}")
        print(f" -> Words Closer to Fluent: {s2_summary['words_closer_to_fluent']}")
        print(f" -> Next Review ETA: {s2_summary['next_review_eta']}")
        assert s2_summary["mastery_delta"] > 0
        assert s2_summary["words_closer_to_fluent"] >= 1

        # Check Progress View
        prog_res = client.get(f"/progress?user_id={user_id}")
        assert prog_res.status_code == 200
        prog_data = prog_res.json()
        print(f" -> Final Progress State: Mastery Score = {prog_data['mastery_score']}, In Progress = {prog_data['words_in_progress']}")

        print(f"\n>>>>>>> E2E RE-TRIGGER CYCLE #{cycle_num} COMPLETED SUCCESSFULLY! <<<<<<<\n")

    # -------------------------------------------------------------
    # EXECUTE PASS 1: Cafe/Travel Theme (Gender Agreement)
    # -------------------------------------------------------------
    execute_e2e_retrigger_cycle(
        cycle_num=1,
        user_name="Maya Demo",
        goal="travel",
        slip_text="Hola, quiero un café fría y una problema con el boleto.",
        correct_text="Hola, hoy quiero un café frío y un boleto para el tren."
    )

    # -------------------------------------------------------------
    # EXECUTE PASS 2: Work Theme (Conjugation)
    # -------------------------------------------------------------
    execute_e2e_retrigger_cycle(
        cycle_num=2,
        user_name="Alex Tech",
        goal="work",
        slip_text="Buenos días, yo querer organizar la reunión con el cliente.",
        correct_text="Buenos días, yo quiero organizar la reunión hoy a las diez."
    )

    print("==================================================================")
    print("   THE NON-NEGOTIABLE END-TO-END TEST PASSED TWICE IN A ROW!      ")
    print("==================================================================")

if __name__ == "__main__":
    run_non_negotiable_e2e_test()
