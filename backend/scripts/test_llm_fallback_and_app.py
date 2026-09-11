import sys
import io
from pathlib import Path

# Ensure UTF-8 output on Windows console with line buffering
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.llm import call_llm
from app.models.db import db
from fastapi.testclient import TestClient
from app.main import app

def test_llm_and_app():
    print("==================================================================")
    print("      LOOP: MULTI-PROVIDER LLM FALLBACK & FULL APP TEST          ")
    print("==================================================================")

    # 1. Config Check
    print("\n[Step 1] Verifying Loaded Configurations:")
    print(f" -> OLLAMA_HOST: {settings.OLLAMA_HOST}")
    print(f" -> OLLAMA_MODELS: {settings.OLLAMA_MODELS}")
    print(f" -> GROQ_API_KEY: {'[Configured]' if settings.GROQ_API_KEY else '[None]'}")
    print(f" -> GEMINI_API_KEY: {'[Configured]' if settings.GEMINI_API_KEY else '[None]'}")
    print(f" -> MONGO_URI: {settings.MONGO_URI[:35]}...")

    # 2. Test LLM Dispatcher
    print("\n[Step 2] Testing Multi-Provider LLM Fallback (Ollama(3 models) -> Groq -> Gemini)...")
    res = call_llm(
        prompt="Say '¡Hola! Bienvenidos a Loop' in Spanish and nothing else.",
        system_instruction="You are a helpful Spanish tutor. Output only the requested sentence.",
        temperature=0.3
    )
    print(f" -> LLM Generation Result: \"{res}\"")
    assert len(res) > 3, "LLM must produce a valid output"

    # 3. Test Database Connection
    print("\n[Step 3] Verifying Database Connection...")
    active_db = db.db.name if db.db is not None else 'In-Memory Fallback'
    print(f" -> DB Connected to MongoDB: {db.is_connected} (Active DB: {active_db})")

    # 4. Comprehensive REST Pipeline
    print("\n[Step 4] Running Full Application Pipeline...")
    client = TestClient(app)

    # 4a. Health
    h_res = client.get("/health")
    assert h_res.status_code == 200
    print(f" -> /health OK: {h_res.json()}")

    # 4b. Onboard & Placement
    onboard_res = client.post("/onboarding/start", json={"name": "Fallback Tester", "target_language": "es", "goal": "travel"})
    assert onboard_res.status_code == 200
    user_id = onboard_res.json()["user_id"]
    placement_id = onboard_res.json()["placement_session_id"]
    print(f" -> User created: {user_id}")

    p_res = client.post("/onboarding/placement/turn", json={"placement_session_id": placement_id, "learner_text": "Hola, me gusta viajar a España."})
    assert p_res.status_code == 200
    print(f" -> Placement turn reply: \"{p_res.json()['agent_text'][:50]}...\"")

    # 4c. Session Start & Turn
    s_start = client.post("/session/start", json={"user_id": user_id, "mode": "daily_loop"})
    assert s_start.status_code == 200
    session_id = s_start.json()["session_id"]
    print(f" -> Session started: {session_id} | Scenario: {s_start.json().get('scenario')}")

    s_turn = client.post("/session/turn", json={"session_id": session_id, "learner_text": "Quiero una café fría y la cuenta por favor."})
    assert s_turn.status_code == 200
    print(f" -> Session turn processed | Agent reply: \"{s_turn.json()['agent_text'][:50]}...\"")

    # 4d. Session End
    s_end = client.post("/session/end", json={"session_id": session_id})
    assert s_end.status_code == 200
    summary = s_end.json()
    print(f" -> Session ended | Mastery Delta: {summary['mastery_delta']} | Mistakes Tagged: {len(summary['mistakes_this_session'])}")

    # 4e. Progress & Weekly Digest
    p_data = client.get(f"/progress?user_id={user_id}").json()
    print(f" -> Progress: Mastery Score = {p_data['mastery_score']} | Streak = {p_data['streak_days']}")

    digest = client.get(f"/progress/digest?user_id={user_id}").json()
    print(f" -> Weekly Digest: \"{digest['summary']}\"")

    # 4f. Active Recall Review
    review_due = client.get(f"/review/due?user_id={user_id}").json()
    print(f" -> Review Due Count: {review_due['count']}")

    print("\n==================================================================")
    print("   ALL MULTI-PROVIDER LLM & FULL APP VERIFICATIONS PASSED!       ")
    print("==================================================================")

if __name__ == "__main__":
    test_llm_and_app()
