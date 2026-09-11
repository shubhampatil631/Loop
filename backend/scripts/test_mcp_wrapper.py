import sys
import json
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.db import db
from app.tools.mcp_tools import (
    get_due_items,
    fetch_level_vocab,
    log_error_tag,
    schedule_next_review,
    get_learner_profile,
    MCP_TOOL_DEFINITIONS
)
from fastapi.testclient import TestClient
from app.main import app

def run_mcp_wrapper_suite():
    print("==================================================================")
    print("        LOOP BUFFER / MCP WRAPPER VERIFICATION SUITE (DAY 13)     ")
    print("==================================================================")

    # 1. Verify Tool Registry
    print("\n[Test 1/5] Verifying MCP Tool Definitions...")
    assert len(MCP_TOOL_DEFINITIONS) == 5
    tool_names = [t["name"] for t in MCP_TOOL_DEFINITIONS]
    print(f" -> Registered tools ({len(tool_names)}): {tool_names}")
    expected_tools = ["get_due_items", "fetch_level_vocab", "log_error_tag", "schedule_next_review", "get_learner_profile"]
    for t in expected_tools:
        assert t in tool_names, f"Tool '{t}' must be registered"

    # Setup test user
    user = db.create_user(name="MCP Inspector Tester", target_language="es", goal="travel")
    user_id = user["id"]

    # 2. Test Internal Python Invocations
    print("\n[Test 2/5] Testing Direct Internal Python Tool Calls...")
    p = get_learner_profile(user_id)
    assert p["name"] == "MCP Inspector Tester"
    print(f" -> get_learner_profile: {p}")

    v = fetch_level_vocab(level="A1", theme="travel", k=3)
    assert len(v) > 0
    lemma_example = v[0].get("metadata", {}).get("lemma") or v[0].get("lemma") or "vocab_item"
    print(f" -> fetch_level_vocab: fetched {len(v)} items (e.g., '{lemma_example}')")


    due = get_due_items(user_id=user_id, limit=5)
    assert len(due) > 0
    target_item_id = due[0].id
    print(f" -> get_due_items: found {len(due)} due items (first: '{due[0].lemma}', ID: {target_item_id})")

    tag_id = log_error_tag(
        user_id=user_id,
        vocab_item_id=target_item_id,
        error_type="gender_agreement",
        severity="medium",
        example_turn="la mapa",
        correction="el mapa"
    )
    assert tag_id is not None
    print(f" -> log_error_tag: logged tag ID: {tag_id}")

    sched = schedule_next_review(user_id=user_id, vocab_item_id=target_item_id, outcome="correct")
    assert sched is not None
    print(f" -> schedule_next_review: updated '{sched.lemma}' interval={sched.interval_days}d")

    # 3. Test REST Tool Invocation via POST /mcp/call
    print("\n[Test 3/5] Testing REST Tool Invocations (POST /mcp/call)...")
    client = TestClient(app)

    # 3a. GET /mcp/tools
    tools_res = client.get("/mcp/tools")
    assert tools_res.status_code == 200
    assert len(tools_res.json()["tools"]) == 5
    print(" -> GET /mcp/tools returned all 5 schemas.")

    # 3b. POST /mcp/call (fetch_level_vocab)
    call_res = client.post("/mcp/call", json={
        "name": "fetch_level_vocab",
        "arguments": {"level": "A1", "theme": "cafe", "k": 2}
    })
    assert call_res.status_code == 200
    assert call_res.json()["status"] == "success"
    print(f" -> POST /mcp/call (fetch_level_vocab) returned {len(call_res.json()['result'])} items.")

    # 4. Test Standard MCP JSON-RPC 2.0 Protocol (POST /mcp)
    print("\n[Test 4/5] Testing MCP JSON-RPC 2.0 Protocol (POST /mcp)...")
    
    # 4a. tools/list
    rpc_list = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": "req-01",
        "method": "tools/list"
    })
    assert rpc_list.status_code == 200
    rpc_list_data = rpc_list.json()
    assert rpc_list_data["jsonrpc"] == "2.0"
    assert rpc_list_data["id"] == "req-01"
    assert len(rpc_list_data["result"]["tools"]) == 5
    print(" -> JSON-RPC 'tools/list' succeeded with 5 tools.")

    # 4b. tools/call (get_learner_profile)
    rpc_call_1 = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": "req-02",
        "method": "tools/call",
        "params": {
            "name": "get_learner_profile",
            "arguments": {"user_id": user_id}
        }
    })
    assert rpc_call_1.status_code == 200
    rpc_c1_data = rpc_call_1.json()
    assert rpc_c1_data["result"]["isError"] is False
    content_text = json.loads(rpc_c1_data["result"]["content"][0]["text"])
    assert content_text["user_id"] == user_id
    print(f" -> JSON-RPC 'tools/call' (get_learner_profile): parsed content -> {content_text['name']}")

    # 4c. tools/call (schedule_next_review)
    rpc_call_2 = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": "req-03",
        "method": "tools/call",
        "params": {
            "name": "schedule_next_review",
            "arguments": {"user_id": user_id, "vocab_item_id": target_item_id, "outcome": "incorrect"}
        }
    })
    assert rpc_call_2.status_code == 200
    rpc_c2_data = rpc_call_2.json()
    assert rpc_c2_data["result"]["isError"] is False
    sched_content = json.loads(rpc_c2_data["result"]["content"][0]["text"])
    print(f" -> JSON-RPC 'tools/call' (schedule_next_review): interval reset to {sched_content['interval_days']}d")

    # 5. Test JSON-RPC Error Handling
    print("\n[Test 5/5] Testing JSON-RPC Protocol Error Handling...")
    rpc_err = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": "req-04",
        "method": "unknown/method"
    })
    assert rpc_err.status_code == 200
    err_data = rpc_err.json()
    assert "error" in err_data
    assert err_data["error"]["code"] == -32601
    print(f" -> JSON-RPC unknown method correctly returned code {err_data['error']['code']}: {err_data['error']['message']}")

    print("\n==================================================================")
    print("   ALL 5 BUFFER / MCP WRAPPER CHECKS PASSED SUCCESSFULLY!         ")
    print("==================================================================")

if __name__ == "__main__":
    run_mcp_wrapper_suite()
