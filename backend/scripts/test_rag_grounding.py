import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.rag.vocab_store import vocab_store, LEVEL_HIERARCHY
from app.tools.mcp_tools import fetch_level_vocab
from app.agents.conversation import generate_conversation_turn
from scripts.seed_vocab_bank import seed_vocab

def test_rag_grounding():
    print("==================================================")
    print("       LOOP RAG GROUNDING VERIFICATION SUITE       ")
    print("==================================================")

    # Step 1: Ensure Seeding
    print("\n[Step 1] Seeding and verifying vocabulary store...")
    seed_vocab()
    
    if vocab_store.is_chroma_ready and vocab_store.collection:
        count = vocab_store.collection.count()
        print(f" -> ChromaDB status: READY ({count} documents indexed in 'vocab_bank')")
        assert count > 0, "ChromaDB collection should have documents"
    else:
        print(f" -> Local In-Memory status: READY ({len(vocab_store.in_memory_docs)} documents cached)")
        assert len(vocab_store.in_memory_docs) > 0, "In-memory docs should have items"

    # Step 2: Test CEFR Level Hierarchy Constraints
    print("\n[Step 2] Testing CEFR Level Hierarchy Constraints...")
    
    # 2a. A1 Query: MUST ONLY return A1 documents
    a1_results = fetch_level_vocab(level="A1", theme="travel", k=5)
    print(f" -> A1 Travel query returned {len(a1_results)} items:")
    for item in a1_results:
        lvl = item.get("metadata", {}).get("cefr_level")
        doc = item.get("document")
        lemma = item.get("metadata", {}).get("lemma")
        print(f"    - [{lvl}] ({lemma}): {doc}")
        assert lvl == "A1", f"A1 query must NOT return non-A1 items (got {lvl})"

    # 2b. A2 Query: MUST ONLY return A1 or A2 documents
    a2_results = fetch_level_vocab(level="A2", theme="work", k=5)
    print(f"\n -> A2 Work query returned {len(a2_results)} items:")
    for item in a2_results:
        lvl = item.get("metadata", {}).get("cefr_level")
        lemma = item.get("metadata", {}).get("lemma")
        print(f"    - [{lvl}] ({lemma}): {item.get('document')}")
        assert lvl in ["A1", "A2"], f"A2 query must only return A1/A2 items (got {lvl})"

    # 2c. B1 Query: Allowed A1, A2, B1
    b1_results = fetch_level_vocab(level="B1", theme="work", k=5)
    print(f"\n -> B1 Work query returned {len(b1_results)} items:")
    for item in b1_results:
        lvl = item.get("metadata", {}).get("cefr_level")
        lemma = item.get("metadata", {}).get("lemma")
        print(f"    - [{lvl}] ({lemma}): {item.get('document')}")
        assert lvl in ["A1", "A2", "B1"], f"B1 query must only return <= B1 items (got {lvl})"

    # Step 3: Test Semantic Context Biasing
    print("\n[Step 3] Testing Semantic Context Querying with Due Words...")
    due_query_results = fetch_level_vocab(
        level="A1",
        theme="travel",
        k=3,
        query_text="pedir café con leche en la cafetería y pagar con tarjeta"
    )
    print(f" -> Semantic query ('pedir café') returned {len(due_query_results)} items:")
    for item in due_query_results:
        print(f"    - [{item['metadata'].get('cefr_level')}] {item['metadata'].get('lemma')}: {item['document']}")
    
    lemmas_returned = [item["metadata"].get("lemma") for item in due_query_results]
    assert any("café" in l or "pedir" in l or "pagar" in l or "cuenta" in l for l in lemmas_returned), \
        "Semantic query should prioritize relevant cafe/ordering items"

    # Step 4: Test Grounded Conversation Turn Generation
    print("\n[Step 4] Testing Grounded Conversation Partner Generation...")
    turn_response = generate_conversation_turn(
        level="A1",
        theme="cafe",
        persona="barista",
        target_language="es",
        due_items=[{"lemma": "el café", "id": "test_1"}, {"lemma": "la cuenta", "id": "test_2"}],
        tagged_mistakes=[{"error_type": "gender_agreement", "correction": "un café frío", "example_turn": "un café fría"}],
        conversation_history=[],
        latest_learner_text=None
    )
    print(f" -> Generated Grounded Opening Turn:\n    \"{turn_response}\"")
    assert len(turn_response) > 5, "Should generate a valid conversational opening"

    # Step 5: Test API Endpoint
    print("\n[Step 5] Testing FastAPI TestClient for /session/rag/vocab endpoint...")
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    
    api_res = client.get("/session/rag/vocab?level=A1&theme=travel&k=3")
    assert api_res.status_code == 200, f"API endpoint failed: {api_res.text}"
    api_data = api_res.json()
    print(f" -> Endpoint returned {api_data['count']} items (Level: {api_data['level']}, Theme: {api_data['theme']})")
    assert api_data["count"] > 0, "Endpoint should return items"

    print("\n==================================================")
    print("  ALL RAG GROUNDING VERIFICATION CHECKS PASSED!   ")
    print("==================================================")

if __name__ == "__main__":
    test_rag_grounding()
