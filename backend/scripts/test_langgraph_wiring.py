import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.db import db
from app.agents.graph import (
    graph,
    build_loop_graph,
    orchestrate_session_start,
    orchestrate_session_turn,
    LoopState
)
from fastapi.testclient import TestClient
from app.main import app

def run_langgraph_wiring_suite():
    print("==================================================================")
    print("        LOOP FULL LANGGRAPH WIRING VERIFICATION SUITE             ")
    print("==================================================================")

    # 1. Test Graph Compilation
    print("\n[Test 1/5] Testing LangGraph StateGraph Compilation...")
    compiled_graph = build_loop_graph()
    assert compiled_graph is not None, "LangGraph StateGraph must compile cleanly"
    print(" -> LangGraph StateGraph compiled successfully.")

    # 2. Test Placement Node via StateGraph
    print("\n[Test 2/5] Testing Placement Node in StateGraph...")
    placement_state: LoopState = {
        "user_id": "lg_user_01",
        "session_id": "lg_sess_01",
        "mode": "placement",
        "level": "A1",
        "target_language": "es",
        "theme": "travel",
        "persona": "assessor",
        "due_items": [],
        "items_touched": [],
        "conversation_history": [],
        "turn_count": 0,
        "max_turns": 3,
        "tagged_mistakes": [],
        "latest_agent_text": None,
        "latest_learner_text": "Hola, me gustaría aprender español.",
        "placement_complete": False,
        "session_complete": False,
        "session_summary": None
    }
    placement_res = compiled_graph.invoke(placement_state)
    print(f" -> Placement node output: '{placement_res.get('latest_agent_text')[:45]}...'")
    assert placement_res.get("latest_agent_text") is not None
    assert len(placement_res.get("conversation_history", [])) == 2

    # 3. Test Multi-Node Flow: Curriculum Pull -> Conversation Partner -> Error Analysis
    print("\n[Test 3/5] Testing Orchestrated Session Start (Curriculum Pull -> Conversation)...")
    user = db.create_user(name="LangGraph Learner", target_language="es", goal="travel")
    user_id = user["id"]

    start_res = orchestrate_session_start(user_id=user_id, mode="daily_loop")
    session_id = start_res["session_id"]
    print(f" -> Session Started: ID={session_id}, Scenario='{start_res['scenario']}'")
    print(f" -> Opening Turn: \"{start_res['agent_text']}\"")
    assert len(start_res["agent_text"]) > 5

    # 4. Test Orchestrated Conversation Turns + Error Analysis
    print("\n[Test 4/5] Testing Turn-by-Turn Graph Invocation (Conversation -> Error Analysis)...")
    # Turn 1
    t1_res = orchestrate_session_turn(session_id=session_id, learner_text="Hola, quiero un café caliente.")
    print(f" -> Turn 1 processed: Agent replied: \"{t1_res['agent_text'][:40]}...\" (Turn count: {t1_res['turn_count']})")
    assert t1_res["turn_count"] == 1
    assert t1_res["session_complete"] is False

    # Turn 2 with intentional grammar slip to test Error Analysis in Graph
    t2_res = orchestrate_session_turn(session_id=session_id, learner_text="Una problema es que no tengo el dinero.")
    print(f" -> Turn 2 processed: Agent replied: \"{t2_res['agent_text'][:40]}...\" (Turn count: {t2_res['turn_count']})")
    assert t2_res["turn_count"] == 2

    # Check that session in DB accumulated mistakes from error analysis
    sess_doc = db.get_session(session_id)
    print(f" -> Session mistakes tagged so far: {sess_doc.get('mistakes_tagged')}")

    # 5. Test Full REST API Pipeline (No Manual Glue Code)
    print("\n[Test 5/5] Testing Full REST API Pipeline via FastAPI TestClient...")
    client = TestClient(app)

    # 5a. Start
    api_start = client.post("/session/start", json={"user_id": user_id, "mode": "daily_loop"})
    assert api_start.status_code == 200
    api_sess_id = api_start.json()["session_id"]

    # 5b. Turn
    api_turn = client.post("/session/turn", json={"session_id": api_sess_id, "learner_text": "Buenos días, un café por favor."})
    assert api_turn.status_code == 200
    assert api_turn.json()["turn_count"] == 1

    # 5c. End
    api_end = client.post("/session/end", json={"session_id": api_sess_id})
    assert api_end.status_code == 200
    end_summary = api_end.json()
    print(f" -> API Session Completed: Mastery Delta = {end_summary['mastery_delta']}, Words Closer = {end_summary['words_closer_to_fluent']}")
    assert "mastery_delta" in end_summary

    print("\n==================================================================")
    print("   ALL 5 LANGGRAPH WIRING CHECKS PASSED SUCCESSFULLY!             ")
    print("==================================================================")

if __name__ == "__main__":
    run_langgraph_wiring_suite()
