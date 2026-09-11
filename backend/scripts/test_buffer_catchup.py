import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.db import db
from app.rag.vocab_store import vocab_store
from app.tools.mcp_tools import (
    get_due_items,
    fetch_level_vocab,
    log_error_tag,
    schedule_next_review,
    get_learner_profile
)
from app.tools.mcp_server import dispatch_tool_call
from app.agents.placement import assess_placement_turn
from app.agents.conversation import generate_conversation_turn
from app.agents.error_analysis import analyze_learner_errors
from app.agents.curriculum import curriculum_agent
from app.agents.graph import build_loop_graph
from fastapi.testclient import TestClient
from app.main import app

def run_buffer_catchup_suite():
    print("==================================================================")
    print("        LOOP BUILD PLAN: BUFFER & CATCH-UP VERIFICATION           ")
    print("==================================================================")

    # -------------------------------------------------------------
    # 1. WEEK 1 CATCH-UP CHECKPOINTS (Days 1–7)
    # -------------------------------------------------------------
    print("\n--- [WEEK 1 CATCH-UP] ---")
    
    # 1a. Database Layer & Models
    print("[1/10] Verifying DB CRUD & User Onboarding...")
    user = db.create_user(name="CatchUp Tester", target_language="es", goal="travel")
    user_id = user["id"]
    assert user["level"] == "A1"
    print(f" -> User created successfully: ID={user_id}, Name={user['name']}, Goal={user['goal']}")

    # 1b. Placement Agent Evaluation
    print("\n[2/10] Verifying Placement Agent (3-turn conversational assessment)...")
    history = []
    p1 = assess_placement_turn("es", history, "Hola, me llamo Carlos y estoy aprendiendo español.")
    history.append({"role": "learner", "text": "Hola, me llamo Carlos y estoy aprendiendo español."})
    history.append({"role": "agent", "text": p1["agent_text"]})
    assert p1["placement_complete"] is False

    p2 = assess_placement_turn("es", history, "Me gusta viajar y quiero hablar con la gente local.")
    history.append({"role": "learner", "text": "Me gusta viajar y quiero hablar con la gente local."})
    history.append({"role": "agent", "text": p2["agent_text"]})
    assert p2["placement_complete"] is False

    p3 = assess_placement_turn("es", history, "He visitado España dos veces.")
    assert p3["placement_complete"] is True
    assert p3["level"] in ["A1", "A2", "B1"]
    print(f" -> Placement 3-turn assessment complete! Assessed Level: {p3['level']} (Notes: {p3.get('notes')})")

    # 1c. A1 vs B1 Leveled Vocabulary Complexity Comparison
    print("\n[3/10] Verifying A1 vs B1 Vocabulary Grounding Complexity...")
    a1_vocab = fetch_level_vocab(level="A1", theme="work", k=5)
    b1_vocab = fetch_level_vocab(level="B1", theme="work", k=5)
    
    a1_levels = {item["metadata"]["cefr_level"] for item in a1_vocab}
    b1_levels = {item["metadata"]["cefr_level"] for item in b1_vocab}
    
    print(f" -> A1 Query Result Levels: {a1_levels} (All items <= A1)")
    print(f" -> B1 Query Result Levels: {b1_levels} (Includes A2/B1 nuanced vocabulary)")
    assert all(lvl == "A1" for lvl in a1_levels), "A1 retrieval must only return A1"
    assert "B1" in b1_levels or "A2" in b1_levels, "B1 query should include intermediate items"

    # -------------------------------------------------------------
    # 2. WEEK 2 CATCH-UP CHECKPOINTS (Days 8–14)
    # -------------------------------------------------------------
    print("\n--- [WEEK 2 CATCH-UP] ---")

    # 2a. Error-Analysis Agent
    print("[4/10] Verifying Error-Analysis Agent Classifier...")
    test_learner_turn = "Quiero una café fría y la problema es el precio."
    analyzed_errors = analyze_learner_errors(user_id=user_id, learner_text=test_learner_turn, level="A1", target_language="es")
    print(f" -> Analyzed errors for: '{test_learner_turn}'")
    for err in analyzed_errors:
        print(f"    - Type: {err.get('error_type')} | Lemma: {err.get('vocab_item')} | Correction: {err.get('correction')}")
    assert len(analyzed_errors) >= 1, "Error analysis must detect intentional grammatical errors"

    # 2b. Curriculum / Spaced-Repetition FSRS Updates
    print("\n[5/10] Verifying Curriculum Agent FSRS-Lite Scheduling...")
    user_vocab = db.get_all_user_vocab(user_id)
    assert len(user_vocab) > 0, "User should have initial seeded vocab items"
    test_item = user_vocab[0]
    initial_ease = test_item.get("ease_factor", 2.5)
    initial_reps = test_item.get("reps", 0)
    
    # Simulate 'correct' outcome
    updated_correct = schedule_next_review(user_id=user_id, vocab_item_id=test_item["id"], outcome="correct")
    assert updated_correct.ease_factor >= initial_ease
    assert updated_correct.reps == initial_reps + 1
    print(f" -> FSRS 'correct' update: Ease {initial_ease} -> {updated_correct.ease_factor}, Interval -> {updated_correct.interval_days} days, Reps -> {updated_correct.reps}")


    # 2c. THE CORE BET: Multi-Session Mistake Re-triggering Loop (Day 12 Checkpoint)
    print("\n[6/10] Verifying THE CORE BET: Multi-Session Mistake Re-Triggering Loop...")
    # Session 1: Learner makes a mistake, tagged into DB and backdated 2 days
    tag_id = log_error_tag(
        user_id=user_id,
        vocab_item_id=test_item["id"],
        error_type="gender_agreement",
        severity="medium",
        example_turn="Quiero una café fría",
        correction="un café frío",
        explanation="Café is masculine."
    )
    # Manually backdate the created_at by 2 days to simulate forgetting interval
    db.update_mistake_tag(tag_id, {
        "created_at": datetime.utcnow() - timedelta(days=2),
        "retriggered_count": 0
    })
    
    # Session 2: Curriculum Agent pulls mistakes eligible for re-triggering
    retriggered = curriculum_agent.get_retrigger_mistakes(user_id=user_id, limit=2)
    assert len(retriggered) > 0, "Curriculum Agent must retrieve past eligible mistakes"
    assert any(m.get("id") == tag_id for m in retriggered)
    print(f" -> Session 2 Curriculum Pull successfully found past mistake: '{retriggered[0].get('correction')}'")

    # Pass into Conversation Agent to verify prompt grounding includes this past mistake
    conv_opening = generate_conversation_turn(
        level="A1",
        theme="cafe",
        persona="barista",
        target_language="es",
        due_items=[{"lemma": "el café", "id": test_item["id"]}],
        tagged_mistakes=retriggered,
        conversation_history=[]
    )
    print(f" -> Session 2 Conversation Agent Generated Opening:\n    \"{conv_opening}\"")
    assert len(conv_opening) > 0

    # 2d. LangGraph StateGraph Execution
    print("\n[7/10] Verifying LangGraph StateGraph Execution...")
    graph = build_loop_graph()
    if graph:
        initial_state = {
            "user_id": user_id,
            "mode": "daily_loop",
            "level": "A1",
            "target_language": "es",
            "theme": "travel",
            "persona": "barista",
            "due_items": [],
            "conversation_history": [],
            "turn_count": 0,
            "tagged_mistakes": [],
            "latest_agent_text": None,
            "latest_learner_text": "Hola, buenos días.",
            "placement_complete": False,
            "session_summary": None
        }
        res_graph = graph.invoke(initial_state)
        print(f" -> LangGraph invocation successful! Next Agent Turn: '{res_graph.get('latest_agent_text')[:45]}...'")
        assert res_graph.get("latest_agent_text") is not None
    else:
        print(" -> LangGraph compiled with direct executor fallback.")

    # 2e. MCP Server & Tool Registry
    print("\n[8/10] Verifying MCP Tool Registry & Dispatch...")
    res_mcp_vocab = dispatch_tool_call("fetch_level_vocab", {"level": "A1", "theme": "travel", "k": 2})
    assert len(res_mcp_vocab) > 0
    res_mcp_profile = dispatch_tool_call("get_learner_profile", {"user_id": user_id})
    assert res_mcp_profile["user_id"] == user_id
    print(" -> MCP Tool Dispatch OK (fetch_level_vocab, get_learner_profile)")

    # -------------------------------------------------------------
    # 3. FASTAPI REST & MCP JSON-RPC ENDPOINT TESTING
    # -------------------------------------------------------------
    print("\n--- [FASTAPI REST & MCP PROTOCOL TESTING] ---")
    client = TestClient(app)

    # 3a. MCP Tools List endpoint
    print("[9/10] Testing GET /mcp/tools...")
    mcp_list_res = client.get("/mcp/tools")
    assert mcp_list_res.status_code == 200
    tools_list = mcp_list_res.json()["tools"]
    print(f" -> Registered MCP Tools count: {len(tools_list)} ({[t['name'] for t in tools_list]})")
    assert len(tools_list) == 5

    # 3b. MCP JSON-RPC 2.0 endpoint
    print("\n[10/10] Testing POST /mcp (JSON-RPC 2.0 protocol)...")
    rpc_payload = {
        "jsonrpc": "2.0",
        "id": "test_req_01",
        "method": "tools/call",
        "params": {
            "name": "get_learner_profile",
            "arguments": {"user_id": user_id}
        }
    }
    rpc_res = client.post("/mcp", json=rpc_payload)
    assert rpc_res.status_code == 200
    rpc_data = rpc_res.json()
    assert rpc_data["id"] == "test_req_01"
    assert rpc_data["result"]["isError"] is False
    print(f" -> MCP JSON-RPC response: {rpc_data['result']['content'][0]['text']}")

    print("\n==================================================================")
    print("   ALL 10 BUFFER & CATCH-UP CHECKPOINTS PASSED SUCCESSFULLY!      ")
    print("==================================================================")

if __name__ == "__main__":
    run_buffer_catchup_suite()
